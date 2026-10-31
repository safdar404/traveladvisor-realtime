from pathlib import Path
import base64
import os
import json
import hashlib
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from service import create_answer, session_config, verify_access, chat_answer, transcribe_recording

load_dotenv(override=False)
ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title='TravelTalk · Realtime AI', page_icon='🎙️', layout='wide')
frontend_dir = ROOT / 'frontend'
if not (frontend_dir / 'index.html').is_file():
    st.error('🎧 Voice frontend is missing from this deployment.')
    st.info('Upload frontend/index.html into the frontend folder beside app.py in your GitHub repository, then reboot the app.')
    st.code('app.py\nservice.py\nfrontend/\n    index.html\nassets/\n    agent.png\n.streamlit/\n    config.toml')
    st.stop()
voice_panel = components.declare_component('traveltalk_voice', path=str(frontend_dir))
st.markdown('''<style>
[data-testid="stAppViewContainer"]{background:radial-gradient(ellipse at top right,#30205255,transparent 55%),#0d1024;color:#f1efff}
[data-testid="stHeader"]{background:#0d1024ee}[data-testid="stSidebar"]{background:#17182e}
.block-container{padding:1rem 2rem 1rem!important;max-width:100%!important;width:100%!important}
[data-testid="stSidebar"]{min-width:270px;max-width:320px}
[data-testid="stAppViewContainer"] input,[data-testid="stAppViewContainer"] textarea{font-size:15px}
[data-testid="stExpander"]{border-radius:14px;border-color:#4b4268}
@media(min-width:1600px){.block-container{padding-left:3rem!important;padding-right:3rem!important}}
@media(max-width:700px){.block-container{padding:1rem!important}}
h1,h2,h3{color:#f3f0ff}div.stButton>button,div.stDownloadButton>button{background:#33295a;color:#fff;border:1px solid #785cc0;border-radius:12px}
.hero{display:flex;align-items:center;gap:16px;padding:16px;border:1px solid #65528c;border-radius:22px;background:linear-gradient(115deg,#26294d,#342044,#133d4a);margin-bottom:16px}
.hero img{width:78px;height:78px;object-fit:cover;border-radius:23px}.hero h1{font-size:1.8rem;margin:0;line-height:1.1}.hero p{color:#d5d0eb;margin:8px 0}.tag{color:#88e7e5;font-weight:700;font-size:.75rem;letter-spacing:2px}
@media(max-width:600px){.hero{padding:16px;gap:12px}.hero img{width:76px;height:76px}.hero h1{font-size:1.5rem}}
</style>''', unsafe_allow_html=True)
with st.sidebar:
    st.subheader('🔐 Connect your AI')
    try:
        saved = st.secrets.get('OPENAI_API_KEY', '')
    except Exception:
        saved = ''
    entered = st.text_input('OpenAI API key', type='password', help='Used only by the Python server to initialize your call. Never sent to the browser audio component.')
    api_key = entered.strip() or os.getenv('OPENAI_API_KEY', '') or saved
    st.caption('✅ Key supplied' if api_key else '⬅️ Enter a key to enable connection')
    st.caption('API usage is billed separately from a ChatGPT subscription.')
    st.divider()
    st.subheader('🎛️ Conversation settings')
    model = st.text_input('Realtime model', value='gpt-realtime', help='Preserves the model in your original script. Your project must have access.')
    if st.button('🔎 Check API access', disabled=not bool(api_key)):
        try:
            available = verify_access(api_key, model.strip())
            if available:
                st.success('Key accepted; model is listed. A live connection still needs WebRTC access.')
            else:
                st.warning('Key accepted, but this model was not listed. Check the model name and project permissions.')
        except ValueError as exc:
            st.error(str(exc))
    voice = st.selectbox('🗣️ Voice', ['ash', 'alloy', 'ballad', 'coral', 'echo', 'sage', 'shimmer', 'verse', 'marin', 'cedar'])
    language = st.selectbox('🌐 Reply language', ['English', 'Urdu', 'Match the language the traveler uses', 'Arabic', 'Portuguese', 'Spanish'])
    style = st.selectbox('💬 Response style', ['brief, friendly and conversational', 'detailed and practical', 'family-friendly and encouraging'])
    tokens = st.slider('Maximum output tokens per reply', 256, 4096, 1024, 256)
    minutes = st.slider('Auto-end after minutes', 1, 30, 10)
    st.caption('Settings apply on the next connection. End an active call before changing settings.')
image = ROOT / 'assets' / 'agent.png'
image_html = ''
if image.exists():
    image_html = '<img alt="TravelTalk AI headset assistant" src="data:image/png;base64,' + base64.b64encode(image.read_bytes()).decode() + '">'
st.markdown(f'<div class="hero">{image_html}<div><div class="tag">REALTIME · TRAVEL ADVISOR</div><h1>TravelTalk AI 🎙️</h1><p>Your next journey starts with a conversation.</p><small>🎧 Live voice &nbsp; 🌍 Travel ideas &nbsp; 📝 Captions &nbsp; ✨ Natural interruptions</small></div></div>', unsafe_allow_html=True)
with st.expander('🧭 Personalize your advisor', expanded=False):
    c1,c2,c3=st.columns(3)
    origin=c1.text_input('📍 Departing from', placeholder='Lahore, Pakistan')
    destination=c2.text_input('🌍 Destination or region', placeholder='Brazil, Europe, or surprise me')
    budget=c3.text_input('💰 Budget and currency', placeholder='USD 1,500 total')
    c4,c5=st.columns(2)
    dates=c4.text_input('📅 Dates / duration', placeholder='7 days in March')
    travelers=c5.text_input('👨‍👩‍👧‍👦 Travelers and interests', placeholder='Family, nature, halal food')
    extra=st.text_area('✨ Additional instructions', max_chars=3000, placeholder='Accessible transport, relaxed pace, food preferences…')
