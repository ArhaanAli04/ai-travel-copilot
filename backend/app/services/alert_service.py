"""
Alert service for sending notifications on critical events
"""
import logging
import httpx
from typing import List, Optional
from datetime import datetime

from app.core.config import settings


logger = logging.getLogger(__name__)


class AlertService:
    """Service for sending alerts via email and webhooks"""
    
    def __init__(self):
        self.resend_api_key = settings.RESEND_API_KEY
        self.from_email = settings.FROM_EMAIL
        self.enabled = bool(self.resend_api_key)
        
        if not self.enabled:
            logger.warning("⚠️ Alert service disabled: RESEND_API_KEY not configured")
    
    async def send_email_alert(
        self,
        to_emails: List[str],
        subject: str,
        message: str,
        priority: str = "normal"
    ) -> bool:
        """
        Send email alert using Resend API
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            message: Email body (plain text or HTML)
            priority: "low", "normal", or "high"
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning("Email alerts disabled - skipping")
            return False
        
        if not to_emails:
            logger.warning("No email recipients specified - skipping")
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {self.resend_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "from": self.from_email,
                        "to": to_emails,
                        "subject": subject,
                        "html": self._format_html_email(subject, message, priority),
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ Alert email sent to {len(to_emails)} recipients")
                    return True
                else:
                    logger.error(f"❌ Failed to send alert email: {response.status_code} - {response.text}")
                    return False
        
        except Exception as e:
            logger.error(f"❌ Error sending alert email: {e}")
            return False
    
    def _format_html_email(self, subject: str, message: str, priority: str) -> str:
        """Format alert email as HTML"""
        # Priority color mapping
        colors = {
            "low": "#3B82F6",      # Blue
            "normal": "#F59E0B",   # Orange
            "high": "#EF4444",     # Red
        }
        color = colors.get(priority, colors["normal"])
        
        # Priority icon
        icons = {
            "low": "ℹ️",
            "normal": "⚠️",
            "high": "🚨",
        }
        icon = icons.get(priority, icons["normal"])
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: {color}; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #f9fafb; padding: 20px; border-radius: 0 0 8px 8px; }}
                .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #6b7280; }}
                pre {{ background-color: #e5e7eb; padding: 10px; border-radius: 4px; overflow-x: auto; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>{icon} {subject}</h2>
                </div>
                <div class="content">
                    <pre>{message}</pre>
                    <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                    <p><strong>Environment:</strong> {settings.ENV}</p>
                </div>
                <div class="footer">
                    <p>This is an automated alert from AI Travel Copilot monitoring system.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    async def send_storage_alert(
        self,
        to_emails: List[str],
        storage_mb: float,
        usage_percentage: float,
        collections: dict
    ):
        """Send storage threshold alert"""
        priority = "high" if storage_mb > 950 else "normal"
        
        subject = f"{'🚨 CRITICAL' if priority == 'high' else '⚠️ WARNING'}: Storage Threshold Exceeded"
        
        collections_info = "\n".join([
            f"  • {name}: {stats.get('vectors_count', 0)} vectors, {stats.get('storage_estimate_mb', 0):.2f} MB"
            for name, stats in collections.items()
        ])
        
        message = f"""
Storage usage has exceeded the threshold!

Current Usage: {storage_mb:.2f} MB ({usage_percentage:.1f}% of 1GB free tier)
Threshold: 850 MB (85%)

Collections:
{collections_info}

Action Required:
- Review and delete unused data
- Consider upgrading to a paid plan
- Optimize vector dimensions (currently using 768-dim embeddings)

Dashboard: http://localhost:8000/api/admin/monitoring
        """
        
        await self.send_email_alert(to_emails, subject, message, priority)
    
    async def send_ingestion_failure_alert(
        self,
        to_emails: List[str],
        job_name: str,
        error_message: str,
        cities: List[str]
    ):
        """Send ingestion job failure alert"""
        subject = f"🚨 Ingestion Job Failed: {job_name}"
        
        message = f"""
Background ingestion job has failed!

Job: {job_name}
Cities: {', '.join(cities)}
Error: {error_message}

Please check the logs for more details:
  docker logs <container_id> | grep ERROR

Dashboard: http://localhost:8000/api/admin/monitoring
        """
        
        await self.send_email_alert(to_emails, subject, message, "high")
    
    async def send_service_down_alert(
        self,
        to_emails: List[str],
        service_name: str,
        error_message: str
    ):
        """Send service down alert"""
        subject = f"🚨 CRITICAL: {service_name} Service Down"
        
        message = f"""
A critical service is unavailable!

Service: {service_name}
Error: {error_message}

Immediate action required to restore service.

Health Check: http://localhost:8000/api/health
        """
        
        await self.send_email_alert(to_emails, subject, message, "high")


# Singleton instance
alert_service = AlertService()
