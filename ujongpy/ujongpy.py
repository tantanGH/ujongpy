import x68k
import random
import time
from uctypes import addressof
from struct import pack

# 牌クラス
class Hai:

  # クラス変数 - GVRam オブジェクト参照
  gvram = x68k.GVRam()

  # クラス変数 - 牌パターン定義バイト列のリスト
  patterns = None

  # コンストラクタ
  def __init__(self, id, type):
    self.hai_id = id
    self.hai_type = type
    self.hai_status = 2

  # パターンデータ参照
  def get_pattern(self):
    if self.hai_status == 2:            
      return Hai.patterns [ 7 + 9 * 3 + 3 ]   # 背面
    elif self.hai_status == 1:          
      return Hai.patterns [ 7 + 9 * 3 + 3 + 1 + self.hai_type ]   # 倒牌
    else:
      return Hai.patterns [ self.hai_type ]   # 起牌

  # パターン描画
  def paint(self, pos_x, pos_y):
   Hai.gvram.put(pos_x * 24 , 16 + pos_y * 32, pos_x * 24 + 23, 16 + pos_y * 32 + 35, self.get_pattern())

  # 配牌
  @classmethod
  def get_hais(cls, hai0_file_name, hai1_file_name):

    # 牌画像データ読み込み (起牌)
    hai0 = bytearray()
    with open(hai0_file_name,"rb") as f:
      while True:
        h = f.read()
        if len(h) == 0:
          break
        hai0.extend(h)

    # 牌画像データ読み込み (倒牌)
    hai1 = bytearray()
    with open(hai1_file_name,"rb") as f:
      while True:
        h = f.read()
        if len(h) == 0:
          break
        hai1.extend(h)

    # パターン登録
    patterns = []
    for i in range( 7 + 9 * 3 + 3 + 1 ):    # 字牌(7) + 萬子(9) + 筒子(9) + 索子(9) + 赤5(3) + 背面(1)
      patterns.append(bytes(hai0[ 24 * 36 * 2 * i : 24 * 36 * 2 * ( i + 1 ) ]))
    for i in range( 7 + 9 * 3 + 3 + 1 ):    # 字牌(7) + 萬子(9) + 筒子(9) + 索子(9) + 赤5(3)
      patterns.append(bytes(hai1[ 24 * 36 * 2 * i : 24 * 36 * 2 * ( i + 1 ) ]))
    Hai.patterns = patterns

    # 牌インスタンス作成 字牌(7) + 萬子(9) + 筒子(9) + 索子(9) 
    hais = []
    for i in range(34*4):
      t = i % 34
      h = Hai(i, t)
      hais.append(h)

    return hais

  # 洗牌
  @classmethod
  def shuffle_hais(self, hais):
    for i in range(len(hais) * 8):
      a = random.randrange(0,len(hais)-1)
      b = random.randrange(0,len(hais)-1)
      c = hais[a]
      hais[a] = hais[b]
      hais[b] = c

# メイン
def main():

  # randomize
  random.seed(int(time.time() * 10))

  # 512 x 512 x 65536 (31kHz) mode
  x68k.crtmod(12, True)

  # cursor off
  x68k.curoff()

  # function key display off
  funckey_mode = x68k.dos(x68k.d.CONCTRL,pack('hh',14,3))

  # 配牌
  print("Initializing hai data...",end="")
  hais = Hai.get_hais("hai0.dat", "hai1.dat")
  Hai.shuffle_hais(hais)
  print("\r\x1b[0K")

  # 雀卓
  x68k.iocs(x68k.i.FILL,a1=pack('5h',0,0,511,511,0b01000_00011_00011_1))

  # 王牌
  for i,h in enumerate(hais[-14:]):
    x68k.vsync()
    h.hai_status = 2    # 背面
    h.paint(9+i//2,7)

  # ドラ表示牌
  time.sleep(0.5)
  x68k.vsync()
  hais[-5].hai_status = 0
  hais[-5].paint(9+2,7)

  # 相手の牌ならべる
  for i,h in enumerate(hais[13:26]):
    for v in range(3):
      x68k.vsync()
    h.hai_status = 2    # 背面
    h.paint(4+i,2)

  # 自分の牌ならべる
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

  # flush key buffer
  x68k.dos(x68k.d.KFLUSH,pack('h',0))  

  # resume function key display mode
  x68k.dos(x68k.d.CONCTRL,pack('hh',14,funckey_mode))

  # cursor on
  x68k.curon()

if __name__ == "__main__":
  main()