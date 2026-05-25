from flask import Flask, request, jsonify, render_template_string
import uuid
import time

app = Flask(__name__)

# Store tokens and HTML in memory
tokens = {}
pages = {}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Turnstile Solver</title>
    <script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>
    <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
    <div style="text-align: center; margin-top: 50px;">
        <h2>Solve Turnstile</h2>
        <div class="cf-turnstile" data-sitekey="{{ sitekey }}" data-callback="onSubmit"></div>
        <p id="status">Waiting for solve...</p>
        <p><small>Session: {{ session_id }}</small></p>
    </div>
    <script>
        function onSubmit(token) {
            document.getElementById('status').innerHTML = 'Solved! Token: ' + token.substring(0, 30) + '...';
            fetch(window.location.origin + '/submit-token', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    session_id: '{{ session_id }}',
                    token: token
                })
            });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return jsonify({
        "service": "Turnstile Solver",
        "endpoints": {
            "solve": "POST /solve with {sitekey}",
            "get-token": "GET /get-token/{session_id}"
        }
    })

@app.route('/solve', methods=['POST'])
def solve():
    data = request.json
    sitekey = data.get('sitekey')
    
    if not sitekey:
        return jsonify({"error": "sitekey required"}), 400
    
    session_id = uuid.uuid4().hex[:16]
    tokens[session_id] = None
    
    html = HTML_TEMPLATE.replace('{{ sitekey }}', sitekey)
    html = html.replace('{{ session_id }}', session_id)
    
    pages[session_id] = html
    
    return jsonify({
        "status": "waiting",
        "session_id": session_id,
        "url": f"{request.host_url}view/{session_id}"
    })

@app.route('/view/<session_id>')
def view(session_id):
    html = pages.get(session_id)
    if html:
        return html
    return "Session expired or invalid", 404

@app.route('/submit-token', methods=['POST'])
def submit_token():
    data = request.json
    session_id = data.get('session_id')
    token = data.get('token')
    
    if session_id in tokens:
        tokens[session_id] = token
        return jsonify({"status": "success"})
    return jsonify({"error": "Invalid session"}), 404

@app.route('/get-token/<session_id>')
def get_token(session_id):
    token = tokens.get(session_id)
    if token:
        return jsonify({"status": "solved", "token": token})
    return jsonify({"status": "waiting"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
