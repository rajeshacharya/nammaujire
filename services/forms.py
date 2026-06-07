from django import forms
from .models import Booking

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['name','booking_datetime','phone', 'email', 'message', ]
        widgets = {
            'booking_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }