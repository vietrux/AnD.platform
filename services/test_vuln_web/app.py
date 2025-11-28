# Simple Vulnerable Web Service
# For CTF testing purposes

from flask import Flask, request, render_template_string
import os
import subprocess

app = Flask(__name__)

# Home page with intentional vulnerabilities
HOME_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Vulnerable File Reader</title>
    <style>
        body { font-family: Arial; margin: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        input, button { padding: 10px; margin: 5px; }
        .result { background: #f0f0f0; padding: 20px; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📁 File Reader Service</h1>
        <p>Welcome to the file reading service!</p>
        
        <h2>Read File</h2>
        <form action="/read" method="GET">
            <input type="text" name="file" placeholder="Enter filename" size="50">
            <button type="submit">Read</button>
        </form>
        
        <h2>Ping Tool</h2>
        <form action="/ping" method="GET">
            <input type="text" name="host" placeholder="Enter hostname/IP" size="50">
            <button type="submit">Ping</button>
        </form>
        
        <hr>
        <p><small>Flags are located at:</small></p>
        <ul>
            <li><code>/home/ctf/flag1.txt</code> - User flag (easy)</li>
            <li><code>/root/flag2.txt</code> - Root flag (requires RCE + privesc)</li>
        </ul>
    </div>
</body>
</html>
"""

RESULT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Result</title>
    <style>
        body { font-family: Arial; margin: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        .result { background: #f0f0f0; padding: 20px; white-space: pre-wrap; }
        a { display: inline-block; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Result</h1>
        <div class="result">{{ result }}</div>
        <a href="/">← Back</a>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    """Home page"""
    return render_template_string(HOME_TEMPLATE)


@app.route('/read')
def read_file():
    """
    VULN 1: Path Traversal
    Easy vulnerability to read user flag
    """
    filename = request.args.get('file', '')
    
    if not filename:
        return render_template_string(RESULT_TEMPLATE, result="No file specified")
    
    try:
        # VULNERABLE: No sanitization!
        with open(filename, 'r') as f:
            content = f.read()
        return render_template_string(RESULT_TEMPLATE, result=content)
    except Exception as e:
        return render_template_string(RESULT_TEMPLATE, result=f"Error: {str(e)}")


@app.route('/ping')
def ping():
    """
    VULN 2: Command Injection
    Vulnerable to command injection for RCE
    """
    host = request.args.get('host', '')
    
    if not host:
        return render_template_string(RESULT_TEMPLATE, result="No host specified")
    
    try:
        # VULNERABLE: No sanitization! Command injection possible
        # Example exploit: 127.0.0.1; cat /root/flag2.txt
        result = subprocess.check_output(
            f"ping -c 1 {host}",
            shell=True,  # DANGEROUS!
            stderr=subprocess.STDOUT,
            timeout=5
        ).decode()
        return render_template_string(RESULT_TEMPLATE, result=result)
    except subprocess.TimeoutExpired:
        return render_template_string(RESULT_TEMPLATE, result="Timeout!")
    except Exception as e:
        return render_template_string(RESULT_TEMPLATE, result=str(e))


if __name__ == '__main__':
    # Run on all interfaces
    app.run(host='0.0.0.0', port=8001, debug=True)
