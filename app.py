from flask import Flask, request, jsonify, render_template_string
import uuid
import time
import os

app = Flask(__name__)

# Store sessions in memory
sessions = {}

# HTML Template
TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Turnstile Solver</title>
    <script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial; text-align: center; margin-top: 50px; }
        .container { max-width: 500px; margin: auto; padding: 20px; }
        .status { margin-top: 20px; padding: 10px; }
        .solved { color: green; }
        .waiting { color: orange; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🔐 Turnstile Solver</h2>
        <div class="cf-turnstile" data-sitekey="{{ sitekey }}" data-callback="onSubmit"></div>
        <div class="status" id="status">⏳ Waiting for solve...</div>
        <p><small>Session: {{ session_id }}</small></p>
    </div>
    <script>
        function onSubmit(token) {
            document.getElementById('status').innerHTML = '✅ Solved! Token received';
            document.getElementById('status').className = 'status solved';
            
            fetch('/submit', {
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
        "status": "running",
        "endpoints": {
            "POST /solve": '{"sitekey": "YOUR_SITEKEY"}',
            "GET /view/<session_id>": "Open in browser to solve",
            "GET /token/<session_id>": "Get solved token"
        }
    })

@app.route('/solve', methods=['POST'])
def solve():
    try:
        data = request.json
        sitekey = data.get('sitekey')
        
        if not sitekey:
            return jsonify({"error": "sitekey required"}), 400
        
        session_id = uuid.uuid4().hex[:12]
        
        # Store session
        sessions[session_id] = {
            "sitekey": sitekey,
            "token": None,
            "created": time.time(),
            "html": TEMPLATE.replace('{{ sitekey }}', sitekey).replace('{{ session_id }}', session_id)
        }
        
        return jsonify({
            "status": "success",
            "session_id": session_id,
            "view_url": f"{request.host_url}view/{session_id}",
            "token_url": f"{request.host_url}token/{session_id}"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/view/<session_id>')
def view(session_id):
    session = sessions.get(session_id)
    if not session:
        return "Session not found or expired", 404
    
    return session['html']

@app.route('/submit', methods=['POST'])
def submit():
    try:
        data = request.json
        session_id = data.get('session_id')
        token = data.get('token')
        
        if session_id in sessions:
            sessions[session_id]['token'] = token
            return jsonify({"status": "success"})
        
        return jsonify({"error": "Session not found"}), 404
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/token/<session_id>')
def get_token(session_id):
    session = sessions.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    
    if session['token']:
        return jsonify({
            "status": "solved",
            "token": session['token']
        })
    else:
        return jsonify({
            "status": "waiting",
            "message": "Solve turnstile first"
        })

# Cleanup old sessions (older than 10 minutes)
@app.before_request
def cleanup():
    now = time.time()
    to_delete = []
    for sid, data in sessions.items():
        if now - data['created'] > 600:  # 10 minutes
            to_delete.append(sid)
    for sid in to_delete:
        del sessions[sid]

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
