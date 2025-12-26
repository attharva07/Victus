# Phase 4 Temporary Popup Demo (Text Only)

A simple developer harness for Phase 4 that launches the Victus popup UI directly. It is text-only and intended for quick local testing.

## Install dependencies
```bash
pip install PySide6
```

## Run
```bash
python run_ui_temp.py
```

## Controls
- **Enter**: submit text
- **Shift + Enter**: insert newline
- **Window close**: exit the popup

## Notes
- UI opens immediately; there is no tray icon or global hotkey.
- All requests flow through `VictusApp.run_request` (no direct plugin calls).
- Text in/out only (no voice, TTS, screenshots, or vision).
- The popup is intended for local desktop use and may not render in headless containers.
