from django.db import models
from django.conf import settings
from django.utils import timezone
import datetime

class OTPVerification(models.Model):
    phone_number = models.CharField(max_length=15, unique=True)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        # OTP is valid for 5 minutes
        expiration_time = self.created_at + datetime.timedelta(minutes=5)
        return timezone.now() <= expiration_time

    def __str__(self):
        return f"{self.phone_number} - {self.otp}"


class LocalUpdate(models.Model):
    class Category(models.TextChoices):
        ANNOUNCEMENT = 'ANNOUNCEMENT', 'Local announcement'
        BUS = 'BUS', 'Bus & transport'
        TEMPLE = 'TEMPLE', 'Temple & festival'
        HEALTH = 'HEALTH', 'Health camp'
        FARMER = 'FARMER', 'Farmer update'
        SCHOOL = 'SCHOOL', 'School & college'
        PANCHAYAT = 'PANCHAYAT', 'Panchayat notice'
        JOB = 'JOB', 'Local job'
        MARKET = 'MARKET', 'Buy & sell'
        WEATHER = 'WEATHER', 'Rain & weather'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending review'
        PUBLISHED = 'PUBLISHED', 'Published'
        REJECTED = 'REJECTED', 'Rejected'

    CATEGORY_ICONS = {
        Category.ANNOUNCEMENT: 'fa-solid fa-bullhorn',
        Category.BUS: 'fa-solid fa-bus',
        Category.TEMPLE: 'fa-solid fa-gopuram',
        Category.HEALTH: 'fa-solid fa-kit-medical',
        Category.FARMER: 'fa-solid fa-seedling',
        Category.SCHOOL: 'fa-solid fa-graduation-cap',
        Category.PANCHAYAT: 'fa-solid fa-building-columns',
        Category.JOB: 'fa-solid fa-briefcase',
        Category.MARKET: 'fa-solid fa-store',
        Category.WEATHER: 'fa-solid fa-cloud-rain',
    }

    title = models.CharField(max_length=160)
    category = models.CharField(max_length=20, choices=Category.choices)
    description = models.TextField()
    location = models.CharField(max_length=120, blank=True)
    contact_name = models.CharField(max_length=80, blank=True)
    contact_phone = models.CharField(max_length=15, blank=True)
    event_datetime = models.DateTimeField(blank=True, null=True)
    valid_until = models.DateField(blank=True, null=True)
    is_urgent = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='submitted_local_updates',
    )
    generated_from = models.ForeignKey(
        'RecurringLocalUpdate',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='generated_updates',
    )
    generated_for = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_urgent', '-is_pinned', 'event_datetime', '-created_at']

    @classmethod
    def published(cls):
        today = timezone.localdate()
        return cls.objects.filter(status=cls.Status.PUBLISHED).filter(
            models.Q(valid_until__isnull=True) | models.Q(valid_until__gte=today)
        )

    @classmethod
    def category_options(cls):
        return [
            {
                'value': value,
                'label': label,
                'icon': cls.CATEGORY_ICONS.get(value, 'fa-solid fa-circle-info'),
            }
            for value, label in cls.Category.choices
        ]

    @property
    def icon_class(self):
        return self.CATEGORY_ICONS.get(self.category, 'fa-solid fa-circle-info')

    def __str__(self):
        return self.title


