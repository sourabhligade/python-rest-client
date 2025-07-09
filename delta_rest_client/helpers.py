import hmac
import hashlib
import base64
import json

def generate_signature_headers(api_key, api_secret, request_path, method, timestamp, body):
    """
    Generates headers for authenticated API requests to Delta Exchange.
    """
    if body:
        body_str = json.dumps(body, separators=(',', ':'), sort_keys=True)
    else:
        body_str = ''

    message = f'{timestamp}{method.upper()}{request_path}{body_str}'
    signature = hmac.new(
        api_secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    signature_b64 = base64.b64encode(signature).decode()

    headers = {
        'api-key': api_key,
        'timestamp': timestamp,
        'signature': signature_b64,
        'Content-Type': 'application/json'
    }
    return headers
