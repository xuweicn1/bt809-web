#!/usr/bin/env python
import time
import serial
import struct
with serial.Serial('/dev/ttyUSB0',4800,timeout=1) as ser:
  # while 1:
    # time.sleep(2)
    s = '81815201'
    ser.write(bytes.fromhex(s))
    fd = ser.readline()
    if len(fd) == 8:
      r =list(struct.unpack('hhbbh',fd))
      r[0],r[1] = r[0]/10,r[1]/10
      print('测量值是：{}℃\n给定值是：{}℃\n所读参数是：{}分'.format(r[0],r[1],r[4]))
      print(r)