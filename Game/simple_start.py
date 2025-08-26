# -*- coding: utf-8 -*-
from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'stock_undercover_game_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return "<h1>🎮 股市卧底游戏服务器</h1><p>服务器运行正常！</p>"

@app.route('/test')
def test():
    return "🎮 游戏服务器运行正常！"

if __name__ == '__main__':
    print("🎮 启动简化版游戏服务器...")
    print("📍 访问 http://localhost:5000 测试服务器")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)