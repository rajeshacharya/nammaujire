# AI Reel Editor MVP Design

## Goal

Build a Django-based reel editor inside the existing Namma Ujire project. The first release should let a user create a vertical reel project, upload media, import VN/VNFlow QR code metadata when readable, enter a prompt, generate an edit plan, preview the timeline, and request an MP4 render.

## Scope

This MVP is not a full VN clone. It creates the foundation for a VN-like workflow while avoiding proprietary-format assumptions. VN QR codes and `.vnt` files can be stored and analyzed when the QR payload is readable, but exact VN project compatibility is not guaranteed because VN template internals may be private or encrypted.

## Chosen Approach

Use a server-rendered Django app named `editor` with small domain services:

- `PromptPlanner` converts natural language into deterministic edit-plan JSON.
- `RenderService` builds a safe FFmpeg command when FFmpeg is available.
- `QRImport` stores uploaded QR images and decoded text supplied by the browser or user.

This is preferred over immediately building a React/Canvas editor because it fits the current project structure, keeps dependencies small, and provides an end-to-end working workflow quickly. A future iteration can replace the timeline page with a richer React editor without changing the backend project/media/render models.

## Main Components

- `EditorProject`: reel project metadata, prompt, template payload, timeline JSON, render status, output file.
- `EditorAsset`: uploaded video, image, audio, or QR/template file attached to a project.
- Views for project list/detail/create, media upload, QR import, prompt planning, render request, and output download.
- Templates for a compact project dashboard, upload forms, QR import form, prompt editor, timeline preview, and render status.

## Data Flow

1. User creates a project with a title and optional prompt.
2. User uploads media files and optional VN QR image.
3. Browser-side QR detection attempts to fill decoded text; manual paste is supported as fallback.
4. User clicks "Generate edit plan"; backend creates timeline JSON from uploaded assets and prompt keywords.
5. User clicks "Render"; backend validates files and runs FFmpeg only with argument-list APIs, not shell string interpolation.
6. Rendered MP4 is saved under project media and exposed through the project page.

## Error Handling

- Uploaded file types are constrained to video, image, audio, and QR/template categories.
- Prompt planning works even with no media and produces actionable warnings.
- Render requests fail gracefully if FFmpeg is missing or if the project has no usable video/image assets.
- QR import stores unknown payloads without assuming they are VN-compatible.

## Security

- No shell command concatenation for FFmpeg.
- No secrets in model fields, logs, or rendered pages.
- Uploaded filenames use Django storage handling.
- Prompt text is treated as untrusted content and rendered through Django escaping.

## Testing

Tests cover project creation, prompt-plan generation, upload validation, QR metadata storage, render failure behavior when FFmpeg is unavailable, and route accessibility for authenticated users.

## Follow-up Iterations

- Add a React timeline editor with drag, trim, and layer controls.
- Add real AI provider integration behind an environment-gated service.
- Add background jobs for long renders.
- Add beat detection, auto captions, and speech-to-text.
- Add richer template import for readable `.vnt`/VNFlow formats if legally and technically feasible.
