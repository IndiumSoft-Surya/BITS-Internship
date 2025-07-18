\# Jira Activity Tracker



This project is a Python-based tool that monitors a Jira project for recent issue updates and sends notifications to a Slack channel. It tracks issues updated within a specified time frame (default: last hour) and posts formatted messages to Slack with details such as issue key, summary, status, assignee, priority, and update time.



\## Prerequisites



Before setting up and running the project, ensure you have the following:



\- \*\*Python 3.8 or higher\*\*: The project is built and tested with Python 3.8+.

\- \*\*Jira Account\*\*: Access to a Jira instance with API token authentication.

\- \*\*Slack Webhook\*\*: A Slack app with an incoming webhook configured for your workspace.

\- A code editor (e.g., VS Code, PyCharm) and a terminal for running commands.



\## Setup Instructions



Follow these steps to set up and run the Jira Activity Tracker.



\### 1. Clone the Repository



Clone the project to your local machine:



```bash

git clone <repository-url>

cd jira-activity-tracker

```



Replace `<repository-url>` with the URL of your repository if applicable.



\### 2. Install Dependencies



The project dependencies are listed in `requirements.txt`. To install them:



1\. \*\*Create a Virtual Environment\*\* (recommended):

&nbsp;  ```bash

&nbsp;  python -m venv venv

&nbsp;  source venv/bin/activate  # On Windows: venv\\Scripts\\activate

&nbsp;  ```



2\. \*\*Install Requirements\*\*:

&nbsp;  ```bash

&nbsp;  pip install -r requirements.txt

&nbsp;  ```



This installs all necessary packages, including `requests`, `slack\_sdk`, `python-dateutil`, and others.



\### 3. Set Up the `.env` File



The project uses environment variables to securely store sensitive configuration details. Follow these steps to configure the `.env` file:



1\. \*\*Copy the Example File\*\*:

&nbsp;  ```bash

&nbsp;  cp .env.example .env

&nbsp;  ```



2\. \*\*Edit the `.env` File\*\*:

&nbsp;  Open the `.env` file in a text editor and provide the following values:



&nbsp;  ```plaintext

&nbsp;  JIRA\_EMAIL=your-jira-email@example.com

&nbsp;  JIRA\_API\_TOKEN=your-jira-api-token

&nbsp;  JIRA\_BASE\_URL=https://your-jira-instance.atlassian.net

&nbsp;  SLACK\_WEBHOOK\_URL=https://hooks.slack.com/services/xxx/yyy/zzz

&nbsp;  PROJECT\_KEY=your-jira-project-key

&nbsp;  ```



&nbsp;  - \*\*JIRA\_EMAIL\*\*: The email address associated with your Jira account.

&nbsp;  - \*\*JIRA\_API\_TOKEN\*\*: Generate an API token from your Jira account:

&nbsp;    1. Log in to your Jira instance.

&nbsp;    2. Go to your Atlassian account settings.

&nbsp;    3. Navigate to \*\*Security\*\* > \*\*Create and manage API tokens\*\*.

&nbsp;    4. Create a new API token and copy it.

&nbsp;  - \*\*JIRA\_BASE\_URL\*\*: The base URL of your Jira instance (e.g., `https://yourcompany.atlassian.net`).

&nbsp;  - \*\*SLACK\_WEBHOOK\_URL\*\*: The incoming webhook URL for your Slack channel:

&nbsp;    1. Create a Slack app in your workspace.

&nbsp;    2. Enable \*\*Incoming Webhooks\*\* and create a webhook URL.

&nbsp;    3. Copy the webhook URL provided by Slack.

&nbsp;  - \*\*PROJECT\_KEY\*\*: The key of the Jira project you want to monitor (e.g., `PROJ`).



&nbsp;  \*\*Example `.env` file\*\*:

&nbsp;  ```plaintext

&nbsp;  JIRA\_EMAIL=user@example.com

&nbsp;  JIRA\_API\_TOKEN=abcd1234efgh5678

&nbsp;  JIRA\_BASE\_URL=https://example.atlassian.net

&nbsp;  SLACK\_WEBHOOK\_URL=https://hooks.slack.com/services/T00000000/B00000000/xxxxxxxxxxxxxxxxxxxxxxxx

&nbsp;  PROJECT\_KEY=PROJ

&nbsp;  ```



3\. \*\*Save the `.env` File\*\*:

&nbsp;  Ensure the `.env` file is saved in the project root directory. Do not commit this file to version control (it’s typically ignored via `.gitignore`).



\### 4. Verify Environment Variables



The project uses the `python-dotenv` package to load environment variables from the `.env` file. Ensure the `.env` file is correctly formatted and contains all required values. Missing or incorrect values will cause errors during execution.



\### 5. Run the Application



To start the Jira Activity Tracker:



1\. \*\*Activate the Virtual Environment\*\* (if not already activated):

&nbsp;  ```bash

&nbsp;  source venv/bin/activate  # On Windows: venv\\Scripts\\activate

&nbsp;  ```



2\. \*\*Run the Script\*\*:

&nbsp;  ```bash

&nbsp;  python new\_run.py

&nbsp;  ```



The script will:

\- Start monitoring your Jira project for issues updated in the last hour.

\- Print details of updated issues to the console.

\- Send notifications to the configured Slack channel for new or updated issues.

\- Save notified issue timestamps to `notified\_issues.json` to avoid duplicate notifications.

\- Check for updates every 30 seconds.



\### 6. Monitor Output



\- \*\*Console Output\*\*: The script prints details of recently updated issues, including key, summary, status, assignee, priority, and update time (in IST).

\- \*\*Slack Notifications\*\*: For each new or updated issue, a formatted message is sent to the Slack channel specified by `SLACK\_WEBHOOK\_URL`.

\- \*\*Error Handling\*\*: If an error occurs (e.g., network issues or invalid credentials), the script logs the error and retries after 60 seconds.



\### 7. Stopping the Application



To stop the tracker, press `Ctrl+C` in the terminal. The script will exit gracefully, preserving the `notified\_issues.json` file for the next run.



\## Project Structure



\- `config.py`: Loads environment variables from the `.env` file.

\- `jira\_tracker.py`: Contains functions to query Jira for recent issues.

\- `notifier.py`: Handles sending notifications to Slack.

\- `new\_run.py`: Main script that orchestrates the tracking and notification process.

\- `requirements.txt`: Lists Python dependencies.

\- `.env.example`: Template for the `.env` file.

\- `notified\_issues.json`: Generated file that tracks notified issues to prevent duplicates.

