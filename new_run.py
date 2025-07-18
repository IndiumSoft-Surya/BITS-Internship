# run.py

from jira_tracker import get_recent_issues
from notifier import send_to_slack
import time
from config import JIRA_BASE_URL
from datetime import datetime
from dateutil import tz 
import json
import os

STATE_FILE = "notified_issues.json"


IST = tz.gettz('Asia/Kolkata')

def load_notified_updates():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_notified_updates(updates):
    with open(STATE_FILE, "w") as f:
        json.dump(updates, f)

def print_recent_issues_verbose(issues):
    if not issues:
        print("No issues updated in the last 30 seconds.")
        return
    print(f"Found {len(issues)} recently updated issues:\n")
    for i, issue in enumerate(issues, start=1):
        fields = issue['fields']
        assignee = fields['assignee']['displayName'] if fields.get('assignee') else 'Unassigned'
        priority = fields.get('priority')
        priority_name = priority['name'] if priority else 'None'
        
        updated_dt = parse_jira_timestamp(fields['updated'])
        updated_ist = updated_dt.astimezone(IST)
        updated_ist_str = updated_ist.strftime('%d %b %Y, %I:%M %p IST')
        
        print(f"Issue {i}:")
        print(f" Key: {issue['key']}")
        print(f" Summary: {fields['summary']}")
        print(f" Status: {fields['status']['name']}")
        print(f" Assignee: {assignee}")
        print(f" Updated: {updated_ist_str}") 
        print(f" Priority: {priority_name}")
        print(f" URL: {JIRA_BASE_URL}/browse/{issue['key']}")
        print("-" * 60)


def parse_jira_timestamp(ts):
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%f%z")

def main():
    print("Starting Jira activity tracker...")
    notified_updates = load_notified_updates()

    while True:
        try:
            issues = get_recent_issues()
            print_recent_issues_verbose(issues) 
            updated = False

            for issue in issues:
                issue_key = issue["key"]
                updated_str = issue["fields"]["updated"]
                updated_dt = parse_jira_timestamp(updated_str)

                last_str = notified_updates.get(issue_key)
                last_dt = parse_jira_timestamp(last_str) if last_str else None

                if not last_dt or updated_dt > last_dt:
                   
                    updated_ist = updated_dt.astimezone(IST)
                    updated_ist_str = updated_ist.strftime('%d %b %Y, %I:%M %p IST')

                    fields = issue['fields']
                    summary = fields['summary']
                    status = fields['status']['name']
                    assignee = fields['assignee']['displayName'] if fields.get('assignee') else 'Unassigned'
                    priority = fields.get('priority')
                    priority_name = priority['name'] if priority else 'None'
                    issue_url = f"{JIRA_BASE_URL}/browse/{issue_key}"

                    message = (
                        f"🔔 *Jira Update: <{issue_url}|{issue_key}>*\n"
                        f"*Summary:* {summary}\n"
                        f"*Status:* {status}\n"
                        f"*Assignee:* {assignee}\n"
                        f"*Priority:* {priority_name}\n"
                        f"*Updated:* {updated_ist_str}"
                    )
                    
                    if send_to_slack(message):
                        print(f"Sent notification for {issue_key}")
                        notified_updates[issue_key] = updated_str
                        updated = True
                    else:
                        print(f"Failed to send notification for {issue_key}")
                else:
                    print(f"Skipping {issue_key} — not updated since last notification")

            if updated:
                save_notified_updates(notified_updates)

            time.sleep(30)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
