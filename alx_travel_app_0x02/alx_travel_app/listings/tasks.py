from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Payment

@shared_task
def send_payment_confirmation(payment_id: str):
    payment = Payment.objects.select_related("booking").get(id=payment_id)
    booking = payment.booking

    subject = f"Booking #{booking.id} — Payment received"
    body = (
        f"Hi,\n\nYour payment of {payment.amount} {payment.currency} for booking #{booking.id} "
        f"was successful. Reference: {payment.tx_ref}.\n\n"
        f"Thank you for booking with us!"
    )

    send_mail(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        [getattr(booking, "email", None) or getattr(getattr(booking, "user", None), "email", None)],
        fail_silently=True,
    )
