import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
from config import JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN, PROJECT_KEY

def get_recent_issues(hours=1):
    since = (datetime.utcnow() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M')
    jql = f'project = {PROJECT_KEY} AND updated >= "{since}" ORDER BY updated DESC'
    url = f"{JIRA_BASE_URL}/rest/api/3/search"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    params = {
        "jql": jql,
        "maxResults": 10,
        "fields": "summary,status,assignee,updated"
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        auth=HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
    )

    response.raise_for_status()
    data = response.json()
    return data.get("issues", [])
