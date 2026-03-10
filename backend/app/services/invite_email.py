"""
Invite email service using Resend
"""
import resend
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

resend.api_key = settings.RESEND_API_KEY


def send_invite_email(
    to_email: str,
    invited_by_name: str,
    trip_title: str,
    trip_destinations: list[str],
    role: str,
    invite_token: str,
    
) -> dict:
    """
    Send a trip collaboration invite email via Resend.
    Returns Resend API response dict.
    """
    accept_url = f"{settings.FRONTEND_URL}/invites/{invite_token}/accept"
    destinations_str = ", ".join(trip_destinations)
    role_label = "edit" if role == "editor" else "view"

    html = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; background: #0a0e14; color: #e2e8f0; padding: 32px; border-radius: 12px;">
      <h1 style="color: #38BDF8; margin-bottom: 4px;">✈️ AI Travel Copilot</h1>
      <p style="color: #9CA3AF; margin-top: 0;">You've been invited to collaborate</p>

      <div style="background: #1F2937; border-radius: 8px; padding: 20px; margin: 24px 0;">
        <p style="margin: 0 0 8px;"><strong style="color: #38BDF8;">{invited_by_name}</strong> has invited you to {role_label} their trip:</p>
        <h2 style="margin: 8px 0; color: #fff;">{trip_title}</h2>
        <p style="margin: 4px 0; color: #9CA3AF;">📍 {destinations_str}</p>
        <p style="margin: 4px 0; color: #9CA3AF;">🔑 Your role: <strong style="color: #F59E0B;">{role.capitalize()}</strong></p>
      </div>

      <a href="{accept_url}"
         style="display: inline-block; background: #38BDF8; color: #0a0e14; font-weight: bold;
                padding: 12px 28px; border-radius: 8px; text-decoration: none; font-size: 16px;">
        Accept Invitation
      </a>

      <p style="margin-top: 24px; font-size: 12px; color: #6B7280;">
        Or copy this link: <a href="{accept_url}" style="color: #38BDF8;">{accept_url}</a><br/>
        This invite link will remain valid until accepted or removed.
      </p>
    </div>
    """

    try:
        response = resend.Emails.send({
            "from": settings.FROM_EMAIL,
            "to": [to_email],
            "subject": f"✈️ {invited_by_name} invited you to collaborate on '{trip_title}'",
            "html": html,
        })
        logger.info(f"✅ Invite email sent to {to_email}, id: {response.get('id')}")
        return response
    except Exception as e:
        logger.error(f"❌ Failed to send invite email to {to_email}: {e}")
        raise
