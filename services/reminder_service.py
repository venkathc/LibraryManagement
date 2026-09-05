"""Email delivery for borrower return reminders."""

from __future__ import annotations

import re
import smtplib
import ssl
from email.message import EmailMessage
from typing import Callable

from config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD


class ReminderService:
    """Send borrower reminders through a configured Gmail account."""

    def __init__(
        self,
        address: str = GMAIL_ADDRESS,
        app_password: str = GMAIL_APP_PASSWORD,
        smtp_factory: Callable[..., smtplib.SMTP_SSL] = smtplib.SMTP_SSL,
    ) -> None:
        self.address = address
        self.app_password = app_password
        self.smtp_factory = smtp_factory

    @property
    def configured(self) -> bool:
        """Return whether the Gmail sender credentials are available."""
        return bool(self.address and self.app_password)

    @staticmethod
    def email_from_contact(contact: str | None) -> str | None:
        """Extract a single email address from the saved borrower contact field."""
        match = re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", contact or "", re.IGNORECASE)
        return match.group(0) if match else None

    def send_email(self, recipient: str, subject: str, message: str) -> None:
        """Deliver a plain-text reminder using Gmail's SSL SMTP endpoint."""
        if not self.configured:
            raise ValueError("Gmail is not configured. Add GMAIL_ADDRESS and GMAIL_APP_PASSWORD to .env.")
        if not self.email_from_contact(recipient):
            raise ValueError("This borrower does not have a valid email address.")
        email = EmailMessage()
        email["From"] = self.address
        email["To"] = recipient
        email["Subject"] = subject
        email.set_content(message)
        try:
            with self.smtp_factory("smtp.gmail.com", 465, timeout=15) as server:
                server.login(self.address, self.app_password)
                server.send_message(email)
                return
        except OSError as ssl_error:
            try:
                with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as server:
                    server.starttls(context=ssl.create_default_context())
                    server.login(self.address, self.app_password)
                    server.send_message(email)
                    return
            except OSError as starttls_error:
                raise ValueError(
                    "Could not reach Gmail SMTP on ports 465 or 587. Check your internet, VPN, firewall, or network policy."
                ) from starttls_error
            except smtplib.SMTPException as error:
                raise ValueError("Gmail rejected the reminder. Check the sender address and app password.") from error
        except smtplib.SMTPException as error:
            raise ValueError("Gmail rejected the reminder. Check the sender address and app password.") from error