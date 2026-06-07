from django.db import migrations
from django.utils import timezone


def seed_recurring_updates(apps, schema_editor):
    RecurringLocalUpdate = apps.get_model('core', 'RecurringLocalUpdate')
    today = timezone.localdate()

    templates = [
        {
            'title': 'Morning Ujire check-in - {day}',
            'category': 'ANNOUNCEMENT',
            'description': 'Check today for bus delays, rain issues, urgent help, service providers, jobs, marketplace posts, and verified local notices. Villagers can submit updates for admin review.',
            'location': 'Ujire',
            'frequency': 'DAILY',
            'valid_days': 1,
            'starts_on': today,
            'is_pinned': True,
            'is_active': True,
        },
        {
            'title': 'Weekly local jobs and marketplace roundup - {date}',
            'category': 'JOB',
            'description': 'Local shops, households, farms, and students can share verified work needs, helper openings, tuition needs, rentals, and buy/sell posts for the week.',
            'location': 'Ujire and nearby villages',
            'frequency': 'WEEKLY',
            'days_of_week': str(today.weekday()),
            'valid_days': 7,
            'starts_on': today,
            'is_active': True,
        },
        {
            'title': 'Monthly panchayat and public service reminder - {date}',
            'category': 'PANCHAYAT',
            'description': 'Use this monthly reminder for water supply notices, road work, ration updates, public meetings, bill deadlines, and office-service announcements.',
            'location': 'Ujire',
            'frequency': 'MONTHLY',
            'day_of_month': 1,
            'valid_days': 7,
            'starts_on': today,
            'is_active': True,
        },
    ]

    for template in templates:
        RecurringLocalUpdate.objects.get_or_create(
            title=template['title'],
            defaults=template,
        )


def unseed_recurring_updates(apps, schema_editor):
    RecurringLocalUpdate = apps.get_model('core', 'RecurringLocalUpdate')
    RecurringLocalUpdate.objects.filter(title__in=[
        'Morning Ujire check-in - {day}',
        'Weekly local jobs and marketplace roundup - {date}',
        'Monthly panchayat and public service reminder - {date}',
    ]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_recurringlocalupdate_localupdate_generated_for_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_recurring_updates, unseed_recurring_updates),
    ]
