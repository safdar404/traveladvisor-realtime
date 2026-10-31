from pathlib import Path
import base64
import os
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from service import create_answer, session_config

load_dotenv(override=False)
ROOT = Path(__file__).parent
st.set_page_config(page_title='TravelTalk · Realtime AI', page_icon='🎙️', layout='wide')
voice_panel = components.declare_component('traveltalk_voice', path=str(ROOT / 'frontend'))
st.markdown('''<style>
[data-testid="stAppViewContainer"]{background:radial-gradient(ellipse at top right,#30205255,transparent 55%),#0d1024;color:#f1efff}
[data-testid="stHeader"]{background:#0d1024ee}[data-testid="stSidebar"]{background:#17182e}
.block-container{padding-top:1.8rem;padding-bottom:1rem;max-width:1280px}
h1,h2,h3{color:#f3f0ff}div.stButton>button,div.stDownloadButton>button{background:#33295a;color:#fff;border:1px solid #785cc0;border-radius:12px}
.hero{display:flex;align-items:center;gap:22px;padding:22px;border:1px solid #65528c;border-radius:22px;background:linear-gradient(115deg,#26294d,#342044,#133d4a);margin-bottom:16px}
.hero img{width:110px;height:110px;object-fit:cover;border-radius:23px}.hero h1{font-size:2.1rem;margin:0;line-height:1.1}.hero p{color:#d5d0eb;margin:8px 0}.tag{color:#88e7e5;font-weight:700;font-size:.75rem;letter-spacing:2px}
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
reply=st.session_state.get('handshake_reply', {})
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
st.caption('TravelTalk AI · Built for Muhammad Safdar · Browser audio + OpenAI Realtime · End the session when finished')
