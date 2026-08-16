import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify

from .forms import EditorAssetUploadForm, EditorProjectForm, PromptPlanForm, QRImportForm
from .models import EditorAsset, EditorProject
from .services import PromptPlanner, RenderService


def _user_project(request, project_id):
    return get_object_or_404(EditorProject, pk=project_id, owner=request.user)


@login_required
def project_list(request):
    projects = EditorProject.objects.filter(owner=request.user)
    return render(request, 'editor/project_list.html', {'projects': projects})


@login_required
def project_create(request):
    if request.method == 'POST':
        form = EditorProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            messages.success(request, 'Reel project created.')
            return redirect('editor:project_detail', project_id=project.pk)
    else:
        form = EditorProjectForm()
    return render(request, 'editor/project_form.html', {'form': form})


@login_required
def project_detail(request, project_id):
    project = _user_project(request, project_id)
    timeline = project.timeline or {}
    visual_clips = timeline.get('tracks', {}).get('visual', [])
    audio_clips = timeline.get('tracks', {}).get('audio', [])
    text_clips = timeline.get('tracks', {}).get('text', [])
    return render(request, 'editor/project_detail.html', {
        'project': project,
        'assets': project.assets.all(),
        'prompt_form': PromptPlanForm(instance=project),
        'visual_clips': visual_clips,
        'audio_clips': audio_clips,
        'text_clips': text_clips,
        'timeline_json': json.dumps(timeline, indent=2),
    })


@login_required
def upload_asset(request, project_id):
    project = _user_project(request, project_id)
    if request.method == 'POST':
        form = EditorAssetUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data['file']
            EditorAsset.objects.create(
                project=project,
                kind=form.cleaned_data['kind'],
                file=uploaded_file,
                original_filename=uploaded_file.name,
                content_type=getattr(uploaded_file, 'content_type', ''),
                size=uploaded_file.size,
            )
            messages.success(request, 'Asset uploaded.')
            return redirect('editor:project_detail', project_id=project.pk)
    else:
        form = EditorAssetUploadForm()
    return render(request, 'editor/upload_asset.html', {'project': project, 'form': form})


@login_required
def import_qr(request, project_id):
    project = _user_project(request, project_id)
    if request.method == 'POST':
        form = QRImportForm(request.POST, request.FILES)
        if form.is_valid():
            qr_image = form.cleaned_data.get('qr_image')
            decoded_text = form.cleaned_data.get('decoded_text', '').strip()
            notes = form.cleaned_data.get('template_notes', '').strip()
            if qr_image:
                EditorAsset.objects.create(
                    project=project,
                    kind=EditorAsset.Kind.QR,
                    file=qr_image,
                    original_filename=qr_image.name,
                    content_type=getattr(qr_image, 'content_type', ''),
                    size=qr_image.size,
                    metadata={'decoded_text_present': bool(decoded_text)},
                )
            project.template_source = EditorProject.TemplateSource.VN_QR
            project.template_payload = decoded_text
            project.template_notes = notes
            project.save(update_fields=['template_source', 'template_payload', 'template_notes', 'updated_at'])
            messages.success(request, 'VN QR/template reference saved.')
            return redirect('editor:project_detail', project_id=project.pk)
    else:
        form = QRImportForm()
    return render(request, 'editor/import_qr.html', {'project': project, 'form': form})


@login_required
def generate_plan(request, project_id):
    project = _user_project(request, project_id)
    if request.method != 'POST':
        return redirect('editor:project_detail', project_id=project.pk)

    form = PromptPlanForm(request.POST, instance=project)
    if form.is_valid():
        project = form.save(commit=False)
        project.timeline = PromptPlanner().build_plan(project)
        project.render_status = EditorProject.RenderStatus.PLANNED
        project.render_message = 'Edit plan generated.'
        project.save(update_fields=['prompt', 'target_duration', 'timeline', 'render_status', 'render_message', 'updated_at'])
        messages.success(request, 'Edit plan generated.')
    else:
        messages.error(request, 'Fix the prompt settings and try again.')
    return redirect('editor:project_detail', project_id=project.pk)


@login_required
def render_project(request, project_id):
    project = _user_project(request, project_id)
    if request.method != 'POST':
        return redirect('editor:project_detail', project_id=project.pk)
    if not project.timeline or not project.timeline.get('tracks'):
        project.timeline = PromptPlanner().build_plan(project)
        project.save(update_fields=['timeline', 'updated_at'])
    result = RenderService().render(project)
    if result.success:
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect('editor:project_detail', project_id=project.pk)


@login_required
def download_output(request, project_id):
    project = _user_project(request, project_id)
    if not project.output_video:
        raise Http404('No rendered video is available.')
    filename = f'{slugify(project.title) or "reel"}.mp4'
    return FileResponse(project.output_video.open('rb'), as_attachment=True, filename=filename)
