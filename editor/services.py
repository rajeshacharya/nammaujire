import logging
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from .models import EditorAsset, EditorProject

logger = logging.getLogger(__name__)


VISUAL_KINDS = {EditorAsset.Kind.VIDEO, EditorAsset.Kind.IMAGE}
AUDIO_KINDS = {EditorAsset.Kind.AUDIO}


class PromptPlanner:
    STYLE_KEYWORDS = {
        'cinematic': ['cinematic', 'film', 'movie', 'dramatic'],
        'upbeat': ['upbeat', 'energetic', 'viral', 'trending', 'fast'],
        'devotional': ['temple', 'devotional', 'pooja', 'spiritual'],
        'birthday': ['birthday', 'anniversary', 'celebration'],
        'travel': ['travel', 'trip', 'nature', 'place', 'tour'],
        'minimal': ['clean', 'simple', 'minimal'],
    }

    EFFECT_KEYWORDS = {
        'captions': ['caption', 'subtitle', 'text'],
        'beat_sync': ['beat', 'music sync', 'sync'],
        'zoom': ['zoom', 'punch in', 'ken burns'],
        'speed_ramp': ['speed', 'slow motion', 'slow-mo', 'fast cut'],
        'warm_grade': ['warm', 'golden', 'sunset'],
        'cool_grade': ['cool', 'blue', 'moody'],
    }

    def build_plan(self, project):
        prompt = project.prompt.strip()
        normalized_prompt = prompt.lower()
        duration = self._duration_from_prompt(normalized_prompt) or project.target_duration
        visual_assets = list(project.assets.filter(kind__in=VISUAL_KINDS))
        audio_assets = list(project.assets.filter(kind__in=AUDIO_KINDS))
        style = self._style(normalized_prompt)
        effects = self._effects(normalized_prompt)
        visual_track = self._visual_track(visual_assets, duration, effects)
        audio_track = self._audio_track(audio_assets, duration)
        text_track = self._text_track(project, prompt, duration, effects)
        warnings = []

        if not visual_assets:
            warnings.append('Add at least one video or image before rendering.')
        if project.template_payload:
            warnings.append('VN QR/template data is attached as reference metadata; exact VN compatibility is not guaranteed.')
        if not prompt:
            warnings.append('Prompt is empty, so a neutral vertical reel plan was generated.')

        return {
            'schema_version': 1,
            'canvas': {
                'width': project.canvas_width,
                'height': project.canvas_height,
                'fps': 30,
                'aspect_ratio': '9:16',
            },
            'duration_seconds': duration,
            'style': style,
            'effects': effects,
            'prompt': prompt,
            'template': {
                'source': project.template_source,
                'has_payload': bool(project.template_payload),
                'notes': project.template_notes,
            },
            'tracks': {
                'visual': visual_track,
                'audio': audio_track,
                'text': text_track,
            },
            'warnings': warnings,
            'generated_at': timezone.now().isoformat(),
        }

    def _duration_from_prompt(self, prompt):
        match = re.search(r'\b(\d{1,3})\s*(s|sec|secs|second|seconds)\b', prompt)
        if not match:
            return None
        return max(3, min(180, int(match.group(1))))

    def _style(self, prompt):
        for style, keywords in self.STYLE_KEYWORDS.items():
            if any(keyword in prompt for keyword in keywords):
                return style
        return 'reel'

    def _effects(self, prompt):
        effects = []
        for effect, keywords in self.EFFECT_KEYWORDS.items():
            if any(keyword in prompt for keyword in keywords):
                effects.append(effect)
        if 'zoom' not in effects:
            effects.append('subtle_zoom')
        if 'captions' not in effects and prompt:
            effects.append('title_card')
        return effects

    def _visual_track(self, assets, duration, effects):
        if not assets:
            return []
        clip_duration = round(duration / len(assets), 2)
        cursor = 0
        clips = []
        for index, asset in enumerate(assets):
            end = duration if index == len(assets) - 1 else round(cursor + clip_duration, 2)
            clips.append({
                'asset_id': asset.pk,
                'filename': asset.original_filename,
                'kind': asset.kind,
                'start': cursor,
                'end': end,
                'fit': 'crop_to_9_16',
                'effects': [effect for effect in effects if effect in {'subtle_zoom', 'zoom', 'speed_ramp'}],
                'transition_out': 'crossfade' if index < len(assets) - 1 else 'none',
            })
            cursor = end
        return clips

    def _audio_track(self, assets, duration):
        if not assets:
            return []
        first_asset = assets[0]
        return [{
            'asset_id': first_asset.pk,
            'filename': first_asset.original_filename,
            'start': 0,
            'end': duration,
            'duck_original_audio': True,
        }]

    def _text_track(self, project, prompt, duration, effects):
        text_layers = [{
            'text': project.title,
            'start': 0,
            'end': min(3, duration),
            'position': 'center',
            'style': 'bold_title',
        }]
        if 'captions' in effects and prompt:
            text_layers.append({
                'text': prompt[:120],
                'start': 1,
                'end': duration,
                'position': 'bottom',
                'style': 'caption',
            })
        return text_layers


