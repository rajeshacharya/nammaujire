from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from core.models import LocalUpdate, RecurringLocalUpdate


class Command(BaseCommand):
    help = 'Generate published LocalUpdate rows from active recurring update rules.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            help='Target date in YYYY-MM-DD format. Defaults to today in the project timezone.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be generated without creating updates.',
        )

    def handle(self, *args, **options):
        target_date = self._target_date(options.get('date'))
        dry_run = options['dry_run']
        created_count = 0
        skipped_count = 0

        for template in RecurringLocalUpdate.objects.filter(is_active=True):
            if not template.should_generate_for(target_date):
                skipped_count += 1
                continue

            defaults = template.build_update_defaults(target_date)

            if dry_run:
                created_count += 1
                self.stdout.write(f'Would generate: {defaults["title"]}')
                continue

            _, created = LocalUpdate.objects.get_or_create(
                generated_from=template,
                generated_for=target_date,
                defaults=defaults,
            )

            if created:
                template.last_generated_on = target_date
                template.save(update_fields=['last_generated_on'])
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Generated: {defaults["title"]}'))
            else:
                skipped_count += 1

        summary = f'{created_count} generated, {skipped_count} skipped for {target_date}.'
        if dry_run:
            summary = f'Dry run: {summary}'
        self.stdout.write(summary)

    def _target_date(self, raw_date):
        if not raw_date:
            return timezone.localdate()

        try:
            return datetime.strptime(raw_date, '%Y-%m-%d').date()
        except ValueError as exc:
            raise CommandError('Use --date in YYYY-MM-DD format.') from exc
