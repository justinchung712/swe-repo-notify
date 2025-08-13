from typing import List
from common.models import UserPreferences, UserContact


def hydrate_users(rows) -> List[UserContact]:
    out = []
    for r in rows:
        prefs = UserPreferences(
            subscribe_new_grad=bool(r["subscribe_new_grad"]),
            subscribe_internship=bool(r["subscribe_internship"]),
            receive_all=bool(r["receive_all"]),
            tech_keywords=[
                x for x in (r["tech_keywords"] or "").split(",") if x
            ],
            role_keywords=[
                x for x in (r["role_keywords"] or "").split(",") if x
            ],
            location_keywords=[
                x for x in (r["location_keywords"] or "").split(",") if x
            ],
        )
        out.append(
            UserContact(
                id=r["id"],
                email=r["email"],
                phone=r["phone"],
                is_verified=bool(r["is_verified"]),
                notify_email=bool(r["notify_email"]),
                notify_sms=bool(r["notify_sms"]),
                prefs=prefs,
            ))
    return out
