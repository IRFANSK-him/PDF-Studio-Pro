# PDF Studio Pro v1.0 — Release Preview

**Windows PDF editing application | Source preview**

This repository contains the **cumulative three-part PDF Studio Pro v1.0 source candidate**, including a PySide6 editor, PDF document processing, and a FastAPI server for online one-PC lifetime licensing.

> **Release preview, not a production release.** The Windows GUI and installer need final acceptance testing; this repository does not include a compiled `.exe`, a deployed HTTPS licensing server, or issued licenses.

## Modules

- **Part 1:** Document rendering, navigation, search, page thumbnails, drag-and-drop reorder, crop, PNG export, image-to-PDF, shortcuts, page-order history.
- **Part 2:** Text/image insertion, highlights, permanent redaction, watermarks, metadata, PDF compression, password and AES-256 protection.
- **Part 3:** Online lifetime license activation, one-PC binding, signed licenses, license administration, revocation/device reset, portable and installer build scripts.

## Windows local preview

1. Install Windows 10/11 x64 with Python 3.11 or 3.12 x64.
2. Run `scripts\setup_windows.bat` to install dependencies, configure local test licensing, and run tests.
3. Run `scripts\start_local_license_server.bat` in a terminal.
4. Run `scripts\create_local_license.bat` in another terminal. Retain the generated test key.
5. Run `scripts\run_windows.bat` to activate and open the desktop program.

Detailed architecture, feature limitations, build instructions, and security caveats are in [`docs/ORIGINAL_PART3_README.md`](docs/ORIGINAL_PART3_README.md). See [`docs/WINDOWS_RELEASE_CHECKLIST.md`](docs/WINDOWS_RELEASE_CHECKLIST.md) before distribution.

## Testing and builds

Run automated tests with `python -m pytest -q` after installing the requirements. On Windows, `scripts\test_windows.bat` is provided. On Windows, the portable build uses `scripts\build_windows_portable.bat` and the installer uses `scripts\build_windows_installer.bat`, which requires Inno Setup 6. **Public builds require a configured HTTPS license endpoint.**

## Security & distribution notes

Keep `secrets/`, server private signing keys, administrator credentials, and local databases out of Git. The bundled `config/license_client.example.json` is a schema example only. The project uses PyMuPDF; review `LICENSE-NOTE.txt` before redistribution under AGPL or a commercial license.

**Preview project:** PDF Studio Pro v1.0 release preview.
