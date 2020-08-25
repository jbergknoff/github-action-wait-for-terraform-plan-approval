FROM python:3.8-alpine
WORKDIR /opt
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY wait_for_terraform_plan_approval.py .
ENTRYPOINT ["python", "-m", "wait_for_terraform_plan_approval"]
