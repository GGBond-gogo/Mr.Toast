print("Python 工作正常！")
print("当前 Python 版本：")
import sys
print(sys.version)

try:
    import flask
    print("✅ Flask 已安装")
except ImportError:
    print("❌ Flask 未安装")

try:
    import flask_socketio
    print("✅ Flask-SocketIO 已安装")
except ImportError:
    print("❌ Flask-SocketIO 未安装")