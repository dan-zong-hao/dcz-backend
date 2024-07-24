"""gunicorn + eventlet 的配置文件"""

# 多进程
import multiprocessing

# 绑定ip + 端口
bind = '0.0.0.0:5000'

# 进程数 = cup数量 * 2 + 1
workers = 1

# 等待队列最大长度，超过这个长度的链接将被拒绝连接
backlog = 2048

# 工作模式--协程
worker_class = 'eventlet'

# 最大客户客户端并发数量，对使用协程的 worker 的工作有影响
# 服务器配置设置的值  1000：中小型项目  上万并发： 中大型
worker_connections = 1000

# 进程名称
proc_name = 'gunicorn.pid'

# 进程 pid 记录文件
pidfile = 'gunicorn.pid'

# 日志等级
loglevel = 'warning'

# 日志文件名
logfile = 'gunicorn_log.log'

# 设置访问日志
accesslog = 'gunicorn_acess.log'

# 设置错误信息日志
errorlog  = 'gunicorn_error.log'

# 代码发生变化是否自动重启
reload = True

daemon = True
