from django.contrib import admin

from .models import EditorAsset, EditorProject


class EditorAssetInline(admin.TabularInline):
    model = EditorAsset
    extra = 0
    readonly_fields = ['original_filename', 'content_type', 'size', 'created_at']


@admin.register(EditorProject)
class EditorProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'render_status', 'target_duration', 'updated_at']
    list_filter = ['render_status', 'template_source', 'created_at']
    search_fields = ['title', 'prompt', 'owner__username']
    inlines = [EditorAssetInline]


@admin.register(EditorAsset)
class EditorAssetAdmin(admin.ModelAdmin):
    list_display = ['original_filename', 'project', 'kind', 'size', 'created_at']
    list_filter = ['kind', 'created_at']
    search_fields = ['original_filename', 'project__title']
