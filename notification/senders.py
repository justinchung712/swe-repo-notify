import os
from typing import Optional


class ResendEmailSender:

    def __init__(self,
                 api_key: Optional[str] = None,
                 from_addr: Optional[str] = None):
        import resend  # Lazy import so tests don't need the lib
        self.resend = resend
        self.resend.api_key = api_key or os.getenv("RESEND_API_KEY", "")
        self.from_addr = from_addr or os.getenv("EMAIL_FROM",
                                                "noreply@example.com")

    def send_email(self, to_addr: str, subject: str, html_body: str,
                   text_body: str):
        # text_body is optional; Resend will auto-generate if omitted
        self.resend.Emails.send({
            "from": self.from_addr,
            "to": [to_addr],
            "subject": subject,
            "html": html_body or f"<pre>{text_body}</pre>",
            "text": text_body or None,
        })


class TwilioSmsSender:

    def __init__(self,
                 account_sid: Optional[str] = None,
                 auth_token: Optional[str] = None,
                 from_number: Optional[str] = None):
        from twilio.rest import Client
        self.client = Client(
            account_sid or os.getenv("TWILIO_ACCOUNT_SID", ""), auth_token
            or os.getenv("TWILIO_AUTH_TOKEN", ""))
        self.from_number = from_number or os.getenv("TWILIO_FROM_NUMBER", "")

    def send_sms(self, to_number: str, text_body: str):
        self.client.messages.create(
            to=to_number,
            from_=self.from_number,
            body=text_body[:1590],  # Hard cap
        )
