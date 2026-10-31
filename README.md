# 🎙️ TravelTalk AI — Realtime Streamlit Voice Advisor

A browser-based adaptation of your `16-realtime_agents(1).py`. Preserves the Travel Advisor persona, `gpt-realtime`, default `ash` voice, input transcription and semantic voice activity detection with interruptions. The transport changes from the Agents SDK + local sounddevice to the official Realtime WebRTC API, so hosted users speak through their own browsers.

## Run on Windows / VS Code

Extract this entire folder, open a terminal in it, then run:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open http://localhost:8501. Enter your OpenAI API key in the sidebar. No need to activate the virtual environment. No sounddevice, system microphone driver, Node.js or frontend build is needed.

## Use

1. Enter a key in the sidebar (or set OPENAI_API_KEY locally / in Streamlit secrets).
2. Set language, voice, reply length and session time limit.
3. Optionally add origin, destination, budget, dates and interests.
4. Click Start voice and allow microphone access, or choose Text-only.
5. Speak naturally. Semantic VAD automatically detects turns and can interrupt replies.
6. Use typed messages, travel prompt buttons, mute, interrupt, or enable speaker.
7. End session when finished; export transcript JSON before refreshing.

Settings apply to a new connection. End before changing settings. Each connection starts fresh model context. Clear view erases only displayed transcripts; it does not erase the live model's context.

## Streamlit Community Cloud

Upload **all** project files including frontend/index.html, assets/agent.png and .streamlit/config.toml to your own repository. Deploy with app.py as entry point and Python 3.12. Use HTTPS and Chrome/Edge. Users can supply their own key; alternatively add OPENAI_API_KEY through app secrets for a private deployment. Do not expose an owner-funded API key in an unrestricted public deployment. Custom-component microphone access depends on browser/embedding permissions; if denied, open the app directly in a browser tab and inspect site permissions. Text-only avoids microphone requirements but still uses WebRTC and spoken output.

## Docker

```powershell
docker build -t traveltalk-ai .
docker run --rm -p 127.0.0.1:8501:8501 traveltalk-ai
```

Open http://localhost:8501 and enter a key. For remote hosting use HTTPS via your platform's reverse proxy.

## Review findings and fixes

- Original sounddevice accessed the server's hardware, unsuitable for a hosted UI. Browser WebRTC now handles the visitor's microphone and speakers.
- Removed manual PCM queues and per-chunk coroutine scheduling: no unbounded server playback queue or ignored send_audio futures. WebRTC handles audio transport and playout.
- Browser sample rates are negotiated; no assumption that every device supports a 24 kHz sounddevice stream.
- Full API key stays on the Python server; only SDP connection information reaches the frontend.
- Duplicate dotenv calls removed; existing environment values are not overwritten.
- Added explicit session lifecycle, timeout, auto-end, track release, mic permission messages, API error handling and reconnect controls.
- Safe transcript rendering uses textContent. No generated HTML is executed.
- Added captions, JSON export, typed prompts, text-only connection, voice/language settings and traveler preferences.
- Session limit is a browser timer, not a server-enforced billing cap. Tab suspension can delay it. End the session explicitly when finished.

## Privacy and limitations

This app uses AI-generated voice. Audio/text is transmitted to OpenAI. API usage requires a funded API project with Realtime access and is separate from a ChatGPT subscription. Transcript view is kept in browser memory; exported JSON is stored on the user's device. Transcripts can arrive out of order because input transcription is asynchronous. Captions are best-effort and may differ from spoken content. No live price, browsing, visa verification or booking integrations are connected; itinerary advice is generated, not verified inventory. Network/firewall WebRTC restrictions can prevent a call even if the HTTP handshake succeeds.

## Validation

Python compilation, JavaScript syntax, mocked API error/success paths and Streamlit UI smoke checks are run during packaging. A real microphone-to-model call requires the user's API key, billing/access and browser permissions; it is not claimed as verified without that call.

## Official references

- https://developers.openai.com/api/docs/guides/voice-webrtc
- https://developers.openai.com/api/reference/resources/realtime/subresources/calls/methods/create
- https://docs.streamlit.io/develop/concepts/custom-components/components-v1/intro
