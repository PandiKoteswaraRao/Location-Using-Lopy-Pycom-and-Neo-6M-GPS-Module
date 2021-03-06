from machine import UART
from time import sleep

__version__ = "0." + "$Revision: 1.5 $"[11:-2]
__license__ = 'GPLV4'

# Config.py definitions preceed
# if UARTpins array of (Tx,Rx) tuples is defined try to identify UART device
# if UARTpins is defined dust or useGPS + pins maybe overwritten
class identifyUART:
  def __init__(self, uart=[-1], UARTpins=[('P11','P10')], debug=False):
    error = "Unable to identify UART devs"
    self.uart = uart
    if len(self.uart) > 3: raise ValueError(error)
    self.debug = debug
    self.UARTs = UARTpins
    self.dust = ''; self.D_Tx = None; self.D_Rx = None
    self.useGPS = ''; self.G_Tx = None; self.G_Rx = None
    try:
      from Config import UARTpins as pins
      if (type(pins) is list) and len(pins): self.UARTS = pins
    except: pass
    self.dust = 'PMSx003'; self.D_Tx = UARTpins[0][0]; self.D_Rx = UARTpins[0][1]  # defaults
    try:
      from Config import dust, D_Tx, D_Rx
      self.dust = dust; self.D_Tx = D_Tx; self.D_Rx = D_Rx  # use config
    except:  pass
    # self.useGPS = False; self.G_Tx = UARTpins[1][0]; self.G_Rx = UARTpins[1][1]  # defaults
    try:
      from Config import useGPS, G_Tx, G_Rx
      self.useGPS = useGPS; self.G_Tx = G_Tx; self.G_Rx = G_Rx  # use config
    except:  pass
    if not len(self.UARTs):
      if self.debug: print("No UART pins defined")
    else:
      devs = self.identify()
      if self.debug: print("Found UART devices: %s" % ', '.join(devs))
    return None

  # try to discover type of uart sensor
  def identify(self):
    found = []
    for one in self.UARTs:
        if (len(one) != 2) or (not type(one[0]) is str) or (not type(one[1]) is str):
            continue
        if self.debug: print("Try UART pins Tx %s, Rx %s" % one)
        for baud in [9600,115200]:
          cnt = len(found)
          ser = UART(len(self.uart), baudrate=baud, pins=one, timeout_chars=20)
          for i in range(0,6): # try 3 times to read known pattern
            line = []
            sleep(2)
            try: line = ser.readall()
            except:
                print("Uart read error")
                continue
            if (line == None) or (not len(line)):   # try to wake up
                if not 'dust' in found:
                  if self.debug: print("Try to wake up device")
                  if (i%3) == 0: ser.write(b'\x42\x4D\xE1\x00\x01\x01\x71') # try activate PMS
                  elif (i%3) == 1: ser.write(b'\xAA\xB4\x06\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\xFF\x06\xAB') # second try activate SDS
                  elif (i%3) == 2:
                    ser.write(b'~\x00\xd3\x00,~') # try reset SPS
                  sleep(1)
                continue
            # if self.debug: print("Read: %s" % line)
            if (not 'dust' in found) and (line.count(b'\x42\x4D') > 0): # start char BM
                self.dust = 'PMSx003'; self.D_Tx = one[0]; self.D_Rx = one[1]
                found.append('dust')
            elif (not 'dust' in found) and line.count(b'\xAA') and line.count(b'\xC0'): # start char 0xAA,0xC0 tail 0xAB
                self.dust = 'SDS011'; self.D_Tx = one[0]; self.D_Rx = one[1]
                found.append('dust')
            elif (not 'gps' in found) and (line.count(b'GPGGA') or line.count(b',') > 1):
                self.useGPS = 'UART'; self.G_Tx = one[0]; self.G_Rx = one[1]
                found.append('gps')
            elif (not 'dust' in found) and (line.count(b'~\x00\xd3\x00') or line.count(b'\x00\x2C~')):
                self.useGPS = 'SPS30'; self.G_Tx = one[0]; self.G_Rx = one[1]
                found.append('dust')
            else: continue
            if self.debug: print("UART: %s on Tx %s, Rx %s" % (found[-1], one[0],one[1]))
            break
          ser.readall(); ser.deinit(); del ser
          if len(found) > cnt: break
          if i > 2:
            print("Unknown device found on Tx %s, Rx %s" % one)
    return found

  @property
  def uartDust(self):
    return self.dust, self.D_Tx, self.D_Rx

  @property
  def DUST(self):
    return self.dust

  @property
  def D_TX(self):
    return self.D_Tx

  @property
  def D_RX(self):
    return self.D_Rx

  @property
  def uartGPS(self):
    return self.useGPS, self.G_Tx, self.G_Rx

  @property
  def GPS(self):
    return self.useGPS

  @property
  def G_TX(self):
    return self.G_Tx

  @property
  def G_RX(self):
    return self.G_Rx
