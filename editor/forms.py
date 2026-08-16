from pathlib import Path

from django import forms
from django.conf import settings

from .models import EditorAsset, EditorProject


ALLOWED_EXTENSIONS_BY_KIND = {
    EditorAsset.Kind.VIDEO: {'.mp4', '.mov', '.m4v', '.webm'},
    EditorAsset.Kind.IMAGE: {'.jpg', '.jpeg', '.png', '.webp'},
    EditorAsset.Kind.AUDIO: {'.mp3', '.m4a', '.aac', '.wav', '.ogg'},
    EditorAsset.Kind.QR: {'.jpg', '.jpeg', '.png', '.webp'},
    EditorAsset.Kind.TEMPLATE: {'.vnt', '.zip', '.json'},
}

ALL_ALLOWED_EXTENSIONS = set().union(*ALLOWED_EXTENSIONS_BY_KIND.values())


class EditorProjectForm(forms.ModelForm):
    class Meta:
        model = EditorProject
        fields = ['title', 'prompt', 'target_duration']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'prompt': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'target_duration': forms.NumberInput(attrs={'class': 'form-control', 'min': 3, 'max': 180}),
        }


class PromptPlanForm(forms.ModelForm):
    class Meta:
        model = EditorProject
        fields = ['prompt', 'target_duration']
        widgets = {
            'prompt': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'target_duration': forms.NumberInput(attrs={'class': 'form-control', 'min': 3, 'max': 180}),
        }


class EditorAssetUploadForm(forms.Form):
    file = forms.FileField(widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))
    kind = forms.ChoiceField(
        choices=[choice for choice in EditorAsset.Kind.choices if choice[0] != EditorAsset.Kind.OTHER],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    def clean_file(self):
        uploaded_file = self.cleaned_data['file']
        extension = Path(uploaded_file.name).suffix.lower()
        if extension not in ALL_ALLOWED_EXTENSIONS:
            raise forms.ValidationError('Unsupported file type for the editor.')
        max_size = getattr(settings, 'EDITOR_MAX_UPLOAD_SIZE', 500 * 1024 * 1024)
        if uploaded_file.size > max_size:
            raise forms.ValidationError('File is larger than the configured upload limit.')
        return uploaded_file

    def clean(self):
        cleaned_data = super().clean()
        uploaded_file = cleaned_data.get('file')
        selected_kind = cleaned_data.get('kind')
        if not uploaded_file:
            return cleaned_data

        extension = Path(uploaded_file.name).suffix.lower()
        if selected_kind:
            allowed = ALLOWED_EXTENSIONS_BY_KIND.get(selected_kind, set())
            if extension not in allowed:
                raise forms.ValidationError('The selected asset type does not match the file extension.')
        else:
            cleaned_data['kind'] = infer_asset_kind(uploaded_file.name, getattr(uploaded_file, 'content_type', ''))
        return cleaned_data


class QRImportForm(forms.Form):
    qr_image = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'id': 'id_qr_image'}),
    )
    decoded_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'id': 'id_decoded_text'}),
    )
    template_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
    )

    def clean_qr_image(self):
        uploaded_file = self.cleaned_data.get('qr_image')
        if not uploaded_file:
            return uploaded_file
        extension = Path(uploaded_file.name).suffix.lower()
        if extension not in ALLOWED_EXTENSIONS_BY_KIND[EditorAsset.Kind.QR]:
            raise forms.ValidationError('QR code must be an image file.')
        return uploaded_file

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('qr_image') and not cleaned_data.get('decoded_text'):
            raise forms.ValidationError('Upload a QR image or paste the decoded VN code text.')
        return cleaned_data


def infer_asset_kind(filename, content_type=''):
    extension = Path(filename).suffix.lower()
    for kind, extensions in ALLOWED_EXTENSIONS_BY_KIND.items():
        if extension in extensions:
            if kind == EditorAsset.Kind.QR and 'qr' not in filename.lower():
                return EditorAsset.Kind.IMAGE
            return kind
    if content_type.startswith('video/'):
        return EditorAsset.Kind.VIDEO
    if content_type.startswith('image/'):
        return EditorAsset.Kind.IMAGE
    if content_type.startswith('audio/'):
        return EditorAsset.Kind.AUDIO
    return EditorAsset.Kind.OTHER
