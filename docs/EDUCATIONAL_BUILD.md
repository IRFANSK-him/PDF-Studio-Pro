# PDF Studio Pro — Educational Edition

## Scope
Personal learning and testing. This is not a production-certified PDF editor.

## Windows build
1. Open GitHub Actions and select **Windows release candidate**.
2. Select **Run workflow** and choose `development/phase-6-online-licensing`.
3. After the workflow passes, download **PDF-Studio-Pro-Educational-Installer** or **PDF-Studio-Pro-Release-Candidate** from its artifacts.
4. Run the installer on Windows 10/11.

The build workflow runs unit tests first. A green build does not prove every GUI interaction works.

## Online-only activation
The desktop requires `PDF_STUDIO_LICENSE_URL` to point to your own HTTPS license service. It cannot activate without a configured, reachable service. See `docs/ONLINE_LICENSING.md` for the server configuration. Issue keys through the authenticated server admin endpoint. A license binds to one device; reset-device is an administrator-only educational operation.

## Included tools
PDF viewer, navigation, zoom, page thumbnails, merge/split/extract/rotate/delete/reorder, page-order undo/redo, text search, insert text, highlight, redaction, password encryption, PNG export, watermark, image insertion, metadata editing, images-to-PDF, compression, crop.

## Known limitations
- No OCR or true editing of existing PDF text.
- No digital signature signing UI.
- Opening encrypted input PDFs is not supported.
- Compression may not reduce every file.
- License verification is synchronous and requires connectivity.
- Admin API uses an educational SQLite single-process implementation.
- Windows installer is unsigned and may display SmartScreen warnings.
- No completed Windows build or release is claimed until the GitHub Actions workflow passes.
