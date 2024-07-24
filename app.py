# from gevent import monkey; monkey.patch_all()
from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from flask_session import Session
from cas_client import CASClient
import redis
from redis import Redis
from flask_socketio import SocketIO
from threading import Lock
from blacklist import blacklist
from datetime import timedelta
from flask_cors import CORS

async_mode = None
app = Flask(__name__,
            template_folder='./templates',
            static_folder='./static'
            )

app.debug = True
app.config['SECRET_KEY'] = 'some-secret-string'

app_login_url = 'http://8.130.52.22:5000/login'     # 需要替换
cas_url = 'https://auth.bupt.edu.cn/authserver'
cas_client = CASClient(cas_url, auth_prefix='')


socketio = SocketIO(app, cors_allowed_origins="*")
thread = None
thread_lock = Lock()

# 登录session存入redis持久化
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = Redis(host='8.130.73.85', port=6379)   # 需要替换
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=3)  # 设置 session 过期时间为 3h
app.config['SESSION_PERMANENT'] = True  # 设置 session 为永久性
Session(app)
CORS(app, origins=['http://8.130.52.22:5000'])   #替换
# 数据使用redis连接池存入
pool = redis.ConnectionPool(host='localhost', port=6379, db=0, password='dcztp2024')    #密码可能替换


# 登录路由
@app.route('/login')
def login():
    ticket = request.args.get('ticket')
    # print('ticket:',ticket)
    if ticket:
        try:
            cas_response = cas_client.perform_service_validate(
                ticket=ticket,
                service_url=app_login_url,
                )
            # print(cas_response.data)
        except:
            # CAS server is currently broken, try again later.
            return redirect(url_for('root'))
        if cas_response and cas_response.success:
            # print('session')
            if cas_response.data['user'] not in blacklist:
                session['logged-in'] = True
            else:
                session['logged-in'] = False
            session['username'] = cas_response.data['user']
            """
            创建 redis 连接
            """
            con = redis.Redis(
                connection_pool=pool
            )
            res = con.zrange('username', 0, -1)
            # print(res)
            if bytes(session['username'],'utf-8') not in res and session['username'] not in blacklist:
                # print('新来的')
                con.zadd('username',{session['username']:10})
            """
            创建 mysql 连接
            """
            # sql = "SELECT * FROM `vote` WHERE username =" + cas_response.data['user']
            # res = resources.query(sql)
            # print(res)
            # if len(res) == 0:
                # sql = "INSERT INTO vote (username, ticket) VALUES ('" + cas_response.data['user'] + "', DEFAULT)"
                # resources.insert(sql)
            return redirect(url_for('root'))
    # del(session['logged-in'])
    cas_login_url = cas_client.get_login_url(service_url=app_login_url)
    return redirect(cas_login_url)

# 登出路由
@app.route('/api/logout')
def logout():
    if session.get('logged-in'):
        session.pop('logged-in')
        session.pop('username')
        cas_logout_url = cas_client.get_logout_url(service_url=app_login_url)
        return cas_logout_url

    else:
        return redirect(url_for('login'))

    # cas_logout_url = cas_client.get_logout_url(service_url=app_login_url)
    # print("logout..............")
    # return redirect(cas_logout_url)

# 获取用户身份
@app.route('/api/secret')
# @app.route('/secret')
def getSession():
    if session.get('logged-in'):
        return session.get('username')
    else:
        return redirect(url_for('login'))

# 用户投票
@app.route('/api/vote')
def getVote():
    if session.get('logged-in'):
        project_id = request.args.get('id')
        # username = request.values.get('username')
        # json_re = json.loads(data)
        # print(project_id)
        username = session['username']
        # print(username)
        con = redis.Redis(
               connection_pool=pool
           )
        user_likes = []
        for key in con.scan_iter("voted:*"):
            if con.sismember(key, session['username']):
                # print(key)
                user_likes.append(key.decode('utf8').replace('voted:',''))
        ticket = con.zscore("username", session['username'])
        if ticket > 0:
            if project_id not in user_likes:
                con.zincrby('score', 1, project_id)
                con.zincrby('username', -1, username)
                con.sadd("voted:" + project_id, username)
                return {"message":"投票成功"}
            else:
                return {"message":"请勿重复投票！！！"}
        # return {"data":project_id}
        else:
            return {"message":"票已经用完啦！！！"}
    else:
        return redirect(url_for('login'))

