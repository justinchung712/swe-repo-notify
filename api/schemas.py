from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional


class PrefsIn(BaseModel):
    subscribe_new_grad: bool
    subscribe_internship: bool
    receive_all: bool
    tech_keywords: List[str] = Field(default_factory=list)
    role_keywords: List[str] = Field(default_factory=list)
    location_keywords: List[str] = Field(default_factory=list)


class SubscribeIn(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    notify_email: bool = False
    notify_sms: bool = False
    prefs: PrefsIn


class SubscribeOut(BaseModel):
    status: str


class RequestEditLinkIn(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class UpdatePrefsIn(PrefsIn):
    token: str


class VerifyOut(BaseModel):
    status: str
