# CI 테스트용 최소 웹앱 
from flask import Flask
import socket

app = Flask(__name__)

@app.route('/')
def home():
    return f'<h1>Hello from {socket.gethostname()}</h1><p>CI/CD Test OK!</p>'

@app.route('/api/health')
def health():
    return {'status': 'ok'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

