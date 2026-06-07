from django import forms

from .models import LocalUpdate


class LocalUpdateSubmissionForm(forms.ModelForm):
    class Meta:
        model = LocalUpdate
        fields = [
            'category',
            'title',
            'description',
            'location',
            'contact_name',
            'contact_phone',
            'event_datetime',
            'valid_until',
        ]
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Example: Bus delay near Belthangady'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ujire, Dharmasthala Road, SDM area...'}),
            'contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10-digit mobile number'}),
            'event_datetime': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'valid_until': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean_contact_phone(self):
        phone = self.cleaned_data.get('contact_phone', '').strip()
        if phone and (not phone.isdigit() or len(phone) not in (10, 11, 12)):
            raise forms.ValidationError('Enter a valid phone number.')
        return phone
