import x68k
import random
import time
from uctypes import addressof
from struct import pack

class Hai:

  gvram = x68k.GVRam()

  patterns = []

  def __init__(self, id, type):
    self.hai_id = id
    self.hai_type = type
    self.hai_status = 0

  def paint(self, pos_x, pos_y):
    pattern = Hai.patterns[ self.hai_type ] if self.hai_status == 0 else Hai.patterns [ 7 + 9 * 3 + 3 ]
    Hai.gvram.put(12 + pos_x * 24 , 16 + pos_y * 32, 12 + pos_x * 24 + 23, 16 + pos_y * 32 + 35, pattern)

def init_hais():

  # 牌画像データ読み込み
  hai0 = bytearray()
  with open("hai0.dat","rb") as f:
    while True:
      h = f.read()
      if len(h) == 0:
        break
      hai0.extend(h)

  patterns = []
  for i in range( 7 + 9 * 3 + 3 + 1 ):    # 字牌(7) + 萬子(9) + 筒子(9) + 索子(9) + 赤5(3) + 背面(1)
    patterns.append(bytes(hai0[ 24 * 36 * 2 * i : 24 * 36 * 2 * ( i + 1 ) ]))
  Hai.patterns = patterns

  hais = []
  for i in range(34*4):
    t = i % 34
    h = Hai(i, t)
    hais.append(h)

  return hais

def shuffle_hais(hais):
  for i in range(len(hais) * 8):
    a = random.randrange(0,len(hais)-1)
    b = random.randrange(0,len(hais)-1)
    c = hais[a]
    hais[a] = hais[b]
    hais[b] = c

def main():

  # randomize
  random.seed(int(time.time() * 10))

  # 512 x 512 x 65536 (31kHz) mode
  x68k.crtmod(12, True)

  # cursor off
  x68k.curoff()

  # function key display off
  funckey_mode = x68k.dos(x68k.d.CONCTRL,pack('hh',14,3))

  # init 牌
  print("Initializing hai data...",end="")
  hais = init_hais()
  shuffle_hais(hais)
  print("\r\x1b[0K")

  # 雀卓
  x68k.iocs(x68k.i.FILL,a1=pack('5h',0,0,511,511,0b01000_00011_00011_1))

  # supervisor mode
  #s = x68k.super()

  # 相手の牌
  for i,h in enumerate(hais[13:26]):
    for v in range(3):
      x68k.vsync()
    h.hai_status = 2    # 背面
    h.paint(4+i,2)

  # 自分の牌
  for i,h in enumerate(hais[0:13]):
    for v in range(3):
      x68k.vsync()
    h.hai_status = 0    # 起牌
    h.paint(4+i,13)

  # 一度伏せて
  for i,h in enumerate(hais[0:13]):
    for v in range(3):
      x68k.vsync()
    h.hai_status = 2    # 背面
    h.paint(4+i,13)

  # 理牌
  for i,h in enumerate(sorted(hais[0:13],key=lambda h: h.hai_type)):
    for v in range(3):
      x68k.vsync()
    h.hai_status = 0
    h.paint(4+i,13)

  time.sleep(3)

  # user mode
  #x68k.super(s)

  # flush key buffer
  x68k.dos(x68k.d.KFLUSH,pack('h',0))  

  # resume function key display mode
  x68k.dos(x68k.d.CONCTRL,pack('hh',14,funckey_mode))

  # cursor on
  x68k.curon()

if __name__ == "__main__":
  main()