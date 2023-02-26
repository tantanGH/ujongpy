import x68k
import machine
import random
import time
from uctypes import addressof
from struct import pack, unpack

class Hai:

  # Hai instance ID
  hai_id = None

  # Hai type
  hai_type = None

  # Hai status
  hai_status = None

  # image addr
  images = None

  def __init__(self, id, type, image0, image1, image2):
    self.hai_id = id
    self.hai_type = type
    self.images = [ image0, image1, image2 ]     # 起牌, 倒牌, 背面

  def paint(self, pos_x, pos_y):
    with x68k.Super():
      image_addr = self.images[ self.hai_status ]
      for y in range(36):
        vram_addr = 0xC00000 + ( 16 + pos_y * 32 + y ) * 512 * 2 + 16 + pos_x * 24 * 2
        for x in range(12):
          machine.mem32[ vram_addr ] = machine.mem32[ image_addr ]
          vram_addr += 4
          image_addr += 4

def init_hais():

  # 牌画像データ読み込み
  hai0 = bytearray()
  with open("hai0.dat","rb") as f:
    while True:
      h = f.read()
      if len(h) == 0:
        break
      hai0.extend(h)
#  print(f"len(hai0)={len(hai0)}")
  #with open("hai1.dat","rb") as f:
  #  hai1 = f.read()

  hais = []
  for i in range(34*4):
    t = i // 4
    h = Hai(i, t, addressof(hai0) + 24*36*2*t, None, addressof(hai0) + 24*36*2*(34+3))
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
    h.hai_status = 2    # 背面
    h.paint(4+i,2)
#    time.sleep(0.2)

  # 自分の牌
  for i,h in enumerate(hais[0:13]):
    h.hai_status = 0    # 起牌
    h.paint(4+i,13)
#    time.sleep(0.2)

  # 一度伏せて
  for i,h in enumerate(hais[0:13]):
    h.hai_status = 2    # 背面
    h.paint(4+i,13)

  # 理牌
  for i,h in enumerate(sorted(hais[0:13],key=lambda h: h.hai_type)):
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