@dataclass
class RenderResult:
    success: bool
    message: str


class RenderService:
    def render(self, project):
        ffmpeg_path = shutil.which('ffmpeg')
        if not ffmpeg_path:
            return self._fail(project, 'FFmpeg is not installed or not available on PATH.')

        visual_asset = project.assets.filter(kind__in=VISUAL_KINDS).first()
        if not visual_asset:
            return self._fail(project, 'Add at least one video or image before rendering.')

        output_dir = Path(settings.MEDIA_ROOT) / 'editor' / 'renders' / str(project.pk)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f'reel-{timezone.now().strftime("%Y%m%d%H%M%S")}.mp4'
        duration = int(project.timeline.get('duration_seconds') or project.target_duration)
        input_path = Path(visual_asset.file.path)

        if visual_asset.kind == EditorAsset.Kind.IMAGE:
            args = [
                ffmpeg_path,
                '-y',
                '-loop',
                '1',
                '-t',
                str(duration),
                '-i',
                str(input_path),
                '-vf',
                'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,format=yuv420p',
                '-r',
                '30',
                '-pix_fmt',
                'yuv420p',
                str(output_path),
            ]
        else:
            args = [
                ffmpeg_path,
                '-y',
                '-i',
                str(input_path),
                '-t',
                str(duration),
                '-vf',
                'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,format=yuv420p',
                '-an',
                '-r',
                '30',
                '-pix_fmt',
                'yuv420p',
                str(output_path),
            ]

        project.render_status = EditorProject.RenderStatus.RENDERING
        project.render_message = 'Rendering started.'
        project.save(update_fields=['render_status', 'render_message', 'updated_at'])

        logger.info('editor_render_started', extra={'project_id': project.pk, 'asset_id': visual_asset.pk})
        try:
            completed = subprocess.run(args, capture_output=True, text=True, timeout=600, check=False)
        except subprocess.TimeoutExpired:
            return self._fail(project, 'Render timed out after 10 minutes.')
        except OSError as exc:
            logger.warning('editor_render_os_error', extra={'project_id': project.pk, 'error': str(exc)})
            return self._fail(project, 'Render failed while starting FFmpeg.')

        if completed.returncode != 0:
            logger.warning(
                'editor_render_failed',
                extra={'project_id': project.pk, 'returncode': completed.returncode},
            )
            return self._fail(project, self._safe_ffmpeg_error(completed.stderr))

        project.output_video.name = output_path.relative_to(settings.MEDIA_ROOT).as_posix()
        project.render_status = EditorProject.RenderStatus.COMPLETED
        project.render_message = 'Render completed. MVP renderer used the first visual asset.'
        project.save(update_fields=['output_video', 'render_status', 'render_message', 'updated_at'])
        logger.info('editor_render_completed', extra={'project_id': project.pk})
        return RenderResult(True, project.render_message)

    def _fail(self, project, message):
        project.render_status = EditorProject.RenderStatus.FAILED
        project.render_message = message
        project.save(update_fields=['render_status', 'render_message', 'updated_at'])
        return RenderResult(False, message)

    def _safe_ffmpeg_error(self, stderr):
        if not stderr:
            return 'FFmpeg render failed.'
        lines = [line.strip() for line in stderr.splitlines() if line.strip()]
        return lines[-1][:500] if lines else 'FFmpeg render failed.'
