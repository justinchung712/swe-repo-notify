import os
from itsdangerous import URLSafeTimedSerializer, BadSignature, BadTimeSignature, SignatureExpired


def _serializer() -> URLSafeTimedSerializer:
    secret = os.getenv("APP_SECRET", "dev-secret-change-me")
    return URLSafeTimedSerializer(secret_key=secret, salt="swe-repo-notify")


def make_token(payload: dict) -> str:
    return _serializer().dumps(payload)


def read_token(token: str, max_age_seconds: int):
    try:
        return _serializer().loads(token, max_age=max_age_seconds)
    except SignatureExpired as e:
        raise ValueError("expired") from e
    except (BadTimeSignature, BadSignature) as e:
        raise ValueError("invalid") from e
