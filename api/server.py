import os, uuid
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.responses import HTMLResponse
from typing import Optional
from persistence.db import get_conn, init_db
from persistence.repositories import UserRepository
from common.models import UserPreferences, UserContact
from notification.service import NotificationService
from api.schemas import SubscribeIn, SubscribeOut, VerifyOut, RequestEditLinkIn, UpdatePrefsIn, UnsubscribeConfirmIn
from api.security import make_token, read_token
from fastapi.middleware.cors import CORSMiddleware

APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8000")
VERIFY_TTL = 60 * 15  # 15 minutes
EDIT_TTL = 60 * 15  # 15 minutes
UNSUB_TTL = 60 * 60 * 24 * 30  # 30 days

app = FastAPI(title="swe-repo-notify API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def build_edit_link(user: UserContact) -> str:
    token = make_token({"purpose": "edit", "uid": user.id})
    return f"{APP_BASE_URL}/edit?token={token}"


def build_unsubscribe_link(user: UserContact) -> str:
    token = make_token({"purpose": "unsubscribe", "uid": user.id})
    return f"{APP_BASE_URL}/unsubscribe?token={token}"


# --- Wiring: db + repos + notifier (here: simple console sender; swap later) ---
def get_user_repo():
    # Singleton-ish naive approach for demo
    if not hasattr(get_user_repo, "conn"):
        get_user_repo.conn = get_conn(os.getenv("DB_PATH") or "db.sqlite3")
        init_db(get_user_repo.conn)
    return UserRepository(get_user_repo.conn)


class ConsoleSender:

    def send_email(self, to_addr, subject, html_body, text_body):
        print(f"[EMAIL → {to_addr}] {subject}\n{text_body}\n")

    def send_sms(self, to_number, text_body):
        print(f"[SMS → {to_number}] {text_body}\n")


notifier = NotificationService(ConsoleSender(),
                               edit_link_builder=build_edit_link,
                               unsubscribe_link_builder=build_unsubscribe_link)


# --- Helpers ---
def _prefs_from_model(p) -> UserPreferences:
    return UserPreferences(
        subscribe_new_grad=p.subscribe_new_grad,
        subscribe_internship=p.subscribe_internship,
        receive_all=p.receive_all,
        tech_keywords=p.tech_keywords,
        role_keywords=p.role_keywords,
        location_keywords=p.location_keywords,
    )


def _send_verify_link(email: Optional[str], phone: Optional[str],
                      user_id: str):
    payload = {"purpose": "verify", "uid": user_id}
    token = make_token(payload)
    link = f"{APP_BASE_URL}/verify?token={token}"
    subj = "Verify your subscription"
    body = f"Tap to verify: {link}\nThis link expires in 15 minutes."
    if email:
        notifier.sender.send_email(email, subj, body, body)
    if phone:
        notifier.sender.send_sms(phone, body)


def _send_edit_link(email: Optional[str], phone: Optional[str], user_id: str):
    payload = {"purpose": "edit", "uid": user_id}
    token = make_token(payload)
    link = f"{APP_BASE_URL}/edit?token={token}"
    subj = "Edit your notification preferences"
    body = f"Edit link: {link}\nThis link expires in 15 minutes."
    if email:
        notifier.sender.send_email(email, subj, body, body)
    if phone:
        notifier.sender.send_sms(phone, body)


# --- Routes ---
@app.get("/health")
def health():
    return {"ok": True}


@app.post("/subscribe", response_model=SubscribeOut)
def subscribe(payload: SubscribeIn,
              repo: UserRepository = Depends(get_user_repo)):
    if not payload.email and not payload.phone:
        raise HTTPException(400, "Provide email or phone.")
    if not payload.notify_email and not payload.notify_sms:
        raise HTTPException(400, "Enable at least one notification channel.")
    # New or existing user?
    row = repo.get_user_by_email_or_phone(payload.email, payload.phone)
    if row:
        user_id = row["id"]
        # Keep current verified state exactly as-is
        current_verified = bool(row["is_verified"])

        repo.update_user(
            user_id=user_id,
            email=payload.email if payload.email is not None else row["email"],
            phone=payload.phone if payload.phone is not None else row["phone"],
            is_verified=current_verified,
            prefs=_prefs_from_model(payload.prefs),
            notify_email=payload.notify_email,
            notify_sms=payload.notify_sms)

        # Send verify link ONLY if the user is currently unverified
        if not current_verified:
            _send_verify_link(payload.email or row["email"], payload.phone
                              or row["phone"], user_id)
        return SubscribeOut(status="updated")
    else:
        user_id = str(uuid.uuid4())
        repo.create_user(user_id=user_id,
                         email=payload.email,
                         phone=payload.phone,
                         is_verified=False,
                         prefs=_prefs_from_model(payload.prefs),
                         notify_email=payload.notify_email,
                         notify_sms=payload.notify_sms)
        _send_verify_link(payload.email, payload.phone, user_id)
        return SubscribeOut(status="verification_sent")


@app.get("/verify", response_model=VerifyOut)
def verify(token: str = Query(...),
           repo: UserRepository = Depends(get_user_repo)):
    try:
        data = read_token(token, max_age_seconds=VERIFY_TTL)
    except ValueError as e:
        raise HTTPException(400, f"Token error: {e}")
    if data.get("purpose") != "verify":
        raise HTTPException(400, "Wrong token purpose.")
    uid = data.get("uid")
    if not uid:
        raise HTTPException(400, "Invalid token payload.")
    repo.set_verified(uid, True)
    return VerifyOut(status="verified")


@app.post("/request-edit-link", response_model=SubscribeOut)
def request_edit_link(payload: RequestEditLinkIn,
                      repo: UserRepository = Depends(get_user_repo)):
    if not payload.email and not payload.phone:
        raise HTTPException(400, "Provide email or phone.")
    row = repo.get_user_by_email_or_phone(payload.email, payload.phone)
    if not row or not row["is_verified"]:
        # Do not reveal existence; just say "sent" to avoid user enumeration
        return SubscribeOut(status="sent")
    _send_edit_link(row["email"], row["phone"], row["id"])
    return SubscribeOut(status="sent")


@app.get("/edit", response_class=HTMLResponse)
def edit_page(token: str = Query(...)):
    # NOTE: Nothing updated here. Just a minimal HTML page to POST new prefs with token.
    # A real app would serve a proper UI here.
    html = f"""
    <html><body>
      <h1>Edit Preferences</h1>
      <p>Submit your new preferences via POST /update-prefs with this token.</p>
      <code>{token}</code>
    </body></html>
    """
    return HTMLResponse(html)


@app.post("/update-prefs", response_model=SubscribeOut)
def update_prefs(body: UpdatePrefsIn,
                 repo: UserRepository = Depends(get_user_repo)):
    try:
        data = read_token(body.token, max_age_seconds=EDIT_TTL)
    except ValueError as e:
        raise HTTPException(400, f"Token error: {e}")
    if data.get("purpose") != "edit":
        raise HTTPException(400, "Wrong token purpose.")
    uid = data.get("uid")
    if not uid:
        raise HTTPException(400, "Invalid token payload.")
    repo.update_user(user_id=uid,
                     email=None,
                     phone=None,
                     is_verified=None,
                     prefs=_prefs_from_model(body))
    return SubscribeOut(status="updated")


@app.get("/unsubscribe", response_class=HTMLResponse)
def unsubscribe_form(token: str = Query(...),
                     repo: UserRepository = Depends(get_user_repo)):
    # Validate token & purpose up-front (but don't change anything yet)
    try:
        data = read_token(token, max_age_seconds=UNSUB_TTL)
    except ValueError as e:
        raise HTTPException(400, f"Token error: {e}")
    if data.get("purpose") != "unsubscribe":
        raise HTTPException(400, "Wrong token purpose.")
    uid = data.get("uid")
    if not uid:
        raise HTTPException(400, "Invalid token payload.")

    # Load current channel flags so we can pre-check boxes
    row = repo.get_user(uid)
    if not row:
        # Avoid leaking existence; show generic message
        return HTMLResponse(
            "<html><body>Unable to load preferences.</body></html>",
            status_code=404)

    email_checked = "checked" if row["notify_email"] else ""
    sms_checked = "checked" if row["notify_sms"] else ""

    # Simple minimal HTML form
    html = f"""
    <html><body>
      <h1>Unsubscribe</h1>
      <form method="POST" action="/unsubscribe/confirm">
        <input type="hidden" name="token" value="{token}"/>
        <label><input type="checkbox" name="disable_email" value="true" {email_checked}/> Email</label><br/>
        <label><input type="checkbox" name="disable_sms" value="true" {sms_checked}/> SMS</label><br/><br/>
        <button type="submit">Confirm</button>
      </form>
      <p>You can uncheck a channel to keep it active.</p>
    </body></html>
    """
    return HTMLResponse(html)


@app.post("/unsubscribe/confirm", response_model=SubscribeOut)
def unsubscribe_confirm(token: str = Query(None),
                        body: UnsubscribeConfirmIn = None,
                        repo: UserRepository = Depends(get_user_repo)):
    """
    Accepts either form-encoded (token in query or form) or JSON (body.token).
    If both provided, body.token wins.
    """
    # Normalize input
    if body:
        t = body.token
        disable_email = bool(body.disable_email)
        disable_sms = bool(body.disable_sms)
    else:
        # Form-POST path: FastAPI populates form fields into request.state; simpler approach:
        # Expect token in query (?token=...) and booleans as presence of fields in form.
        # To keep code compact here, require JSON in tests or enhance as needed.
        raise HTTPException(
            400, "Send JSON body with token/disable_email/disable_sms")

    try:
        data = read_token(t, max_age_seconds=UNSUB_TTL)
    except ValueError as e:
        raise HTTPException(400, f"Token error: {e}")
    if data.get("purpose") != "unsubscribe":
        raise HTTPException(400, "Wrong token purpose.")
    uid = data.get("uid")
    if not uid:
        raise HTTPException(400, "Invalid token payload.")

    # Apply changes: if disable_x is True → set notify_x = False; if False → leave as-is (or explicitly True if you prefer)
    # Here we explicitly set based on booleans to make it idempotent:
    repo.update_user(
        user_id=uid,
        email=None,
        phone=None,
        is_verified=None,
        prefs=None,
        notify_email=(False if disable_email else True),
        notify_sms=(False if disable_sms else True),
    )
    return SubscribeOut(status="unsubscribed")
