from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html>
        <body>
            <h1>PRT HMI Dashboard</h1>
            <p>Hello World! HMI is running.</p>
            <p>TODO: Add your PRT dashboard here</p>
        </body>
    </html>
    """

@app.route('/api/status')
def status():
    return jsonify({
        "status": "running",
        "message": "PRT HMI is operational",
        "todo": "Add your PLC/DB integration here"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)