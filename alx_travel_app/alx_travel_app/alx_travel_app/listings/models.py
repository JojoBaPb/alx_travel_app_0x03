import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Listing(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=255)
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Booking(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.listing.title}"

class Review(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s review of {self.listing.title}"

class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey("Booking", on_delete=models.PROTECT, related_name="payments")

    tx_ref = models.CharField(max_length=64, unique=True, db_index=True)
    chapa_ref = models.CharField(max_length=64, blank=True, null=True)  # Chapa internal ref (ref_id)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="ETB")

    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)

    checkout_url = models.URLField(blank=True, null=True)  # redirect here to pay

    initialize_resp = models.JSONField(blank=True, null=True)
    verify_resp = models.JSONField(blank=True, null=True)

    paid_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def mark_success(self, chapa_ref: str | None = None):
        self.status = self.Status.SUCCESS
        if chapa_ref:
            self.chapa_ref = chapa_ref
        self.paid_at = self.paid_at or timezone.now()
        self.save(update_fields=["status", "chapa_ref", "paid_at", "updated_at"])

    def __str__(self):
        return f"Payment<{self.tx_ref}> {self.status} {self.amount} {self.currency}"

    class Meta:
        indexes = [
            models.Index(fields=["booking", "status"]),
        ]
