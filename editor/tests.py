from unittest.mock import patch
from tempfile import TemporaryDirectory

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .forms import EditorAssetUploadForm, QRImportForm
from .models import EditorAsset, EditorProject
from .services import PromptPlanner, RenderService


class TemporaryMediaTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self._media_dir = TemporaryDirectory()
        self._media_override = override_settings(MEDIA_ROOT=self._media_dir.name)
        self._media_override.enable()

    def tearDown(self):
        self._media_override.disable()
        self._media_dir.cleanup()
        super().tearDown()


class EditorPromptPlannerTests(TemporaryMediaTestCase):
    def test_build_plan_uses_prompt_duration_and_effects(self):
        user = User.objects.create_user(username='tester')
        project = EditorProject.objects.create(
            owner=user,
            title='Temple reel',
            prompt='Create a 12 sec cinematic reel with captions and zoom transitions',
        )
        EditorAsset.objects.create(
            project=project,
            kind=EditorAsset.Kind.IMAGE,
            file=SimpleUploadedFile('clip.jpg', b'image-bytes', content_type='image/jpeg'),
            original_filename='clip.jpg',
            content_type='image/jpeg',
            size=11,
        )

        plan = PromptPlanner().build_plan(project)

        self.assertEqual(plan['duration_seconds'], 12)
        self.assertEqual(plan['style'], 'cinematic')
        self.assertIn('captions', plan['effects'])
        self.assertEqual(len(plan['tracks']['visual']), 1)


class EditorFormTests(TemporaryMediaTestCase):
    def test_asset_upload_rejects_unsupported_extension(self):
        form = EditorAssetUploadForm(
            data={'kind': EditorAsset.Kind.VIDEO},
            files={'file': SimpleUploadedFile('bad.exe', b'no', content_type='application/octet-stream')},
        )

        self.assertFalse(form.is_valid())

    def test_qr_import_requires_image_or_decoded_text(self):
        form = QRImportForm(data={})

        self.assertFalse(form.is_valid())


class EditorViewTests(TemporaryMediaTestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username='editor', password='pass')
        self.client.login(username='editor', password='pass')

    def test_create_project(self):
        response = self.client.post(reverse('editor:project_create'), {
            'title': 'My reel',
            'prompt': 'Make a 15 sec upbeat reel',
            'target_duration': 15,
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(EditorProject.objects.filter(owner=self.user, title='My reel').exists())

    def test_qr_import_saves_decoded_text(self):
        project = EditorProject.objects.create(owner=self.user, title='QR reel')
        response = self.client.post(reverse('editor:import_qr', args=[project.pk]), {
            'decoded_text': 'vnflow://template/example',
            'template_notes': 'Imported from phone screenshot',
        })

        project.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(project.template_source, EditorProject.TemplateSource.VN_QR)
        self.assertEqual(project.template_payload, 'vnflow://template/example')

    @patch('editor.services.shutil.which', return_value=None)
    def test_render_fails_cleanly_without_ffmpeg(self, _which):
        project = EditorProject.objects.create(owner=self.user, title='Render reel')

        result = RenderService().render(project)

        project.refresh_from_db()
        self.assertFalse(result.success)
        self.assertEqual(project.render_status, EditorProject.RenderStatus.FAILED)
