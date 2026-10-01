import logging
import os
from flask import Flask, request, Response
import requests

# Import Keras and WAFBrain specifics
from keras.models import load_model
import waf_brain
from waf_brain.inferring import process_payload

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

JUICE_SHOP_URL = "http://juice-shop:3000"
# WAFBrain ML model outputs a score between 0.0 and 1.0 (typically 0.0 for safe, ~0.5+ for malicious)
BLOCKING_THRESHOLD = 0.5

# Initialize WAFBrain Model
logging.info("Initializing WAFBrain model...")
# WAFBrain stores its default models within its package directory
waf_brain_dir = os.path.dirname(waf_brain.__file__)
model_path = os.path.join(waf_brain_dir, "models", "model_feat-5_botneck-101.h5")
MODEL = load_model(model_path)
logging.info("WAFBrain model loaded.")

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'])
def proxy(path):
    is_malicious = False
    
    # 1. Evaluate query parameters
    for arg, val in request.args.items():
        try:
            result = process_payload(MODEL, arg, [val], False)
            if result and result.get("score", 0) >= BLOCKING_THRESHOLD:
                is_malicious = True
                break
        except Exception as e:
            logging.error(f"Error during WAFBrain prediction on args: {e}")

    # 2. Evaluate body payload if present
    if not is_malicious and request.get_data():
        try:
            body_val = request.get_data().decode('utf-8', errors='ignore')
            if len(body_val.strip()) > 0:
                result = process_payload(MODEL, "body", [body_val], False)
                if result and result.get("score", 0) >= BLOCKING_THRESHOLD:
                    is_malicious = True
        except Exception as e:
            logging.error(f"Error during WAFBrain prediction on body: {e}")

    if is_malicious:
        logging.warning("WAFBrain flagged request as malicious. Blocking.")
        return "403 Forbidden - Blocked by WAFBrain\n", 403

    # Forward the safe request to the Juice Shop backend
    url = f"{JUICE_SHOP_URL}/{path}"
    
    # Exclude hop-by-hop headers
    excluded_headers = ['host']
    headers = {k: v for k, v in request.headers if k.lower() not in excluded_headers}

    resp = requests.request(
        method=request.method,
        url=url,
        headers=headers,
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False,
        params=request.args
    )
    
    # Requests automatically decompresses gzip responses.
    # Therefore, we MUST strip the 'content-encoding' header if we are returning resp.content
    excluded_response_headers = ['transfer-encoding', 'connection', 'content-encoding', 'content-length']
    response_headers = [(name, value) for (name, value) in resp.raw.headers.items() 
                        if name.lower() not in excluded_response_headers]
    
    return Response(resp.content, resp.status_code, response_headers)

if __name__ == '__main__':
    logging.info("Starting WAFBrain proxy on port 80...")
    app.run(host='0.0.0.0', port=80)
