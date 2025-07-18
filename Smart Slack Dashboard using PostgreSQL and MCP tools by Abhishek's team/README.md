# Smart Bank Transaction Dashboard & Slack Bot

## Problem Statement

Modern financial institutions struggle with **fragmented transaction analysis**, slow or manual **fraud detection**, and limited channels for real-time action or insights. This project addresses these business and technical gaps with a unified solution that powers:

- **Real-time data visualization** and business monitoring
- **Drill-down analytics** by customer, time, merchant type, demographic, and fraud status
- **Integrated Slack bot assistant** supporting both slash commands and natural language requests for insights or custom summaries, powered by an LLM

### Business Challenges
- **Fragmented Data Analysis**: Data is siloed, hampering unified reporting.
- **Manual Fraud Detection**: Human review is slow, missing patterns in real time.
- **Limited Real-time Insights**: Most tools delay reporting; risks are identified too late.
- **Poor User Experience**: Standard dashboards are inflexible, not intuitive.
- **Communication Gaps**: Lacks a way to get alerts or summaries “where you work”.

### Technical Challenges
- **Scalability**: Current approaches falter with growing data volumes.
- **Static Visuals**: PDFs or fixed reports hide trends, make slicing hard.
- **Integration Complexity**: Hard to join up dashboards, communication, and AI/ML.
- **Accessibility**: Teams struggle to use business intelligence outside the office.

---

## Solution Overview

This project delivers:

1. **Interactive Streamlit Dashboard**: For custom analysis of transactions, patterns, and KPIs.
2. **Slack Bot Integration**: Use direct commands or `/assist` for AI-powered natural language summaries and insights.
3. **AI-Powered Assistant**: LLM-based mapping of user requests to dashboard queries or business summaries.
4. **Advanced Fraud Analytics**: Patterns, rates, and client-level drill‑downs.
5. **Demographic Insights**: Slice any metric by age, gender, merchant type, or more.

---

## Key Features

### Dashboard Capabilities
- **Rich Interactive Visuals**: Plotly charts, real-time filters, multi-dimensional exploration.
- **Fraud Detection**: Patterns, trends, high-risk client analytics.
- **Client Deep-Dive**: Instant 360° client activity and demographics.
- **Comparative Analytics**: Across periods, segments, or metrics.

### Slack Bot Features
- **Command Center**: `/dashboard`, `/overview_summary`, `/fraud_summary [days]`, `/daily_summary [YYYY-MM-DD]`, `/client_summary [client_id]`
- **LLM Assistant**: `/assist` command interprets natural language and delivers mapped summaries or links (`Open the dashboard`, `Show fraud for 7 days`, `Tell me about client 12345`)
- **Buttons & Modals**: Interactive Slack messages to trigger charts or bring the dashboard to you
- **Automated Alerts**: Periodic and real-time insights fund teams directly in Slack
- **Secure Verification**: All Slack requests are HMAC signature-verified for security

### Analytics Modules
- **Overview**: Company‑wide KPIs and trends
- **Fraud Analysis**: Custom period fraud rates, demographic risk breakdowns
- **Daily Snapshot**: Single‑day KPIs, hourly/merchant activity
- **Client Profiles**: Lifetime value, activity, and fraud status per client

---

## Technology Stack

| Layer         | Technology                    |
|---------------|------------------------------|
| Frontend      | **Streamlit** (visualization)|
| Backend/API   | **Flask**                    |
| Database      | **PostgreSQL** + SQLAlchemy  |
| Visualization | **Plotly**                   |
| Slack/Comm    | **Slack SDK**                |
| AI            | **OpenRouter LLM**           |
| Deployment    | **ngrok/LocalTunnel**        |

---

## Repository Structure

smart-bank-dashboard/
├── app.py # Slack bot: Flask endpoints, LLM intent mapper
├── dashboard.py # Streamlit dashboard UI (main entry point)
├── charts.py # Reusable Plotly chart utilities
├── db_conn.py # SQLAlchemy engine factory/setup
├── llm_mapper.py # LLM-enabled text to command mapping
├── queries.py # All SQL queries (overview, fraud, client, etc)
├── summaries.py # Text summary creators from data queries
├── .env # Environment variables (never commit this)
├── requirements.txt # Python package dependencies
└── README.md # This documentation


---

## Prerequisites

- **Python 3.9+**
- **PostgreSQL 12+** (transaction and reference tables: `transactions_data`, `users_data`, `cards_data`, `train_fraud_labels`, `mcc_codes`)
- **ngrok** or **LocalTunnel** (for exposing local services to Slack)
- **Slack Workspace & App** (create one for your workspace)
- **OpenRouter API Key** (for LLM features)
- **Internet access** (for LLM calls and external dashboard access)

---

## Installation & Setup

### 1. Clone the Repository

git clone <your-repository-url>
cd smart-bank-dashboard


### 2. Create & Activate a Virtual Environment

python -m venv .venv