# 获取用户剩余的票数
@app.route('/api/ticket')
def getTicket():
    if session.get('logged-in'):
        con = redis.Redis(
                connection_pool=pool
                )
        res = con.zscore("username", session['username'])
        # print(res)
        return jsonify(res)
    else:
        return redirect(url_for('login'))

# 获取单个用户的投票状态
@app.route('/api/user_likes')
def getUser_likes():
    if session.get('logged-in'):
        con = redis.Redis(
                connection_pool=pool
                )
        res = []
        for key in con.scan_iter("voted:*"):
            if con.sismember(key, session['username']):
                # print(key)
                res.append(key.decode('utf8').replace('voted:',''))
        # print(res)
        return jsonify(res)
    else:
        return redirect(url_for('login'))

# 获取所有项目的票数
@app.route('/api/score')
def getScore():
    if session.get('logged-in'):
        con = redis.Redis(
                connection_pool=pool
                )
        res = con.zrevrange("score", 0, -1, withscores=True)
        for i in range(len(res)):
            res[i] = list(res[i])
            res[i][0] = res[i][0].decode('utf-8')
            res[i] = tuple(res[i])
        # print(res)
        dic = dict(res)
        return jsonify(dic)
    else:
        return redirect(url_for('login'))


# 用户浏览
@app.route('/api/update_views')
def UpdateViews():
    if session.get('logged-in'):
        project_id = request.args.get('id')
        con = redis.Redis(
               connection_pool=pool
           )
        con.zincrby('views', 1, project_id)
        return {"message":"update_views成功"}
        # return {"data":project_id}
    else:
        return redirect(url_for('login'))

# 获取所有项目的浏览量
@app.route('/api/views')
def getViews():
    if session.get('logged-in'):
        con = redis.Redis(
                connection_pool=pool
                )
        res = con.zrevrange("views", 0, -1, withscores=True)
        for i in range(len(res)):
            res[i] = list(res[i])
            res[i][0] = res[i][0].decode('utf-8')
            res[i] = tuple(res[i])
        # print(res)
        dic = dict(res)
        return jsonify(dic)
    else:
        return redirect(url_for('login'))

# 使用websocket进行排行榜的推流
@socketio.on('connect', namespace='/update_rank')
def test_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=background_thread)

def background_thread():
    while True:
        con = redis.Redis(
                connection_pool=pool
                )
        res = con.zrevrange("score", 0, -1, withscores=True)
        for i in range(10):
            res[i] = list(res[i])
            res[i][0] = res[i][0].decode('utf-8')
            # res[i] = tuple(res[i])
        # print(res[0:10])
        # dic = dict(res)
        # print(dic)
        socketio.emit('server_response',
                      {'data': res[0:10]},namespace='/update_rank')
        socketio.sleep(10)

# 处理 404 错误（找不到页面）
@app.errorhandler(404)
def page_not_found(e):
    if session.get('logged-in') and session['username'] not in blacklist:
        return render_template('index.html')
    
    else:
        return redirect(url_for('login'))

# 请求拦截
@app.route('/rank')
@app.route('/blacklist')
def page():
    if session.get('logged-in') and session['username'] not in blacklist:
        return render_template('index.html')
    
    else:
        return redirect(url_for('login'))


# 主页
@app.route('/')
def root():
    if session.get('logged-in') and session['username'] not in blacklist:
        return render_template('index.html')
    
    else:
        return redirect(url_for('login'))
    # return render_template('index.html')


if __name__ == '__main__':
    # app.run(host="0.0.0.0",port=80)
    socketio.run(app, debug=True,host='0.0.0.0',port=5000)
    # from gevent import pywsgi
    # app.debug = True
    # server = pywsgi.WSGIServer( ('0.0.0.0', 80 ), app )
    # server.serve_forever()

