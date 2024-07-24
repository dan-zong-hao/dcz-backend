from flask import Flask, session
from flask_session import Session
from redis import Redis
from datetime import timedelta

app = Flask(__name__)

SESSION_TYPE = 'redis'
SESSION_REDIS = Redis(host='8.130.73.85', port=6379)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=6)  # 设置 session 过期时间为 30 分钟
app.config['SESSION_PERMANENT'] = True  # 设置 session 为永久性
app.config.from_object(__name__)
Session(app)

@app.route('/set/')
def set():
    session['username'] = 'root'
    return 'ok'

@app.route('/get/')
def get():
    return session.get('username')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
