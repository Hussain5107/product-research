from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_access_token
from app.database import get_db
from app.models.core import utc_now
from app.models.email import EmailAccount
from app.models.supplier import SupplierContact, SupplierOutreach

router = APIRouter(prefix="/email", tags=["email"])


class EmailAccountUpsert(BaseModel):
    label: str = Field(default="Primary Email", max_length=128)
    sender_name: str | None = Field(default=None, max_length=256)
    sender_email: str = Field(max_length=320)
    smtp_host: str = Field(max_length=256)
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str | None = Field(default=None, max_length=320)
    smtp_password: str | None = None
    use_tls: bool = True
    is_active: bool = True


class SendDraftPayload(BaseModel):
    outreach_id: int
    to_email: str | None = Field(default=None, max_length=320)
    confirm_send: bool = False


@router.get("/account", response_model=dict[str, Any])
async def get_email_account(
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> dict[str, Any]:
    account = await _get_active_account(session)
    if account is None:
        return {"configured": False}
    return _serialize_account(account)


@router.put("/account", response_model=dict[str, Any])
async def save_email_account(
    payload: EmailAccountUpsert,
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> dict[str, Any]:
    account = await _get_active_account(session)
    if account is None:
        account = EmailAccount(
            label=payload.label,
            sender_name=payload.sender_name,
            sender_email=str(payload.sender_email),
            smtp_host=payload.smtp_host,
            smtp_port=payload.smtp_port,
            smtp_username=payload.smtp_username,
            smtp_password=payload.smtp_password,
            use_tls=payload.use_tls,
            is_active=payload.is_active,
        )
        session.add(account)
    else:
        account.label = payload.label
        account.sender_name = payload.sender_name
        account.sender_email = str(payload.sender_email)
        account.smtp_host = payload.smtp_host
        account.smtp_port = payload.smtp_port
        account.smtp_username = payload.smtp_username
        if payload.smtp_password:
            account.smtp_password = payload.smtp_password
        account.use_tls = payload.use_tls
        account.is_active = payload.is_active

    await session.commit()
    await session.refresh(account)
    return _serialize_account(account)


@router.post("/send-draft", response_model=dict[str, Any])
async def send_outreach_draft(
    payload: SendDraftPayload,
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> dict[str, Any]:
    if not payload.confirm_send:
        raise HTTPException(status_code=400, detail="confirm_send must be true before sending email.")

    account = await _get_active_account(session)
    if account is None:
        raise HTTPException(status_code=400, detail="Email account is not configured.")

    outreach_result = await session.execute(
        select(SupplierOutreach).where(SupplierOutreach.id == payload.outreach_id)
    )
    outreach = outreach_result.scalar_one_or_none()
    if outreach is None:
        raise HTTPException(status_code=404, detail="Outreach draft not found.")
    if outreach.channel != "email":
        raise HTTPException(status_code=400, detail="Only email outreach drafts can be sent by email.")
    if outreach.status == "sent":
        raise HTTPException(status_code=400, detail="This draft was already sent.")

    to_email = payload.to_email
    if to_email is None and outreach.contact_id:
        contact_result = await session.execute(
            select(SupplierContact).where(SupplierContact.id == outreach.contact_id)
        )
        contact = contact_result.scalar_one_or_none()
        if contact and contact.email:
            to_email = contact.email
    if to_email is None:
        raise HTTPException(status_code=400, detail="Recipient email is required.")

    _send_email(account, str(to_email), outreach.subject or "Supplier sourcing inquiry", outreach.message_body)
    outreach.status = "sent"
    outreach.sent_at = utc_now()
    await session.commit()
    return {"sent": True, "outreach_id": outreach.id, "to_email": str(to_email), "sent_at": outreach.sent_at.isoformat()}


async def _get_active_account(session: AsyncSession) -> EmailAccount | None:
    result = await session.execute(
        select(EmailAccount).where(EmailAccount.is_active == True).order_by(EmailAccount.created_at.desc())
    )
    return result.scalar_one_or_none()


def _serialize_account(account: EmailAccount) -> dict[str, Any]:
    return {
        "configured": True,
        "id": account.id,
        "label": account.label,
        "sender_name": account.sender_name,
        "sender_email": account.sender_email,
        "smtp_host": account.smtp_host,
        "smtp_port": account.smtp_port,
        "smtp_username": account.smtp_username,
        "smtp_password_configured": bool(account.smtp_password),
        "use_tls": account.use_tls,
        "is_active": account.is_active,
        "created_at": account.created_at.isoformat() if account.created_at else None,
    }


def _send_email(account: EmailAccount, to_email: str, subject: str, body: str) -> None:
    message = EmailMessage()
    sender = account.sender_email
    if account.sender_name:
        sender = f"{account.sender_name} <{account.sender_email}>"
    message["From"] = sender
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(account.smtp_host, account.smtp_port, timeout=30) as smtp:
            if account.use_tls:
                smtp.starttls()
            if account.smtp_username:
                smtp.login(account.smtp_username, account.smtp_password or "")
            smtp.send_message(message)
    except smtplib.SMTPException as exc:
        raise HTTPException(status_code=502, detail=f"SMTP send failed: {exc}") from exc
    except OSError as exc:
        raise HTTPException(status_code=502, detail=f"Could not connect to SMTP server: {exc}") from exc
