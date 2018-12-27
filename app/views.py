import psutil
import time
import glob
import struct
import serial
import sqlite3 as lite
from threading import Lock
from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit
from app import app
import RPi.GPIO as GPIO


async_mode = None
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()


dbname = 'BT809Data.db'
con = lite.connect(dbname, check_same_thread=False)
cur = con.cursor()

GPIO.setmode(GPIO.BCM)

pins = {
   18 : {'name' : '信道1', 'state' : GPIO.LOW},
   23 : {'name' : '信道2', 'state' : GPIO.LOW},
   24 : {'name' : '信道3', 'state' : GPIO.LOW}
   }

for pin in pins:
    '''设置每个引脚为输出,置低电平'''
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

def getBT809data(x):
    """从809取数 """
    with serial.Serial('/dev/ttyUSB0',4800,timeout=1) as ser:
    # with serial.Serial('com3', 4800, timeout=0.5) as ser:
        ser.write(bytes.fromhex(x))
        fd = ser.readline()
        if len(fd) == 8:
            r = struct.unpack('hhbbh', fd)
        return r


def logTemp(t1, t2, t3, t4):
    """数据入库"""
    with con:
        sql = "INSERT INTO temp VALUES(datetime('now','localtime'),(?), (?),(?),(?))"
        cur.execute(sql, (t1, t2, t3, t4))


def sav():
    """4通道温度存入数据库"""
    fd1 = getBT809data('8181521B')
    fd2 = getBT809data('8282521B')
    fd3 = getBT809data('8383521B')
    fd4 = getBT809data('8484521B')
    t1, t2, t3, t4 = fd1[0]/10, fd2[0]/10, fd3[0]/10, fd4[0]/10
    logTemp(t1, t2, t3, t4)
    print("Deposit data...")
    # time.sleep(sampleFreq)


def getData():
    """读取数据库最新数据"""
    with con:
        sql = "SELECT * FROM temp ORDER BY timestamp DESC LIMIT 1"
        for row in cur.execute(sql):
            time = str(row[0])
            channel_1 = row[1]
            channel_2 = row[2]
            channel_3 = row[3]
            channel_4 = row[4]
        return time, channel_1, channel_2, channel_3, channel_4


def background_thread():
    """后台线程产生数据，即刻推送至前端"""
    count = 0
    while True:
        socketio.sleep(10)
        sav()
        r = getBT809data('8181521B')
        t = time.strftime('%H:%M:%S', time.localtime())  # 获取系统时间
        socketio.emit('server_response', {
                      'data': [t] + [r[0]/10], 'count': count}, namespace='/test')


@app.route("/")
def index():
    """主页"""
    time, channel_1, channel_2, channel_3, channel_4 = getData()
    templateData = {
        'time': time,
        'channel_1': channel_1,
        'channel_2': channel_2,
        'channel_3': channel_3,
        'channel_4': channel_4
    }
    return render_template('home.html', **templateData)


@socketio.on('connect', namespace='/test')
def test_connect():
    """与前端建立 socket 连接后，启动后台线程"""
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=background_thread)


@app.route("/table", methods=['POST', 'GET'])
def table():
   """获取数据库提交"""
   with con:
      cur.execute('''select * from temp''')
      data = cur.fetchall ()
   return render_template("table.html",data=data)

@app.route("/vents")
def vents():
   '''读引脚状态发送到前端'''
   for pin in pins:
      pins[pin]['state'] = GPIO.input(pin)
   templateData = {
      'pins' : pins
      }
   return render_template('vents.html', **templateData)

@app.route("/<int:changePin>/<action>", methods=['GET', 'POST'])
def vent(changePin, action):
    '''执行前端发来请求'''
    if action == "on":
        '''通电'''
        GPIO.output(changePin, GPIO.HIGH)

    if action == "off":
        '''断电'''
        GPIO.output(changePin, GPIO.LOW)

    for pin in pins:
        '''读引脚状态发送到网页'''
        pins[pin]['state'] = GPIO.input(pin)

    templateData = {
    'pins' : pins
    }

    return render_template('vents.html', **templateData)




if __name__ == '__main__':
    # socketio.run(app, debug=True)
    app.run(host='0.0.0.0', debug=True)
