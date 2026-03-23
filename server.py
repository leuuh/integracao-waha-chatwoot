"""
WAHA <-> Chatwoot Integration Server
Serve the dashboard and proxy API calls to WAHA and Chatwoot.
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder=".")
CORS(app)

# ─── Configuration ────────────────────────────────────────────────────────────
WAHA_URL    = os.getenv("WAHA_URL", "http://localhost:3000")
WAHA_KEY    = os.getenv("WAHA_KEY", "")
WAHA_LOGIN  = os.getenv("WAHA_LOGIN", "")
WAHA_PASS   = os.getenv("WAHA_PASS", "")

CW_URL      = os.getenv("CW_URL", "http://localhost:3000")
CW_TOKEN    = os.getenv("CW_TOKEN", "")
CW_ACCOUNT  = os.getenv("CW_ACCOUNT", "1")

WAHA_HEADERS = {
    "X-Api-Key": WAHA_KEY,
    "Content-Type": "application/json",
    "Accept": "application/json",
}
CW_HEADERS = {
    "api_access_token": CW_TOKEN,
    "Content-Type": "application/json",
}

# ─── Helper ───────────────────────────────────────────────────────────────────

def waha_get(path, **kwargs):
    r = requests.get(f"{WAHA_URL}{path}", headers=WAHA_HEADERS,
                     auth=(WAHA_LOGIN, WAHA_PASS), timeout=30, **kwargs)
    r.raise_for_status()
    return r.json()

def waha_put(path, payload):
    r = requests.put(f"{WAHA_URL}{path}", headers=WAHA_HEADERS,
                     auth=(WAHA_LOGIN, WAHA_PASS), json=payload, timeout=30)
    r.raise_for_status()
    return r.json() if r.content else {}

def waha_post(path, payload):
    r = requests.post(f"{WAHA_URL}{path}", headers=WAHA_HEADERS,
                      auth=(WAHA_LOGIN, WAHA_PASS), json=payload, timeout=30)
    r.raise_for_status()
    return r.json() if r.content else {}

def cw_get(path):
    r = requests.get(f"{CW_URL}{path}", headers=CW_HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()

def cw_post(path, payload):
    r = requests.post(f"{CW_URL}{path}", headers=CW_HEADERS,
                      json=payload, timeout=30)
    r.raise_for_status()
    return r.json()

def cw_patch(path, payload):
    r = requests.patch(f"{CW_URL}{path}", headers=CW_HEADERS,
                       json=payload, timeout=30)
    r.raise_for_status()
    return r.json()

# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(".", "dashboard.html")


@app.route("/api/waha/sessions")
def get_sessions():
    """Return all WAHA sessions with their status."""
    try:
        data = waha_get("/api/sessions?all=true")
        return jsonify({"ok": True, "sessions": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/chatwoot/inboxes")
def get_inboxes():
    """Return all Chatwoot inboxes."""
    try:
        data = cw_get(f"/api/v1/accounts/{CW_ACCOUNT}/inboxes")
        return jsonify({"ok": True, "inboxes": data.get("payload", [])})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/integrate", methods=["POST"])
def integrate():
    """
    Integrate a WAHA session with Chatwoot.
    Body: { session: str, inbox_id: int|null, inbox_name: str|null }
      - If inbox_id is given, use that existing inbox
      - If inbox_id is null, create a new inbox with inbox_name (falls back to session name)
    """
    body = request.json or {}
    session_name = body.get("session")
    inbox_id     = body.get("inbox_id")
    inbox_name   = body.get("inbox_name") or session_name

    if not session_name:
        return jsonify({"ok": False, "error": "session name required"}), 400

    try:
        # ── Step 1: Resolve or create Chatwoot inbox ──────────────────────────
        if not inbox_id:
            # Create a new API inbox in Chatwoot
            inbox_payload = {
                "name": inbox_name,
                "channel": {"type": "api"},
            }
            inbox = cw_post(f"/api/v1/accounts/{CW_ACCOUNT}/inboxes", inbox_payload)
            inbox_id = inbox["id"]
            inbox_identifier = inbox.get("inbox_identifier", "")
            webhook_url = inbox.get("webhook_url", "")
            created = True
        else:
            # Fetch existing inbox details
            all_inboxes = cw_get(f"/api/v1/accounts/{CW_ACCOUNT}/inboxes")
            inbox = next(
                (i for i in all_inboxes.get("payload", []) if i["id"] == inbox_id),
                None
            )
            if not inbox:
                return jsonify({"ok": False, "error": f"Inbox {inbox_id} not found"}), 404
            inbox_identifier = inbox.get("inbox_identifier", "")
            webhook_url = inbox.get("webhook_url", "")
            created = False

        # ── Step 2: Configure Chatwoot App officially via WAHA Apps API ───────
        import uuid
        app_id = f"app_{uuid.uuid4().hex}"

        app_payload = {
            "id": app_id,
            "session": session_name,
            "app": "chatwoot",
            "enabled": True,
            "config": {
                "url": CW_URL,
                "accountId": int(CW_ACCOUNT),
                "accountToken": CW_TOKEN,
                "inboxId": int(inbox_id),
                "inboxIdentifier": inbox_identifier,
                "locale": "pt-BR",
                "linkPreview": "OFF",
                "templates": {},
                "commands": {
                    "server": True,
                    "queue": True
                },
                "conversations": {
                    "sort": "created_newest",
                    "status": None,
                    "markAsRead": True
                }
            }
        }

        # Clear any existing chatwoot apps for this session to avoid duplicates
        try:
            apps = waha_get(f"/api/apps?session={session_name}")
            for a in apps:
                if a.get("app") == "chatwoot":
                    requests.delete(
                        f"{WAHA_URL}/api/apps/{a.get('id')}", 
                        headers=WAHA_HEADERS, 
                        auth=(WAHA_LOGIN, WAHA_PASS),
                        timeout=30
                    )
        except Exception:
            pass

        # Use the official Apps endpoint
        waha_post("/api/apps", app_payload)

        # ── Step 3: Configure Chatwoot Inbox Webhook URL ──────────────────────
        # Chatwoot needs to know where to send its responses. The WAHA app generates
        # a specific webhook URL: {WAHA_URL}/webhooks/chatwoot/{session_name}/{app_id}
        cw_inbox_webhook_url = f"{WAHA_URL}/webhooks/chatwoot/{session_name}/{app_id}"
        
        try:
            cw_patch(f"/api/v1/accounts/{CW_ACCOUNT}/inboxes/{inbox_id}", {
                "channel": {
                    "webhook_url": cw_inbox_webhook_url
                }
            })
        except Exception as e:
            print(f"Warning: Failed to set Chatwoot webhook URL: {e}")

        # Clear the fallback webhook if it exists to clean up old experiments
        try:
            session_info = waha_get(f"/api/sessions/{session_name}")
            existing_webhooks = session_info.get("config", {}).get("webhooks", []) or []
            clean_webhooks = [
                w for w in existing_webhooks
                if not (isinstance(w, dict) and "chatwoot" in w.get("url", ""))
            ]
            if len(clean_webhooks) < len(existing_webhooks):
                waha_put(f"/api/sessions/{session_name}", {"config": {"webhooks": clean_webhooks}})
        except Exception:
            pass

        return jsonify({
            "ok": True,
            "session": session_name,
            "inbox_id": inbox_id,
            "inbox_name": inbox_name,
            "inbox_identifier": inbox_identifier,
            "inbox_created": created,
            "webhook_url": cw_inbox_webhook_url,
            "method": "official_waha_app",
        })

    except requests.HTTPError as e:
        resp_text = e.response.text if e.response else str(e)
        return jsonify({"ok": False, "error": f"HTTP {e.response.status_code}: {resp_text}"}), 500
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/session/create", methods=["POST"])
def create_session():
    """
    Create a new WAHA session and optionally auto-integrate with Chatwoot.
    Body: { name: str, auto_integrate: bool, inbox_name: str|null }
    """
    body = request.json or {}
    name           = body.get("name")
    auto_integrate = body.get("auto_integrate", True)
    inbox_name     = body.get("inbox_name") or name

    if not name:
        return jsonify({"ok": False, "error": "session name required"}), 400

    try:
        # Create the session
        waha_post("/api/sessions", {"name": name})

        result = {"ok": True, "session": name, "integrated": False}

        if auto_integrate:
            import requests as req
            import time
            # Small delay to let WAHA initialize the session
            time.sleep(1)
            # Call our own integrate endpoint logic directly
            integration_body = {
                "session": name,
                "inbox_id": None,
                "inbox_name": inbox_name,
            }
            # Reuse the integrate function
            with app.test_request_context(
                "/api/integrate",
                method="POST",
                json=integration_body,
                content_type="application/json"
            ):
                # Call the function directly
                integ_resp = integrate()
                if hasattr(integ_resp, "get_json"):
                    integ_data = integ_resp.get_json()
                else:
                    integ_data = {}
            result["integrated"] = integ_data.get("ok", False)
            result["inbox_id"] = integ_data.get("inbox_id")
            result["integration_details"] = integ_data

        return jsonify(result)

    except requests.HTTPError as e:
        resp_text = e.response.text if e.response else str(e)
        return jsonify({"ok": False, "error": f"HTTP {e.response.status_code}: {resp_text}"}), 500
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/session/<name>/start", methods=["POST"])
def start_session(name):
    try:
        result = waha_post(f"/api/sessions/{name}/start", {})
        return jsonify({"ok": True, "result": result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/session/<name>/qr")
def get_qr(name):
    """Return QR code image URL for a session."""
    try:
        data = waha_get(f"/api/{name}/auth/qr?format=json")
        return jsonify({"ok": True, "qr": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    print("=" * 60)
    print("  WAHA <-> Chatwoot Integration Dashboard")
    print("  Open: http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, port=5000, host="0.0.0.0")
