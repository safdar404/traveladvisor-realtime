"""Server-only Realtime handshake. Never forward the API key to the browser."""
import json
import requests


def session_config(model, voice, language, style, preferences, extra, tokens):
    instructions = (
        'You are Travel Advisor, a friendly conversational travel assistant. '
        'Give useful destination recommendations and practical itineraries. '
        'Ask for missing dates, origin, budget and preferences before making detailed plans. '
        'Never claim to have checked live prices, availability, visa rules or made bookings. '
        'Explain that current travel requirements and prices need verification. '
        'Do not request passport numbers or payment credentials. '
        f'Reply in {language}. Use a {style} style. '
        f'Traveler preferences: {preferences or "Ask the traveler."}\n'
        f'Additional user guidance: {extra}'
    )
    return {'type': 'realtime', 'model': model, 'instructions': instructions,
            'output_modalities': ['audio'], 'max_output_tokens': tokens,
            'audio': {'input': {'transcription': {'model': 'gpt-4o-mini-transcribe'},
                                'turn_detection': {'type': 'semantic_vad',
                                                   'interrupt_response': True,
                                                   'create_response': True}},
                      'output': {'voice': voice}}}


def create_answer(api_key, offer, config):
    if not api_key.strip():
        raise ValueError('Enter your OpenAI API key in the sidebar first.')
    if not isinstance(offer, str) or not offer.startswith('v=0') or len(offer) > 100_000:
        raise ValueError('Invalid WebRTC offer. End the session and connect again.')
    try:
        response = requests.post(
            'https://api.openai.com/v1/realtime/calls',
            headers={'Authorization': f'Bearer {api_key.strip()}'},
            files={'sdp': (None, offer), 'session': (None, json.dumps(config))},
            timeout=(10, 45),
        )
    except requests.Timeout as exc:
        raise ValueError('Connection timed out. Check your connection and try again.') from exc
    except requests.RequestException as exc:
        raise ValueError('Could not reach OpenAI. Check internet access and try again.') from exc
    if not response.ok:
        raise ValueError(api_error(response))
    if not response.text.startswith('v=0'):
        raise ValueError('Unexpected connection response. Please retry.')
    return response.text


def api_error(response):
    """Expose actionable status/codes, never arbitrary remote error messages."""
    code = ''
    try:
        code = str(response.json().get('error', {}).get('code', ''))
    except (ValueError, AttributeError):
        pass
    safe_codes = {'insufficient_quota', 'rate_limit_exceeded', 'model_not_found',
                  'invalid_api_key', 'model_not_supported', 'invalid_request_error'}
    hint = {401: 'API key rejected. Replace it with a valid OpenAI API key.',
            403: 'Project permission denied. Check model access and regional availability.',
            429: 'API quota or rate limit reached. Check API billing and limits.',
            400: 'Request rejected. Check the model name and configuration.',
            404: 'Requested model or endpoint unavailable. Check model access.'}.get(
                response.status_code, 'The API request failed. Try again later.')
    if code == 'insufficient_quota':
        hint = 'API credits or spending quota exhausted. Check your OpenAI API billing; ChatGPT subscription does not supply API credits.'
    return f'HTTP {response.status_code}' + (f' · {code}' if code in safe_codes else '') + ': ' + hint


def verify_access(api_key, model):
    try:
        r = requests.get('https://api.openai.com/v1/models',
                         headers={'Authorization': f'Bearer {api_key.strip()}'}, timeout=(10,20))
    except requests.RequestException as exc:
        raise ValueError('Could not reach OpenAI to check credentials.') from exc
    if not r.ok:
        raise ValueError(api_error(r))
    ids = {item.get('id') for item in r.json().get('data', [])}
    return model in ids


def chat_answer(api_key, messages, instructions, model='gpt-4.1-mini'):
    try:
        r = requests.post('https://api.openai.com/v1/responses',
            headers={'Authorization': f'Bearer {api_key.strip()}'},
            json={'model': model, 'instructions': instructions,
                  'input': messages[-20:], 'max_output_tokens': 1500, 'store': False}, timeout=(10,60))
    except requests.RequestException as exc:
        raise ValueError('Chat request failed or timed out. You can retry your message.') from exc
    if not r.ok:
        raise ValueError(api_error(r))
    data = r.json()
    text = '\n'.join(part.get('text','') for item in data.get('output', [])
                     for part in item.get('content', []) if part.get('type') == 'output_text').strip()
    if not text:
        raise ValueError('No text response was returned. Try a shorter request.')
    if data.get('status') == 'incomplete':
        text += '\n\n[Response reached its output limit. Ask to continue.]'
    return text


def transcribe_recording(api_key, audio):
    if not audio or len(audio) > 10 * 1024 * 1024:
        raise ValueError('Use a non-empty recording below 10 MB.')
    try:
        r = requests.post('https://api.openai.com/v1/audio/transcriptions',
            headers={'Authorization': f'Bearer {api_key.strip()}'},
            files={'file': ('recording.wav', audio, 'audio/wav')},
            data={'model': 'gpt-transcribe'}, timeout=(10,60))
    except requests.RequestException as exc:
        raise ValueError('Recording upload failed or timed out. Try again.') from exc
    if not r.ok:
        raise ValueError(api_error(r))
    text = r.json().get('text', '').strip()
    if not text:
        raise ValueError('No speech recognized. Record a clearer message.')
    return text