class RecurringLocalUpdate(models.Model):
    class Frequency(models.TextChoices):
        DAILY = 'DAILY', 'Daily'
        WEEKLY = 'WEEKLY', 'Weekly'
        MONTHLY = 'MONTHLY', 'Monthly'

    title = models.CharField(max_length=160)
    category = models.CharField(max_length=20, choices=LocalUpdate.Category.choices)
    description = models.TextField()
    location = models.CharField(max_length=120, blank=True)
    contact_name = models.CharField(max_length=80, blank=True)
    contact_phone = models.CharField(max_length=15, blank=True)
    frequency = models.CharField(max_length=20, choices=Frequency.choices, default=Frequency.DAILY)
    days_of_week = models.CharField(
        max_length=20,
        blank=True,
        help_text='For weekly rules: comma-separated weekdays, Monday=0 ... Sunday=6.',
    )
    day_of_month = models.PositiveSmallIntegerField(blank=True, null=True)
    publish_time = models.TimeField(default=datetime.time(hour=6, minute=0))
    valid_days = models.PositiveSmallIntegerField(default=1)
    starts_on = models.DateField(default=timezone.localdate)
    ends_on = models.DateField(blank=True, null=True)
    is_urgent = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    last_generated_on = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'title']

    def _weekday_values(self):
        values = set()
        for raw_value in self.days_of_week.split(','):
            raw_value = raw_value.strip()
            if raw_value.isdigit():
                values.add(int(raw_value))
        return values

    def should_generate_for(self, target_date):
        if not self.is_active:
            return False
        if target_date < self.starts_on:
            return False
        if self.ends_on and target_date > self.ends_on:
            return False
        if self.last_generated_on == target_date:
            return False

        if self.frequency == self.Frequency.DAILY:
            return True
        if self.frequency == self.Frequency.WEEKLY:
            return target_date.weekday() in self._weekday_values()
        if self.frequency == self.Frequency.MONTHLY:
            return self.day_of_month == target_date.day
        return False

    def _render_text(self, value, target_date):
        context = {
            'date': target_date.strftime('%d %b %Y'),
            'day': target_date.strftime('%A'),
        }
        try:
            return value.format(**context)
        except (KeyError, ValueError):
            return value

    def build_update_defaults(self, target_date):
        event_datetime = timezone.make_aware(datetime.datetime.combine(target_date, self.publish_time))
        valid_until = target_date + datetime.timedelta(days=max(self.valid_days - 1, 0))
        return {
            'title': self._render_text(self.title, target_date),
            'category': self.category,
            'description': self._render_text(self.description, target_date),
            'location': self.location,
            'contact_name': self.contact_name,
            'contact_phone': self.contact_phone,
            'event_datetime': event_datetime,
            'valid_until': valid_until,
            'is_urgent': self.is_urgent,
            'is_pinned': self.is_pinned,
            'status': LocalUpdate.Status.PUBLISHED,
        }

    def __str__(self):
        return self.title


class EmergencyContact(models.Model):
    class Category(models.TextChoices):
        HEALTH = 'HEALTH', 'Health'
        POLICE = 'POLICE', 'Police'
        FIRE = 'FIRE', 'Fire'
        PANCHAYAT = 'PANCHAYAT', 'Panchayat'
        TRANSPORT = 'TRANSPORT', 'Transport'
        WOMEN_CHILD = 'WOMEN_CHILD', 'Women & child help'
        DISASTER = 'DISASTER', 'Disaster response'

    CATEGORY_ICONS = {
        Category.HEALTH: 'fa-solid fa-truck-medical',
        Category.POLICE: 'fa-solid fa-shield-halved',
        Category.FIRE: 'fa-solid fa-fire-extinguisher',
        Category.PANCHAYAT: 'fa-solid fa-building-columns',
        Category.TRANSPORT: 'fa-solid fa-taxi',
        Category.WOMEN_CHILD: 'fa-solid fa-hands-holding-child',
        Category.DISASTER: 'fa-solid fa-triangle-exclamation',
    }

    name = models.CharField(max_length=120)
    category = models.CharField(max_length=20, choices=Category.choices)
    phone = models.CharField(max_length=15)
    secondary_phone = models.CharField(max_length=15, blank=True)
    location = models.CharField(max_length=120, blank=True)
    notes = models.CharField(max_length=220, blank=True)
    available_24x7 = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'name']

    @property
    def icon_class(self):
        return self.CATEGORY_ICONS.get(self.category, 'fa-solid fa-phone')

    def __str__(self):
        return self.name
