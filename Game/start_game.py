# -*- coding: utf-8 -*-
import sys
import os

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 直接导入并运行app
from app import app, socketio

if __name__ == '__main__':
    print("🎮 启动股市卧底游戏服务器...")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)