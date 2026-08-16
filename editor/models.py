import uuid
from pathlib import Path

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


def default_timeline():
    return {
        'schema_version': 1,
        'canvas': {'width': 1080, 'height': 1920, 'fps': 30},
        'duration_seconds': 15,
        'tracks': {'visual': [], 'audio': [], 'text': []},
        'warnings': [],
    }


def editor_asset_upload_path(instance, filename):
    extension = Path(filename).suffix.lower()
    safe_stem = slugify(Path(filename).stem)[:48] or 'asset'
    project_id = instance.project_id or 'unassigned'
    return f'editor/assets/{project_id}/{safe_stem}-{uuid.uuid4().hex[:12]}{extension}'


def editor_render_upload_path(instance, filename):
    extension = Path(filename).suffix.lower() or '.mp4'
    return f'editor/renders/{instance.pk}/reel-{uuid.uuid4().hex[:12]}{extension}'


class EditorProject(models.Model):
    class RenderStatus(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        PLANNED = 'PLANNED', 'Plan ready'
        RENDERING = 'RENDERING', 'Rendering'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'

    class TemplateSource(models.TextChoices):
        NONE = 'NONE', 'None'
        VN_QR = 'VN_QR', 'VN QR'
        VN_FILE = 'VN_FILE', 'VN template file'
        MANUAL = 'MANUAL', 'Manual'

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='editor_projects',
    )
    title = models.CharField(max_length=120)
    prompt = models.TextField(blank=True)
    target_duration = models.PositiveSmallIntegerField(
        default=15,
        validators=[MinValueValidator(3), MaxValueValidator(180)],
    )
    canvas_width = models.PositiveSmallIntegerField(default=1080)
    canvas_height = models.PositiveSmallIntegerField(default=1920)
    template_source = models.CharField(
        max_length=20,
        choices=TemplateSource.choices,
        default=TemplateSource.NONE,
    )
    template_payload = models.TextField(blank=True)
    template_notes = models.TextField(blank=True)
    timeline = models.JSONField(default=default_timeline, blank=True)
    render_status = models.CharField(
        max_length=20,
        choices=RenderStatus.choices,
        default=RenderStatus.DRAFT,
    )
    render_message = models.TextField(blank=True)
    output_video = models.FileField(upload_to=editor_render_upload_path, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at', '-created_at']

    def __str__(self):
        return self.title


class EditorAsset(models.Model):
    class Kind(models.TextChoices):
        VIDEO = 'VIDEO', 'Video'
        IMAGE = 'IMAGE', 'Image'
        AUDIO = 'AUDIO', 'Audio'
        QR = 'QR', 'QR code'
        TEMPLATE = 'TEMPLATE', 'Template'
        OTHER = 'OTHER', 'Other'

    project = models.ForeignKey(EditorProject, on_delete=models.CASCADE, related_name='assets')
    kind = models.CharField(max_length=20, choices=Kind.choices)
    file = models.FileField(upload_to=editor_asset_upload_path)
    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=120, blank=True)
    size = models.PositiveBigIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at', 'id']

    def __str__(self):
        return self.original_filename
