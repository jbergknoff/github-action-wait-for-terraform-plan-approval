# GitHub Action: Wait For Terraform Plan Approval

**This Action helps you send your Terraform plan to an external service where it can be displayed and approved/rejected by anyone who has the (randomly generated) link. If you use the default, publicly available service, you risk exposing any sensitive data in your plans. Alternately, you can point this Action at a service that you run, where you are responsible for keeping data secure. If neither option is acceptable to you, please do not use this Action.**

**The author is not responsible for any loss of data or exfiltration of data caused by use of this Action.**

This action uses an external service (https://terraform-plan-approval.herokuapp.com/, [GitHub](https://github.com/jbergknoff/terraform-plan-approval)) to allow a GitHub Action workflow to prompt a user to approve or reject a Terraform plan before proceeding. **This is just for demonstration purposes, and should not be used for any sensitive data because the service has no authentication/authorization and is fully public.** If you need this functionality for real workloads, considering running an instance of https://github.com/jbergknoff/terraform-plan-approval on a private network and/or behind an authorization gate (e.g. [Cloudflare Access](https://www.cloudflare.com/teams-access/)).

# Usage

These two steps (`command == submit` and `command == wait`) will be used in tandem. They are split up so that we can send a notification (e.g. a Slack message) to the relevant people once we have the URL for reviewing the plan.

#### Submit a plan (`command == submit`)

After generating a plan (here, assumed to happen as part of a step with id `plan`), we can submit it to the external service.

```yaml
- name: Submit the plan to external service
  uses: jbergknoff/github-action-wait-for-terraform-plan-approval@v1
  id: submit_plan
  with:
    command: submit

    # The human-readable `terraform plan` output. ANSI color codes are okay (they will
    # be colorized when the plan is displayed for review.
    plan_contents: ${{steps.plan.outputs.stdout}}

    # (Optional) Overrides the URL of the external service. Defaults to the insecure,
    # underpowered https://terraform-plan-approval.herokuapp.com.
    #
    # See https://github.com/jbergknoff/terraform-plan-approval if you are interested
    # in running your own internal copy.
    external_service_url: https://terraform-plan-approval.bigcorp-internal.com
```

This step will produce these outputs:

* `steps.submit_plan.outputs.approval_prompt_url`: the URL where somebody should go to review the plan and approve/reject it.
* `steps.submit_plan.outputs.plan_id`: the plan id generated by the service.

#### Wait for a plan to be approved/rejected (`command == wait`)

After generating a plan (here, assumed to happen as part of a step with id `plan`), we can submit it to the external service.

```yaml
- name: Wait for approval
  uses: jbergknoff/github-action-wait-for-terraform-plan-approval@v1
  with:
    command: wait

    # The plan id generated by the external service.
    plan_id: ${{steps.submit_plan.outputs.plan_id}}

    # (Optional) Overrides the URL of the external service. Defaults to the insecure,
    # underpowered https://terraform-plan-approval.herokuapp.com.
    #
    # See https://github.com/jbergknoff/terraform-plan-approval if you are interested
    # in running your own internal copy.
    external_service_url: https://terraform-plan-approval.bigcorp-internal.com

    # Give up waiting for approval/rejection after this many seconds. If the operation
    # times out and the plan is still pending, the action will `exit 1`, failing the build.
    # Default: 300 (5 minutes)
    timeout_seconds: 600

    # The interval (in seconds) at which we'll check the plan status.
    # Default: 5
    polling_period_seconds: 10
```

If the plan is approved, this step will `exit 0` and the build will continue. If the plan is rejected or we reach the timeout, this step will `exit 1` and the build will fail.

This step will produce these outputs:

* `steps.submit_plan.outputs.plan_status`: the final status of the plan: either 'approved', 'rejected', or 'timed out'.

## Full Example

The [tests for this repository](/.github/workflows/test.yaml) show off how to use this Action, but with two caveats:

* Those tests refer to the action with `uses: ./` which should normally be `uses: jbergknoff/github-action-wait-for-terraform-plan-approval@v1`
* The tests approve/reject the plan using `curl`. The approval/rejection would normally happen when a human visits the plan page and clicks a button.

Here's a more conventional example:

```yaml
name: Terraform Apply

on: push

jobs:
  terraform:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2

    - name: Setup Terraform
      uses: hashicorp/setup-terraform@v1

    - name: Terraform Init
      run: terraform init

    - name: Terraform Plan
      id: plan
      run: terraform plan -out saved_plan

    - name: Submit plan for approval
      uses: jbergknoff/github-action-wait-for-terraform-plan-approval@v1
      id: submit_plan
      with:
        command: submit
        plan_contents: ${{steps.plan.outputs.stdout}}

    # Snip: send a Slack DM asking somebody to visit `steps.submit_plan.outputs.approval_prompt_url` to approve

    - name: Wait for approval
      uses: jbergknoff/github-action-wait-for-terraform-plan-approval@v1
      with:
        command: wait
        plan_id: ${{steps.submit_plan.outputs.plan_id}}
        timeout_seconds: 600

    - name: Terraform Apply
      run: terraform apply -auto-approve saved_plan
```

![Submitting to the service](/image/submit.png)

![Reviewing the plan](/image/approval.png)

![Approved the plan](/image/approved.png)

![Move on to apply](/image/apply.png)
