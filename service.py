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
        messages = {401: 'The API key was rejected. Check the key.',
                    403: 'Your project does not have access to this request.',
                    429: 'API quota or rate limit reached. Check API billing and limits.'}
        # Do not echo raw remote payloads, which could contain user instructions.
        message = messages.get(response.status_code,
                               f'OpenAI returned HTTP {response.status_code}. Check the model name and project access, then retry.')
        raise ValueError(message)
    if not response.text.startswith('v=0'):
        raise ValueError('Unexpected connection response. Please retry.')
    return response.text
