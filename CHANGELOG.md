# TravelTalk v1.1

- Full-width responsive layout, smaller header, side-by-side voice controls and transcript.
- Separate nonfatal speaker notices from connection failures.
- Add visible WebRTC connection diagnostics and better quota/model/authentication errors.
- Add explicit API credential/model access check.
- Add HTTPS chat fallback with separate history, JSON export and reset.
- Add recorded voice transcription with editable text before sending.
- Release microphone and connection resources on page exit.

Validation: Python compilation, JavaScript syntax, Streamlit smoke checks, mocked API success/error, fallback chat/reset and transcription checks passed. Live voice still requires user API credentials and browser permissions.

If everything appears tiny, reset browser zoom with Ctrl+0 (Windows).