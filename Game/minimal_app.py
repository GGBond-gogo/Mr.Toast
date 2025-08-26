from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello, Flask!"

if __name__ == '__main__':
    print("启动 Flask 应用...")
    app.run(debug=True, port=5000)