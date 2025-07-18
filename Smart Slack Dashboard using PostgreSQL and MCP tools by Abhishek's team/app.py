from flask import Flask, request, jsonify, make_response
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os, hmac, hashlib, time, json, threading, logging, requests
from dotenv import load_dotenv

# ──────────────────────────────────────────────
# Local modules
# ──────────────────────────────────────────────
from summaries import (
    get_overview_summary,
    get_fraud_summary,
    get_daily_summary,
    get_client_summary,
)
from llm_mapper import call_llm, parse_command, validate_command

# ──────────────────────────────────────────────
# 1. Environment & logging
# ──────────────────────────────────────────────
load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SLACK_BOT_TOKEN      = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
DASHBOARD_URL        = os.getenv("DASHBOARD_URL")

slack_client = WebClient(token=SLACK_BOT_TOKEN)

# ──────────────────────────────────────────────
# 2. Signature verification
# ──────────────────────────────────────────────
def verify_slack_signature(body, timestamp, signature):
    if not SLACK_SIGNING_SECRET:
        logger.warning("SLACK_SIGNING_SECRET not set – skipping verification")
        return True
    if abs(time.time() - int(timestamp)) > 60 * 5:
        return False
    base     = f"v0:{timestamp}:{body}"
    computed = "v0=" + hmac.new(
        SLACK_SIGNING_SECRET.encode(), base.encode(), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(computed, signature)

# ──────────────────────────────────────────────
# 3. Static Overview – for modal only
# ──────────────────────────────────────────────
def get_dashboard_overview() -> str:
    return (
        "📊 *XYZ Bank Smart Transaction Dashboard*\n"
        "Our dashboard streamlines monitoring and analysis of card-transaction data:\n"
        "• **Overview** – company-wide KPIs, long-term trends and demographics\n"
        "• **Fraud Analysis** – period-based fraud patterns, rates and high-risk clients\n"
        "• **Daily Snapshot** – one-day KPIs, merchant-category insights, demographic mix\n"
        "• **Client Deep-Dive** – 360° client profile with lifetime history\n\n"
        "*Key capabilities*\n"
        "• Real-time database connection (PostgreSQL) with 10-minute caching\n"
        "• Interactive Plotly charts, filters & drill-downs\n"
        "• Slack slash-commands and modal pop-ups for quick access\n"
        "• Built with Streamlit + Flask + Slack SDK\n"
        "────────────────────────────\n"
        f"🔗 *Open full dashboard:* {DASHBOARD_URL}"
    )

def append_dashboard_link(text):
    return f"{text}\n\n🔗 *View full dashboard:* {DASHBOARD_URL}"

# ──────────────────────────────────────────────
# 4. Message blocks
# ──────────────────────────────────────────────
def create_dashboard_message(user_id, custom_text=None):
    header = custom_text or f"🚀 *Database Dashboard* for <@{user_id}>"
    return [
        {"type": "header",
         "text": {"type": "plain_text", "text": "📊 Your Database Dashboard", "emoji": True}},
        {"type": "section",
         "text": {"type": "mrkdwn", "text": header}},
        {"type": "divider"},
        {"type": "section",
         "text": {"type": "mrkdwn",
                  "text": "🔍 *Dashboard Features:*\n• Real-time visualisation\n• Interactive charts\n• Fraud detection\n• Filters & analysis"},
         "accessory": {
             "type": "image",
             "image_url": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=500&h=300&fit=crop",
             "alt_text": "Dashboard Preview"}},
        {"type": "actions",
         "elements": [
             {"type": "button",
              "text": {"type": "plain_text", "text": "🔗 Open Dashboard", "emoji": True},
              "style": "primary",
              "url": DASHBOARD_URL,
              "value": "open_dashboard"},
             {"type": "button",
              "text": {"type": "plain_text", "text": "📋 Overview", "emoji": True},
              "value": "show_overview"}]},
        {"type": "context",
         "elements": [{"type": "mrkdwn", "text": f"🌐 *Direct link:* {DASHBOARD_URL}"}]}
    ]

# ──────────────────────────────────────────────
# 5. Dashboard command + Summary thread helpers
# ──────────────────────────────────────────────
def process_dashboard_command(user_id, text):
    try:
        blocks = create_dashboard_message(user_id, custom_text=text)
        slack_client.chat_postMessage(
            channel=user_id,  # DM to user
            text=f"🚀 Database Dashboard for <@{user_id}>",
            blocks=blocks
        )
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        slack_client.chat_postMessage(
            channel=user_id,
            text="❌ Error loading dashboard."
        )

def process_summary(summary_type, user_id, args=None):
    try:
        if summary_type == "overview":
            msg = get_overview_summary()
        elif summary_type == "fraud":
            days = int(args[0]) if args and args[0].isdigit() else 30
            msg  = get_fraud_summary(days)
        elif summary_type == "daily":
            date = args[0] if args else None
            msg  = get_daily_summary(date)
        elif summary_type == "client":
            client = args[0] if args else ""
            msg    = get_client_summary(client) if client else "Please provide a client ID."
        else:
            msg = "Unknown summary type."
        slack_client.chat_postMessage(channel=user_id, text=append_dashboard_link(msg))
    except Exception as e:
        logger.error(f"Summary error: {e}")
        slack_client.chat_postMessage(
            channel=user_id,
            text=f"❌ Error generating {summary_type} summary."
        )

# Helper: dispatch mapped command (from LLM)
def dispatch_mapped_command(mapped_command, user_id):
    try:
        cmd, args = parse_command(mapped_command)

        if cmd == "/dashboard":
            process_dashboard_command(user_id, " ".join(args) if args else None)
        elif cmd == "/overview_summary":
            process_summary("overview", user_id)
        elif cmd == "/fraud_summary":
            process_summary("fraud", user_id, args)
        elif cmd == "/daily_summary":
            process_summary("daily", user_id, args)
        elif cmd == "/client_summary":
            process_summary("client", user_id, args)
        else:
            slack_client.chat_postMessage(
                channel=user_id,
                text="❌ Sorry, I couldn't understand that command."
            )
    except Exception as e:
        logger.error(f"Dispatch error: {e}")
        slack_client.chat_postMessage(
            channel=user_id,
            text="❌ Something went wrong processing your request."
        )

# ──────────────────────────────────────────────
# 6. Flask routes – Slash commands
# ──────────────────────────────────────────────
@app.route('/slack/dashboard', methods=['POST'])
def slack_dashboard():
    body = request.get_data(as_text=True)
    if not verify_slack_signature(body,
                                  request.headers.get('X-Slack-Request-Timestamp'),
                                  request.headers.get('X-Slack-Signature')):
        return make_response("Unauthorized", 401)

    form = request.form
    threading.Thread(target=process_dashboard_command,
                     args=(form['user_id'], form.get('text', '')),
                     daemon=True).start()
    return jsonify({"response_type": "ephemeral", "text": "⏳ Loading dashboard…"})

@app.route('/slack/overview_summary', methods=['POST'])
def cmd_overview():
    body = request.get_data(as_text=True)
    if not verify_slack_signature(body,
                                  request.headers.get('X-Slack-Request-Timestamp'),
                                  request.headers.get('X-Slack-Signature')):
        return make_response("Unauthorized", 401)

    form = request.form
    threading.Thread(target=process_summary,
                     args=("overview", form['user_id'], None),
                     daemon=True).start()
    return jsonify({"response_type": "ephemeral", "text": "⏳ Generating overview…"})

@app.route('/slack/fraud_summary', methods=['POST'])
def cmd_fraud():
    body = request.get_data(as_text=True)
    if not verify_slack_signature(body,
                                  request.headers.get('X-Slack-Request-Timestamp'),
                                  request.headers.get('X-Slack-Signature')):
        return make_response("Unauthorized", 401)

    form = request.form
    args = form.get('text', '').split()
    threading.Thread(target=process_summary,
                     args=("fraud", form['user_id'], args),
                     daemon=True).start()
    return jsonify({"response_type": "ephemeral", "text": "⏳ Generating fraud summary…"})

@app.route('/slack/daily_summary', methods=['POST'])
def cmd_daily():
    body = request.get_data(as_text=True)
    if not verify_slack_signature(body,
                                  request.headers.get('X-Slack-Request-Timestamp'),
                                  request.headers.get('X-Slack-Signature')):
        return make_response("Unauthorized", 401)

    form = request.form
    args = form.get('text', '').split()
    threading.Thread(target=process_summary,
                     args=("daily", form['user_id'], args),
                     daemon=True).start()
    return jsonify({"response_type": "ephemeral", "text": "⏳ Generating daily summary…"})

@app.route('/slack/client_summary', methods=['POST'])
def cmd_client():
    body = request.get_data(as_text=True)
    if not verify_slack_signature(body,
                                  request.headers.get('X-Slack-Request-Timestamp'),
                                  request.headers.get('X-Slack-Signature')):
        return make_response("Unauthorized", 401)

    form = request.form
    args = [form.get('text', '').strip()]
    threading.Thread(target=process_summary,
                     args=("client", form['user_id'], args),
                     daemon=True).start()
    return jsonify({"response_type": "ephemeral", "text": "⏳ Generating client summary…"})

@app.route("/slack/interactions", methods=["POST"])
def slack_interactions():
    try:
        payload = json.loads(request.form["payload"])
        user_id = payload["user"]["id"]
        action_value = payload["actions"][0]["value"]

        if action_value == "show_overview":
            msg = get_dashboard_overview()
            slack_client.chat_postMessage(
                channel=user_id,
                text=msg
            )
            
    except Exception as e:
        logger.error(f"Interaction error: {e}")
        return make_response("Internal error", 500)

    return make_response("", 200)

# ──────────────────────────────────────────────
# 7. NEW – Natural-language assistant endpoint
# ──────────────────────────────────────────────
@app.route('/slack/assist', methods=['POST'])
def slack_assist():
    body = request.get_data(as_text=True)
    if not verify_slack_signature(
        body,
        request.headers.get('X-Slack-Request-Timestamp'),
        request.headers.get('X-Slack-Signature')
    ):
        return make_response("Unauthorized", 401)

    form     = request.form
    user_id  = form['user_id']
    user_msg = form.get('text', '').strip()

    if not user_msg:
        return jsonify({
            "response_type": "ephemeral",
            "text": "🤔 Please type what you need (e.g. *“Show me fraud for 7 days”*)."
        })

    # Move full logic to a background thread
    def handle_assist():
        try:
            mapped_cmd = call_llm(user_msg)
            if not validate_command(mapped_cmd):
                logger.warning(f"LLM could not map: '{user_msg}' → '{mapped_cmd}'")
                slack_client.chat_postMessage(
                    channel=user_id,
                    text="🙁 Sorry, I couldn't figure out that request. Please try phrasing it differently."
                )
                return
            dispatch_mapped_command(mapped_cmd, user_id)
        except Exception as e:
            logger.error(f"Assist thread error: {e}")
            slack_client.chat_postMessage(
                channel=user_id,
                text="❌ Something went wrong with your request."
            )

    threading.Thread(target=handle_assist, daemon=True).start()

    return jsonify({
        "response_type": "ephemeral",
        "text": "🧠 Thinking… I'll DM you in a moment!"
    })

# ──────────────────────────────────────────────
# 8. Health & index
# ──────────────────────────────────────────────
@app.route('/health')
def health():
    return jsonify({"status": "healthy", "dashboard_url": DASHBOARD_URL})

@app.route('/')
def index():
    return jsonify({
        "name": "Database Dashboard Slack Bot (with LLM)",
        "version": "3.0.0",
        "features": [
            "Dashboard modal overview",
            "All 5 native slash commands",
            "Natural-language assistant (/assist)",
            "Secure signature verification"
        ]
    })

# ──────────────────────────────────────────────
# 9. Startup
# ──────────────────────────────────────────────
if __name__ == "__main__":
    if not SLACK_BOT_TOKEN:
        logger.error("Missing SLACK_BOT_TOKEN")
        exit(1)
    app.run(host="0.0.0.0", port=3000, threaded=True)