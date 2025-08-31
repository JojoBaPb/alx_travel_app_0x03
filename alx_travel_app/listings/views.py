from rest_framework import viewsets
from .models import Listing, Booking
from .serializers import ListingSerializer, BookingSerializer
import json
import uuid
import requests
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.urls import reverse

from .models import Payment
from .models import Booking  # adjust if Booking lives elsewhere

API_BASE = "https://api.chapa.co/v1"


def _build_tx_ref(booking_id: int) -> str:
    suffix = uuid.uuid4().hex[:8]
    return f"booking-{booking_id}-{suffix}"


@require_POST
@csrf_exempt
def initiate_payment(request):
    """
    Expects JSON: {"booking_id": 123}
    Uses Booking.total_amount (if present) else requires "amount" in payload.
    """
    try:
        payload = json.loads(request.body.decode())
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    booking_id = payload.get("booking_id")
    if not booking_id:
        return HttpResponseBadRequest("booking_id is required")

    booking = get_object_or_404(Booking, id=booking_id)

    amount = getattr(booking, "total_amount", None) or payload.get("amount")
    if not amount:
        return HttpResponseBadRequest("amount is required if Booking has no total_amount")

    currency = getattr(settings, "CHAPA_CURRENCY", "ETB")

    # Customer fields — adapt to your Booking model structure
    email = getattr(booking, "email", None) or getattr(getattr(booking, "user", None), "email", None)
    first_name = getattr(booking, "first_name", "Customer")
    last_name = getattr(booking, "last_name", "")

    tx_ref = _build_tx_ref(booking.id)

    init_payload = {
        "amount": str(amount),
        "currency": currency,
        "email": email or "customer@example.com",
        "first_name": first_name,
        "last_name": last_name,
        "tx_ref": tx_ref,
        "callback_url": settings.CHAPA_CALLBACK_URL,  # where we verify
        "return_url": settings.CHAPA_RETURN_URL,      # where to redirect UI after checkout
        "customization": {
            "title": "Travel Booking Payment",
            "description": f"Payment for booking #{booking.id}",
        },
    }

    headers = {
        "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    init_url = f"{API_BASE}/transaction/initialize"
    r = requests.post(init_url, headers=headers, json=init_payload, timeout=20)
    try:
        data = r.json()
    except Exception:
        return JsonResponse({"error": "Bad response from Chapa", "text": r.text}, status=502)

    # Create Payment row
    payment = Payment.objects.create(
        booking=booking,
        tx_ref=tx_ref,
        amount=amount,
        currency=currency,
        status=Payment.Status.PENDING,
        initialize_resp=data,
        checkout_url=(data.get("data") or {}).get("checkout_url"),
    )

class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

