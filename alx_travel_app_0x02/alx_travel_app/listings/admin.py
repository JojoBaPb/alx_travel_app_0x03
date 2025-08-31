from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("tx_ref", "booking", "status", "amount", "currency", "paid_at", "created_at")
    search_fields = ("tx_ref", "booking__id")
    list_filter = ("status", "currency")
