from datetime import timedelta

from django.db import migrations
from django.utils import timezone


def seed_daily_hub(apps, schema_editor):
    EmergencyContact = apps.get_model('core', 'EmergencyContact')
    LocalUpdate = apps.get_model('core', 'LocalUpdate')

    contacts = [
        {
            'name': 'All India Emergency',
            'category': 'DISASTER',
            'phone': '112',
            'notes': 'Police, fire, medical help',
            'available_24x7': True,
            'sort_order': 1,
        },
        {
            'name': 'Ambulance',
            'category': 'HEALTH',
            'phone': '108',
            'notes': 'Emergency medical response',
            'available_24x7': True,
            'sort_order': 2,
        },
        {
            'name': 'Fire Emergency',
            'category': 'FIRE',
            'phone': '101',
            'notes': 'Fire and rescue',
            'available_24x7': True,
            'sort_order': 3,
        },
        {
            'name': 'Women Helpline',
            'category': 'WOMEN_CHILD',
            'phone': '1091',
            'notes': 'Women safety support',
            'available_24x7': True,
            'sort_order': 4,
        },
        {
            'name': 'Child Helpline',
            'category': 'WOMEN_CHILD',
            'phone': '1098',
            'notes': 'Child protection support',
            'available_24x7': True,
            'sort_order': 5,
        },
    ]

    for contact in contacts:
        EmergencyContact.objects.get_or_create(
            phone=contact['phone'],
            defaults=contact,
        )

    today = timezone.localdate()
    update_defaults = [
        {
            'title': 'Daily Ujire board is open for verified local updates',
            'category': 'ANNOUNCEMENT',
            'description': 'Admins can publish useful town updates here: panchayat notices, road work, health camps, school alerts, temple events, jobs, marketplace posts, and transport changes.',
            'location': 'Ujire',
            'valid_until': today + timedelta(days=30),
            'is_pinned': True,
            'status': 'PUBLISHED',
        },
        {
            'title': 'Tap emergency numbers to call quickly',
            'category': 'HEALTH',
            'description': 'Emergency contacts are available from the Daily Ujire page. Add local hospital, clinic, police, ambulance, and panchayat contacts from admin for faster village-level help.',
            'location': 'Ujire',
            'valid_until': today + timedelta(days=30),
            'is_urgent': True,
            'is_pinned': True,
            'status': 'PUBLISHED',
        },
        {
            'title': 'Local shops and households can post jobs or work needs',
            'category': 'JOB',
            'description': 'Use this space for verified daily wage work, shop helper openings, delivery help, farm work, tuition needs, and other local opportunities.',
            'location': 'Ujire and nearby villages',
            'valid_until': today + timedelta(days=30),
            'status': 'PUBLISHED',
        },
        {
            'title': 'Bus delays and road updates can be shared by villagers',
            'category': 'BUS',
            'description': 'When a route is delayed, blocked, or changed, a logged-in user can submit an update. Admin review keeps the board trustworthy.',
            'location': 'Ujire bus stand',
            'valid_until': today + timedelta(days=30),
            'status': 'PUBLISHED',
        },
    ]

    for update in update_defaults:
        LocalUpdate.objects.get_or_create(
            title=update['title'],
            defaults=update,
        )


def unseed_daily_hub(apps, schema_editor):
    EmergencyContact = apps.get_model('core', 'EmergencyContact')
    LocalUpdate = apps.get_model('core', 'LocalUpdate')

    EmergencyContact.objects.filter(phone__in=['112', '108', '101', '1091', '1098']).delete()
    LocalUpdate.objects.filter(title__in=[
        'Daily Ujire board is open for verified local updates',
        'Tap emergency numbers to call quickly',
        'Local shops and households can post jobs or work needs',
        'Bus delays and road updates can be shared by villagers',
    ]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_emergencycontact_localupdate'),
    ]

    operations = [
        migrations.RunPython(seed_daily_hub, unseed_daily_hub),
    ]
