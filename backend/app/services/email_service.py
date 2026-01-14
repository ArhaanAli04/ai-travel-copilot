import resend
from app.core.config import settings
from app.models.trip import Trip
from typing import Optional
import io

resend.api_key = settings.RESEND_API_KEY


class EmailService:
    @staticmethod
    def send_itinerary_email(
        trip: Trip,
        recipient_email: str,
        pdf_bytes: Optional[bytes] = None
    ) -> dict:
        """
        Send trip itinerary via email with optional PDF attachment
        
        Args:
            trip: Trip object
            recipient_email: Email address to send to
            pdf_bytes: Optional PDF file as bytes
            
        Returns:
            dict: Response from Resend API
        """
        
        # Build email subject
        subject = f"Your Trip Itinerary: {trip.title}"
        
        # Build HTML email body
        html_content = EmailService._build_email_html(trip)
        
        # Prepare email parameters
        email_params = {
            "from": settings.FROM_EMAIL,
            "to": [recipient_email],
            "subject": subject,
            "html": html_content,
        }
        
        # Add PDF attachment if provided
        if pdf_bytes:
            email_params["attachments"] = [
                {
                    "filename": f"{trip.title.replace(' ', '_')}_itinerary.pdf",
                    "content": list(pdf_bytes),
                }
            ]
        
        # Send email via Resend
        try:
            response = resend.Emails.send(email_params)
            return {"success": True, "message_id": response["id"]}
        except Exception as e:
            raise Exception(f"Failed to send email: {str(e)}")
    
    @staticmethod
    def _build_email_html(trip: Trip) -> str:
        """Build HTML email content"""
        
        # Format dates
        start_date = trip.start_date.strftime("%b %d, %Y")
        end_date = trip.end_date.strftime("%b %d, %Y")
        
        # Build destinations string
        destinations = ", ".join(trip.destinations) if trip.destinations else "Various"
        
        # Build days HTML
        days_html = ""
        if trip.days:
            for day in trip.days:
                day_date = day.date.strftime("%b %d, %Y") if day.date else "TBA"
                days_html += f"""
                <div style="margin-bottom: 30px; padding: 20px; background-color: #F0F9FF; border-left: 4px solid #38BDF8; border-radius: 8px;">
                    <h3 style="color: #0369A1; margin: 0 0 10px 0; font-size: 18px;">
                        Day {day.day_number} - {day.city or 'TBA'} ({day_date})
                    </h3>
                    {f'<p style="color: #64748B; font-style: italic; margin: 0 0 15px 0;">{day.theme}</p>' if day.theme else ''}
                    <div style="margin-left: 15px;">
                """
                
                if day.activities:
                    for idx, activity in enumerate(day.activities, 1):
                        time_str = ""
                        if activity.start_time and activity.end_time:
                            time_str = f"{activity.start_time} - {activity.end_time}"
                        elif activity.start_time:
                            time_str = f"{activity.start_time} onwards"
                        
                        days_html += f"""
                        <div style="margin-bottom: 15px;">
                            <h4 style="color: #1E293B; margin: 0 0 5px 0; font-size: 16px;">
                                {idx}. {activity.title}
                                {f'<span style="color: #64748B; font-weight: normal; font-size: 14px;">({time_str})</span>' if time_str else ''}
                            </h4>
                            {f'<p style="color: #475569; margin: 0; line-height: 1.6;">{activity.description}</p>' if activity.description else ''}
                        </div>
                        """
                else:
                    days_html += '<p style="color: #94A3B8; font-style: italic;">No activities planned for this day</p>'
                
                days_html += """
                    </div>
                </div>
                """
        
        # Build interests HTML
        interests_html = ""
        if trip.interests:
            interests_html = f"""
            <p style="color: #475569; margin: 5px 0;">
                <strong>Interests:</strong> {", ".join(trip.interests)}
            </p>
            """
        
        # Build budget HTML
        budget_html = ""
        if trip.budget:
            budget_html = f"""
            <p style="color: #475569; margin: 5px 0;">
                <strong>Budget:</strong> ${trip.budget} {trip.budget_currency}
            </p>
            """
        
        # Complete HTML email
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #F8FAFC; padding: 20px; margin: 0;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #38BDF8 0%, #0EA5E9 100%); padding: 30px; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 28px;">Trip Itinerary</h1>
                    <p style="color: rgba(255, 255, 255, 0.9); margin: 10px 0 0 0; font-size: 16px;">Your adventure awaits!</p>
                </div>
                
                <!-- Trip Details -->
                <div style="padding: 30px;">
                    <h2 style="color: #1E293B; margin: 0 0 20px 0; font-size: 24px; border-bottom: 2px solid #E2E8F0; padding-bottom: 10px;">
                        {trip.title}
                    </h2>
                    
                    <div style="background-color: #F8FAFC; padding: 20px; border-radius: 8px; margin-bottom: 30px;">
                        <p style="color: #475569; margin: 5px 0;">
                            <strong>From:</strong> {trip.origin} → {destinations}
                        </p>
                        <p style="color: #475569; margin: 5px 0;">
                            <strong>Dates:</strong> {start_date} - {end_date}
                        </p>
                        <p style="color: #475569; margin: 5px 0;">
                            <strong>Travelers:</strong> {trip.traveler_count}
                        </p>
                        {budget_html}
                        {interests_html}
                    </div>
                    
                    <!-- Days Itinerary -->
                    <h3 style="color: #1E293B; margin: 0 0 20px 0; font-size: 20px;">Your Itinerary</h3>
                    {days_html if days_html else '<p style="color: #94A3B8; font-style: italic;">No itinerary generated yet</p>'}
                </div>
                
                <!-- Footer -->
                <div style="background-color: #F8FAFC; padding: 20px; text-align: center; border-top: 1px solid #E2E8F0;">
                    <p style="color: #64748B; margin: 0; font-size: 14px;">
                        Generated by <strong>AI Travel Copilot</strong>
                    </p>
                    <p style="color: #94A3B8; margin: 10px 0 0 0; font-size: 12px;">
                        Happy travels! ✈️
                    </p>
                </div>
                
            </div>
        </body>
        </html>
        """
        
        return html
