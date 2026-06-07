from django.contrib import admin
from django.utils import timezone
from .models import EmergencyContact, LocalUpdate, OTPVerification, RecurringLocalUpdate


@admin.register(LocalUpdate)
class LocalUpdateAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'status', 'is_urgent', 'is_pinned', 'valid_until', 'generated_from', 'created_at')
    list_filter = ('category', 'status', 'is_urgent', 'is_pinned', 'generated_from')
    search_fields = ('title', 'description', 'location', 'contact_name', 'contact_phone')
    date_hierarchy = 'created_at'
    actions = ('publish_updates', 'reject_updates')

    @admin.action(description='Publish selected updates')
    def publish_updates(self, request, queryset):
        queryset.update(status=LocalUpdate.Status.PUBLISHED)

    @admin.action(description='Reject selected updates')
    def reject_updates(self, request, queryset):
        queryset.update(status=LocalUpdate.Status.REJECTED)


@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'phone', 'available_24x7', 'sort_order', 'is_active')
    list_filter = ('category', 'available_24x7', 'is_active')
    search_fields = ('name', 'phone', 'location', 'notes')


@admin.register(RecurringLocalUpdate)
class RecurringLocalUpdateAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'frequency', 'is_active', 'last_generated_on', 'starts_on', 'ends_on')
    list_filter = ('category', 'frequency', 'is_active')
    search_fields = ('title', 'description', 'location')
    actions = ('generate_today',)

    @admin.action(description='Generate selected rules for today')
    def generate_today(self, request, queryset):
        target_date = timezone.localdate()
        created_count = 0
        skipped_count = 0

        for template in queryset:
            if not template.should_generate_for(target_date):
                skipped_count += 1
                continue

            _, created = LocalUpdate.objects.get_or_create(
                generated_from=template,
                generated_for=target_date,
                defaults=template.build_update_defaults(target_date),
            )
            if created:
                template.last_generated_on = target_date
                template.save(update_fields=['last_generated_on'])
                created_count += 1
            else:
                skipped_count += 1

        self.message_user(request, f'Generated {created_count} update(s). Skipped {skipped_count}.')


admin.site.register(OTPVerification)
