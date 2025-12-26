# Victus Phase 4.0 Desktop Demo (Popup UI)

This demo opens the Victus popup UI directly for text-only interactions. The UI routes every request through `VictusApp.run_request` and never bypasses the policy or executor layers.

## Prerequisites
- Python 3.11+
- Desktop environment capable of rendering Qt windows
- Dependencies:
  ```bash
  pip install PySide6
  ```

## Run the popup
From the repo root:
```bash
python run_ui_temp.py
```
The popup window opens immediately with no tray icon or global hotkey.

## Controls
- **Enter**: send the message
- **Shift + Enter**: insert a newline
- **Window close**: exit the popup

## What the popup shows
- Header: `Victus` title, status pill (Ready/Thinking/Denied/Error), and close button
- Transcript: scrollable history with `You:` and `Victus:` entries
- Input: multiline text box with hint line for shortcuts

## Request flow
1. The popup sends user text to `VictusApp.run_request` with a simple OpenAI planning step (`openai.generate_text`).
2. Privacy is configured to allow OpenAI text outbound so policy review succeeds.
3. The returned assistant text is rendered in the transcript. Policy denials or execution errors are surfaced with clear `Denied`/`Error` labels.

## Notes
- Text in/out only: no voice, vision, automation, or background listeners.
- The UI is intended for local desktop use and may not render in headless containers.