On Linux/Mac
source .venv/bin/activate

On Windows
.venv\Scripts\activate


### 3. Install All Dependencies

pip install --upgrade pip
pip install -r requirements.txt


### 4. Environment Configuration

Create a `.env` file (in the project root):

SLACK_BOT_TOKEN=your-slack-bot-token
SLACK_SIGNING_SECRET=your-signing-secret
OPENROUTER_API_KEY=your-openrouter-api-key
DASHBOARD_URL=https://your-ngrok-subdomain.ngrok.io
DATABASE_URL=postgresql+psycopg2://username:password@localhost:5432/database_name

*Never commit this file!*

### 5. Database Setup

Ensure your PostgreSQL installation has all required tables:

- `transactions_data` (main transaction log)
- `users_data` (client info/demographics)
- `cards_data` (card type linkage)
- `train_fraud_labels` (transaction fraud labels)
- `mcc_codes` (merchant type codes)

---

## Running the Application

**Step 1: Start the Streamlit Dashboard**

streamlit run dashboard.py

text
(by default, runs on [http://localhost:8501](http://localhost:8501))

**Step 2: Expose the Dashboard via ngrok**

In a new terminal:
ngrok http 8501

text
Copy the forwarding URL (`https://<subdomain>.ngrok.io`) and update `DASHBOARD_URL` in your `.env`.

**Step 3: Start the Flask App (Slack Bot)**

python app.py

text
(This runs at `http://localhost:3000`)

**Step 4: Expose Flask App via LocalTunnel (or ngrok)**

For LocalTunnel:
npx localtunnel --port 3000 --subdomain <your-subdomain>

text
For ngrok (alternative):
ngrok http 3000

text

**Step 5: Configure Your Slack App**

- Go to [Slack API Dashboard](https://api.slack.com/apps)
- Create or update your app; under "Slash Commands":
    - `/dashboard` → `https://your-subdomain.loca.lt/slack/dashboard`
    - `/overview_summary` → `https://your-subdomain.loca.lt/slack/overview_summary`
    - `/fraud_summary` → `https://your-subdomain.loca.lt/slack/fraud_summary`
    - `/daily_summary` → `https://your-subdomain.loca.lt/slack/daily_summary`
    - `/client_summary` → `https://your-subdomain.loca.lt/slack/client_summary`
    - `/assist` → `https://your-subdomain.loca.lt/slack/assist`
- Under "Interactivity & Shortcuts", put `https://<your-subdomain>.loca.lt/slack/interactions`
- Install or re-install your app to the workspace after making changes

---

## Usage

### Dashboard (via browser)

- **Overview Tab**: Global business metrics, daily trends, customer segmentation.
- **Fraud Analysis Tab**: Custom period selection, trends, risk, and top clients.
- **Daily Snapshot Tab**: KPIs and customer activity for any date.
- **Client Deep-dive Tab**: Enter a client ID (or select one from other tabs) for 360° view and transaction breakdown.

### Slack Bot Commands

Use these in any channel where your bot is a member:

- `/dashboard` — Opens interactive dashboard menu in Slack
- `/overview_summary` — Returns current company-wide KPIs
- `/fraud_summary 7` — Last 7 days' fraud stats compared to prior period
- `/daily_summary 2023-12-31` — Summary for specific day (YYYY-MM-DD)
- `/client_summary 12345` — Highlights key stats for one client
- `/assist Open the dashboard` — (Natural language; LLM suggests mapped command and responds)

---

## Troubleshooting

### Database Errors
- Ensure all required tables (see above) exist and your `.env` `DATABASE_URL` is correct.
- Verify DB is running; use `python -c "from db_conn import get_connection; print('Database connected')"`.
  
### Slack Auth/Errors
- Make sure your `SLACK_BOT_TOKEN` starts with `xoxb-` and `SLACK_SIGNING_SECRET` is correct.
- Slack URLs must be HTTPS-accessible by Slack (use ngrok or LocalTunnel).

### LLM Integration
- Check `OPENROUTER_API_KEY` and ensure you haven't exceeded quotas.
- Confirm OpenRouter model is live.

### Port Conflicts
- Default ports: Streamlit 8501, Flask 3000 (changeable in invocation if needed).

---

## Contributing

- Fork the repository.
- Create a new branch (`git checkout -b feature/my-feature`).
- Commit your changes with clear messages.
- Push to your fork and create a Pull Request.

---

## Support

- Review Troubleshooting above
- Check error logs in terminal
- Double-check all values in your `.env`
- Ensure required external services are running (PostgreSQL, ngrok/LocalTunnel, Slack/LLM API)

---

To run this project on any system:

Clone, set up the environment, fill the .env, set up database tables, and follow the steps above.

For live Slack command interaction, always ensure both the Flask API and Streamlit dashboard are running and accessible remotely via the URLs you provide to Slack.

Never commit your .env or database credentials.

Prepared by Aryan Mittal, Pinak Sharma and Ansh Bahirat at Indium Software