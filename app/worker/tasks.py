import smtplib
import io
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from app.config import settings

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

from datetime import datetime
from celery import chain, shared_task, Task
import logging
import base64
from typing import cast


logger = logging.getLogger(__name__)


def _get_booking_data_from_db(booking_id: int) -> dict:
    from app.database import sync_session
    from app.crud import get_booking_sync, get_user_sync

    with sync_session() as session:
        booking = get_booking_sync(session, booking_id)
        if not booking:
            raise ValueError(f"Booking {booking_id} not found")

        guest = get_user_sync(session, booking.guest_id)
        if not guest:
            raise ValueError(f"Guest {booking.guest_id} not found")

        return {
            "id": booking.id,
            "guest_id": booking.guest_id,
            "guest_name": f"{guest.first_name} {guest.last_name}",
            "property_id": booking.property_id,
            "property_title": booking.property.title,
            "check_in": booking.check_in.strftime("%Y-%m-%d"),
            "check_out": booking.check_out.strftime("%Y-%m-%d"),
            "guests": booking.guests,
            "total_price": booking.total_price,
        }


@shared_task(name="app.celery.tasks.generate_booking_pdf")
def generate_booking_pdf(booking_data: dict) -> str:
    buffer = io.BytesIO()

    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    pdf.setFont("Helvetica-Bold", 24)
    pdf.drawString(2 * cm, height - 3 * cm, "BOOKING CONFIRMATION")
    pdf.line(2 * cm, height - 3.5 * cm, width - 2 * cm, height - 3.5 * cm)

    pdf.setFont("Helvetica", 12)
    y_position = height - 5 * cm

    lines = [
        f"Booking ID: {booking_data['id']}",
        f"Guest: {booking_data['guest_name']}",
        f"Property: {booking_data['property_title']}",
        f"Check-in: {booking_data['check_in']}",
        f"Check-out: {booking_data['check_out']}",
        f"Number of guests: {booking_data['guests']}",
        f"Total price: ${booking_data['total_price']:.2f}",
        f"",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    ]

    for line in lines:
        pdf.drawString(2 * cm, y_position, line)
        y_position -= 0.7 * cm

    pdf.save()

    buffer.seek(0)

    return base64.b64encode(buffer.read()).decode("utf-8")


@shared_task(
    name="app.celery.tasks.send_booking_email",
    max_retries=3,
    bind=True,
    default_retry_delay=60,
)
def send_booking_email(
    self,
    pdf_b64: str,
    recipient_email: str,
    booking_data: dict,
) -> dict:
    pdf_bytes = base64.b64decode(pdf_b64)
    logger.info(f"Sending email to {recipient_email} for booking {booking_data['id']}")
    try:
        msg = MIMEMultipart()
        msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
        msg["To"] = recipient_email
        msg["Subject"] = f"Booking Confirmation #{booking_data['id']}"

        body = f"""
            Hello, {booking_data['guest_name']}.
            
            Your booking has been confirmed!

            Details:
            - Property: {booking_data['property_title']}
            - Check-in: {booking_data['check_in']}
            - Check-out: {booking_data['check_out']}
            - Guests: {booking_data['guests']}
            - Price: {booking_data['total_price']:.2f}
        """

        msg.attach(MIMEText(body, "plain"))

        pdf_attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
        pdf_attachment.add_header(
            "Content-Disposition",
            "attachment",
            filename=f'booking_{booking_data["id"]}.pdf',
        )
        msg.attach(pdf_attachment)

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"Email successfully sent to {recipient_email}")
        return {"status": "success", "message": f"Email sent to {recipient_email}"}
    except smtplib.SMTPException as e:
        raise self.retry(exc=e, countdown=5)
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}


@shared_task(name="app.celery.tasks.process_booking_confirmation")
def process_booking_confirmation(booking_id: int, user_email: str) -> str:
    booking_data = _get_booking_data_from_db(booking_id)

    workflow = chain(
        cast(Task, generate_booking_pdf).s(booking_data),
        cast(Task, send_booking_email).s(user_email, booking_data),
    )

    result = workflow.apply_async()

    if result is None:
        raise RuntimeError("Failed to enqueue booking workflow")

    return result.id
