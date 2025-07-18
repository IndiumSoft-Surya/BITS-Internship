from jira_tracker import get_recent_issues
from config import SLACK_WEBHOOK_URL
import requests

def send_to_slack(message):
    payload = {"text": message}
    response = requests.post(SLACK_WEBHOOK_URL, json=payload)
    print(response)
    return response.status_code == 200
