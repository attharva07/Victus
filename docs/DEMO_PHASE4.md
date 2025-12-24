# Victus Phase 4.0 Desktop Demo (Tray UI)

This demo introduces a minimal Windows tray application that provides a compact popup for text-only interactions with Victus. The UI routes every request through `VictusApp.run_request` and never bypasses the policy or executor.

## Prerequisites

- Python 3.11+
- Windows host (global hotkey uses the Win32 API)
- Dependencies:

```bash
pip install -r requirements.txt
```

PySide6 is required for the Qt UI; installing on non-Windows platforms is supported for development, but the global hotkey is only registered on Windows.

## Run the tray application

From the repo root:

```bash
python -m victus.ui.tray_app
```

The app runs quietly in the system tray. Use the tray menu or the hotkey to open the popup.

## Controls

- **Win + Alt + V**: toggle popup visibility
- **Esc**: hide popup
- **Enter**: send the message
- **Shift + Enter**: insert a newline
- **Ctrl + L**: clear the input box
- Tray menu:
  - **Open/Hide**: toggle the popup
  - **Quit Victus**: exit the tray app

## What the popup shows

- Header: `Victus` title, status pill (Ready/Thinking/Denied/Error), and close button
- Transcript: scrollable history with `You:` and `Victus:` entries
- Input: multiline text box with hint line for shortcuts

## Request flow

1. The popup sends user text to `VictusApp.run_request` with a simple OpenAI planning step (`openai.generate_text`).
2. Privacy is configured to allow OpenAI text outbound so policy review succeeds.
3. The returned assistant text is rendered in the transcript. Policy denials or execution errors are surfaced with clear `Denied`/`Error` labels.

## Notes

- Only a single instance of the tray app can run at a time.
- Hotkey registration is skipped on non-Windows platforms to avoid crashes.
- No voice, vision, automation, or background actions are included in this Phase 4.0 demo.
