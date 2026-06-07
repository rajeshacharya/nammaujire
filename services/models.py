from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class ServiceProvider(models.Model):
    SERVICE_CHOICES = [
        ('AUTO', 'Auto Driver'),
        ('PLUMBER', 'Plumber'),
        ('ELECTRICIAN', 'Electrician'),
        ('BARBER', 'Barber'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    service_type = models.CharField(max_length=20, choices=SERVICE_CHOICES)
    phone = models.CharField(max_length=15)
    location = models.CharField(max_length=100)
    is_available = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False) # Admin approval required to show in listings

    def __str__(self):
        return f"{self.name} ({self.get_service_type_display()})"

class Booking(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
    ]

    provider = models.ForeignKey(ServiceProvider, on_delete=models.CASCADE)
    customer_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)
    booking_datetime = models.DateTimeField()  # User input
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    creation_datetime = models.DateTimeField(auto_now_add=True)  # Auto-filled on creation

    def __str__(self):
        return f"Booking for {self.provider.name} by {self.name} - {self.status}"