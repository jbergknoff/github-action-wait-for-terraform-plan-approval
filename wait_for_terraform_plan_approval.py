import base64
import os
import sys
import time

import requests


external_service_url = os.getenv('INPUT_EXTERNAL_SERVICE_URL')
external_service_url_auth_token = os.getenv('INPUT_EXTERNAL_SERVICE_URL_AUTH_TOKEN')

if not external_service_url:
	print('`external_service_url` is required.')


def submit(plan_contents: str):
	headers = {}
	if external_service_url_auth_token:
		headers["Authorization"] = external_service_url_auth_token

	response = requests.post(
		f'{external_service_url}/plan',
		headers=headers,
		json={
			'plan_base64': base64.b64encode(plan_contents.encode('utf8')).decode('utf8'),
		},
	)

	if response.status_code != 201:
		print(f'Failed submitting plan. External service sent response code {response.status_code}.')
		sys.exit(1)

	try:
		plan_id = response.json()['id']
	except:
		print('Response from external service was not in expected format.')
		sys.exit(1)

	print(f'Submitted plan: {external_service_url}/plan/{plan_id}')
	print(f'::set-output name=plan_id::{plan_id}')
	print(f'::set-output name=approval_prompt_url::{external_service_url}/plan/{plan_id}')


def wait(plan_id: str, timeout_seconds: int, polling_period_seconds: int):
	print(f'Waiting up to {timeout_seconds} seconds for {external_service_url}/plan/{plan_id} to be approved or rejected')
	waited = 0

	headers = {}
	if external_service_url_auth_token:
		headers["Authorization"] = external_service_url_auth_token

	while waited <= timeout_seconds:
		response = requests.get(f'{external_service_url}/plan/{plan_id}/status', headers=headers)
		if response.status_code != 200:
			print(f'Failed polling plan status. External service sent response code {response.status_code}.')
			sys.exit(1)

		try:
			status = response.json()['status']
		except:
			print('Response from external service was not in expected format.')
			sys.exit(1)

		if status == 'rejected':
			print('Plan was rejected')
			print('::set-output name=plan_status::rejected')
			sys.exit(1)
		elif status == 'approved':
			print('Plan was approved')
			print('::set-output name=plan_status::approved')
			sys.exit(0)

		time.sleep(polling_period_seconds)
		waited += polling_period_seconds

	print('Timed out waiting for plan approval')
	print('::set-output name=plan_status::timed out')
	sys.exit(1)


if __name__ == '__main__':
	# GitHub Actions inputs are exposed as environment variables
	# cf. https://docs.github.com/en/actions/creating-actions/metadata-syntax-for-github-actions#inputs
	command = os.getenv('INPUT_COMMAND')
	if command == 'submit':
		plan_contents = os.getenv('INPUT_PLAN_CONTENTS')
		if not plan_contents:
			print('Error: pass `plan_contents` if using `command = submit`')
			sys.exit(1)

		submit(plan_contents)
	elif command == 'wait':
		plan_id = os.getenv('INPUT_PLAN_ID')
		if not plan_id:
			print('`plan_id` is required.')
			sys.exit(1)

		try:
			timeout_seconds = int(os.getenv('INPUT_TIMEOUT_SECONDS'))
		except:
			print('`timeout_seconds` could not be parsed as integer. Falling back on 300.')
			timeout_seconds = 300

		try:
			polling_period_seconds = int(os.getenv('INPUT_POLLING_PERIOD_SECONDS'))
		except:
			print('`polling_period_seconds` could not be parsed as integer. Falling back on 5.')
			polling_period_seconds = 5

		wait(plan_id=plan_id, timeout_seconds=timeout_seconds, polling_period_seconds=polling_period_seconds)
	else:
		print(f'Unrecognized command: "{command}". Should be one of `submit` or `wait`.')
		sys.exit(1)
