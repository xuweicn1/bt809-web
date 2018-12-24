import psutil, time, glob, struct, serial,sqlite3
from threading import Lock
from flask import Flask,render_template, session, request
from flask_socketio import SocketIO, emit
# from app.models import BT809
from app import app

# SECRET_KEY = 'you-will-never-guess'
# SQLALCHEMY_TRACK_MODIFICATIONS = False

# app = Flask(__name__)

async_mode = None
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()


dbname='BT809Data.db'
# sampleFreq = 1*60 # time in seconds ==> Sample each 1 min

#从809取数
def getBT809data(x):
  # with serial.Serial('/dev/ttyUSB0',4800,timeout=1) as ser:
  with serial.Serial('com3',4800,timeout=0.5) as ser:
    ser.write(bytes.fromhex(x))
    fd = ser.readline()
    if len(fd) == 8:
      r = struct.unpack('hhbbh',fd)
    return r

# 数据存储进数据库

#数据入库
def logTemp(t1,t2,t3,t4):
  conn=sqlite3.connect(dbname,check_same_thread = False)
  curs=conn.cursor()
  curs.execute("INSERT INTO temp VALUES(\
                  datetime('now','localtime'),(?), (?),(?),(?))",(t1,t2,t3,t4))
  conn.commit()
  conn.close()

# 存入4个通道温度数据
def sav():
  fd1 = getBT809data('8181521B')
  fd2 = getBT809data('8282521B')
  fd3 = getBT809data('8383521B')
  fd4 = getBT809data('8484521B')
  t1,t2,t3,t4 = fd1[0]/10,fd2[0]/10,fd3[0]/10,fd4[0]/10
  logTemp(t1,t2,t3,t4)
  print("Deposit data...")
  # time.sleep(sampleFreq)

# 读取数据库最新数据
def getData():
  conn=sqlite3.connect(dbname,check_same_thread = False)
  curs=conn.cursor()
  for row in curs.execute("SELECT * FROM temp ORDER BY timestamp DESC LIMIT 1"):
    time = str(row[0])
    channel_1 = row[1]
    channel_2 = row[2]
    channel_3 = row[3]
    channel_4 = row[4]
  conn.close()
  return time, channel_1, channel_2, channel_3, channel_4

# 后台线程 产生数据，即刻推送至前端
def background_thread():
    count = 0
    while True:
        socketio.sleep(10)
        sav()
        r = getBT809data('8181521B')
        t = time.strftime('%H:%M:%S', time.localtime()) # 获取系统时间
        socketio.emit('server_response',{'data': [t] + [r[0]/10], 'count': count},namespace='/test')

# 主页
@app.route("/")
def index():
  time, channel_1, channel_2, channel_3, channel_4 = getData()
  templateData = {
    'time': time,
    'channel_1': channel_1,
    'channel_2': channel_2,
    'channel_3': channel_3,
    'channel_4': channel_4
  }
  return render_template('index.html', **templateData)

# 与前端建立 socket 连接后，启动后台线程
@socketio.on('connect', namespace='/test')
def test_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=background_thread)

if __name__ == '__main__':
    # socketio.run(app, debug=True)
    app.run(host='0.0.0.0',debug=True)