preferences='; '.join(f'{k}: {v}' for k,v in [('Origin',origin),('Destination',destination),('Budget',budget),('Dates',dates),('Travelers/interests',travelers)] if v)
config=session_config(model.strip() or 'gpt-realtime',voice,language,style,preferences,extra,tokens)
if not api_key:
    st.info('🔑 Add your API key in the sidebar, then choose Start voice or Text-only inside the panel below.')
st.caption('1️⃣ Add key → 2️⃣ Set preferences → 3️⃣ Connect → 4️⃣ Speak or type → 5️⃣ End & export. AI-generated voice; no booking or live search tools are connected.')
mode=st.radio('Conversation mode', ['🎙️ Live voice', '💬 Chat & recorded voice'], horizontal=True, help='End your live session before switching modes. Chat uses HTTPS and does not require a WebRTC connection.')
if mode == '🎙️ Live voice':
    st.caption('Live microphone → Realtime AI → spoken reply. If connection fails, use Chat & recorded voice above.')
reply=st.session_state.get('handshake_reply', {})
if mode == '🎙️ Live voice':
    event=voice_panel(enabled=bool(api_key), reply=reply, minutes=minutes, key='voice_panel', default=None)
    if isinstance(event,dict) and event.get('type')=='offer':
        request_id=event.get('request_id')
        if request_id and request_id != st.session_state.get('handled_offer'):
            st.session_state.handled_offer=request_id
            try:
                with st.spinner('🔗 Connecting your realtime session…'):
                    answer=create_answer(api_key,event.get('sdp'),config)
                st.session_state.handshake_reply={'request_id':request_id,'sdp':answer}
            except ValueError as exc:
                st.session_state.handshake_reply={'request_id':request_id,'error':str(exc)}
            st.rerun()
else:
    st.caption('HTTPS fallback · Type or record a message → AI text reply. This mode has separate history and does not produce realtime audio.')
    chat_model=st.text_input('Chat model', value='gpt-4.1-mini', key='chat_model')
    history=st.session_state.setdefault('chat_history', [])
    a,b=st.columns([1,1])
    if a.button('🧹 New chat'):
        st.session_state.chat_history=[]
        st.session_state.pop('draft_transcript',None)
        st.rerun()
    b.download_button('⬇️ Export chat', data=json.dumps(history,ensure_ascii=False,indent=2),file_name='traveltalk-chat.json',mime='application/json')
    with st.container(height=350):
        if not history:
            st.info('Ask about destinations, budgets, family itineraries or packing.')
        for message in history:
            with st.chat_message(message['role']):
                st.markdown(message['content'])
    with st.expander('🎤 Record a voice message'):
        recording=st.audio_input('Record, then click Transcribe')
        if st.button('📝 Transcribe recording',disabled=not bool(api_key and recording)):
            try:
                with st.spinner('Transcribing…'):
                    st.session_state.draft_transcript=transcribe_recording(api_key,recording.getvalue())
            except ValueError as exc:
                st.error(str(exc))
    with st.form('fallback_chat',clear_on_submit=False):
        prompt=st.text_area('Your message (edit transcribed text before sending)',key='draft_transcript',max_chars=4000)
        submitted=st.form_submit_button('📨 Send to advisor',disabled=not bool(api_key))
    if submitted:
        if not prompt.strip():
            st.warning('Enter or transcribe a message first.')
        else:
            pending=history+[{'role':'user','content':prompt.strip()}]
            try:
                with st.spinner('Planning your answer…'):
                    answer=chat_answer(api_key,pending,config['instructions'],chat_model.strip())
                st.session_state.chat_history=pending+[{'role':'assistant','content':answer}]
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
with st.expander('🛠️ Help & workflow'):
    st.markdown('''- Use **Chrome or Edge**, allow microphone access, and wear headphones to reduce echo.
- On a hosted app, use **HTTPS**. Local development works on `localhost`.
- **Mute mic** disables the microphone track; it does not end the session. Use **End session** to disconnect.
- Speak while the advisor is responding to interrupt naturally, or press **Interrupt**.
- **Text-only** connects without requesting a microphone and still plays spoken answers.
- Captions are best-effort transcriptions. Export them before refreshing the page.
- Transcripts stay in this browser component until cleared/refreshed; audio and text are sent to OpenAI during the session.
- Microphone denied: change browser site permissions. No audio: click **Enable speaker** and check the output device.
- Authentication, quota and model-access errors appear in the voice panel. Stop and reconnect after fixing them.
- Changing the voice or preferences requires a new session. New sessions start with fresh model context.''')
st.caption('TravelTalk AI v1.1 · Built for Muhammad Safdar · Browser audio + OpenAI Realtime · End the session when finished')
