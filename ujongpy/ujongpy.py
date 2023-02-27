import x68k
import random
import time
from uctypes import addressof
from struct import pack

# バージョン
VERSION = const("2023.02.27c")

# 牌クラス
class Hai:

  # クラス変数 - GVRam オブジェクト参照
  gvram = x68k.GVRam()

  # クラス変数 - 牌パターン定義バイト列のリスト
  patterns = None

  # コンストラクタ
  def __init__(self, id:int, type:int):
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

  # パターン描画 (グラフィック)
  #  row ... 0:COMPUTER手牌 1:PLAYER手牌 2:王牌  
  #@micropython.viper
  def put(self, row:int, pos_x:int):
    if row == 0:
      x = 4 * 24 + pos_x * 24 if pos_x != -1 else 4 * 24 + pos_x * 24 - 4
      y = 1 * 36
    elif row == 1:
      x = 4 * 24 + pos_x * 24 if pos_x != 13 else 4 * 24 + pos_x * 24 + 4
      y = 12 * 36
    elif row == 2:
      x = 9 * 24 + pos_x * 24
      y = 6 * 36
    Hai.gvram.put(x, y, x + 23, y + 35, self.get_pattern())

# カーソルクラス
class Cursor:

  # クラス変数 - Sprite オブジェクト参照
  sprite = x68k.Sprite()

  # クラス変数 - パターン定義
  cursor_pattern = bytes([0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11,
                          0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11,
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,

                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,

                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,

                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 ])

  # クラス変数 - パレット定義
  cursor_palette = ( 0b11100_11100_10000_0 )

  def __init__(self):

    # スプライト初期化
    Cursor.sprite.init()
    Cursor.sprite.clr()
    Cursor.sprite.defcg(0, self.cursor_pattern, 1)
    Cursor.sprite.palet(1, self.cursor_palette, 1)
    Cursor.sprite.disp()

    # 位置 0-12 ... 手牌の下  13: ツモ牌の下 
    self.position = 13

  # カーソル表示 (スプライト)
  #@micropython.viper
  def scroll(self):
    if self.position == 13:
      x = 16 + 4 + 4 * 24 + 13 * 24 + 4
    else:
      x = 16 + 4 + 4 * 24 + self.position * 24
    Cursor.sprite.set(0, x, 488, (1 << 8) | 0, 3, True)

  # カーソル左移動
  #@micropython.viper
  def move_left(self):
    self.position = ( self.position - 1 + 14 ) % 14
    self.scroll()

  # カーソル右移動
  #@micropython.viper
  def move_right(self):
    self.position = ( self.position + 1 ) % 14
    self.scroll()

# ゲームクラス
class Game:

  # '〇' '一' '二' '三' '四' '五' '六' '七' '八' '九'
  sjis_suji = bytes([ 0x81, 0x5a, 0x88, 0xea, 0x83, 0x6a, 0x8e, 0x4f, 0x8e, 0x6c, 
                      0x8c, 0xdc, 0x98, 0x5a, 0x8e, 0xb5, 0x94, 0xaa, 0x8b, 0xe3 ])

  # '東'
  sjis_ton = bytes([ 0x93, 0x8c ])

  # '南'
  sjis_nan = bytes([ 0x93, 0xec ])

  # '西'
  sjis_sha = bytes([ 0x90, 0xbc ])

  # '北'
  sjis_pei = bytes([ 0x96, 0x6b ])

  # '家'
  sjis_cha = bytes([ 0x89, 0xc6 ])

  # '親'
  sjis_oya = bytes([ 0x90, 0x65 ])

  # '局'
  sjis_kyoku = bytes([ 0x8b, 0xc7 ])

  # '本' '場'
  sjis_honba = bytes([ 0x96, 0x7b, 0x8f, 0xea ])

  # '点'
  sjis_ten = bytes([ 0x93, 0x5f ])

  # コンストラクタ
  def __init__(self):

    # 東風戦のみ 0:東一局  1:東ニ局  2:東三局  3:東四局(オーラス)
    self.kyoku:int = 0          

    # 積み棒の本数
    self.num_tsumibo:int = 0    

    # 0:自分が親 1:COMPUTERが親
    self.oya:int = random.randint(0,1)

    # 自分の風 0:東家 1:南家 2:西家 3:北家    
    self.kaze_player:int = 0 if self.oya == 1 else 2
    self.kaze_computer:int = 0 if self.oya == 0 else 2

    # 点数 25000点持ち30000点返し
    self.score_player:int = 25000
    self.score_computer:int = 25000

  # 雀卓クリア
  @micropython.viper
  def clear_jantaku(self):
    x68k.dos(x68k.d.CONCTRL,pack('2h',10,2))
    x68k.iocs(x68k.i.FILL,a1=pack('5h',0,0,511,511,0b01000_00011_00011_1))

  # 局名をSJISバイト列で返す
  #@micropython.viper
  def get_kyoku_sjis_bytes(self):
    return Game.sjis_ton + Game.sjis_suji[ self.kyoku * 2 + 2 : self.kyoku * 2 + 4 ] + Game.sjis_kyoku

  # 本場をSJISバイト列で返す
  #@micropython.viper
  def get_honba_sjis_bytes(self):
    return Game.sjis_suji[ self.num_tsumibo * 2 : self.num_tsumibo * 2 + 2 ] + Game.sjis_honba

  # 局・本場情報表示
  #@micropython.viper
  def print_kyoku_honba(self, x=32, y=13):
    if self.num_tsumibo > 0:
      s = f"\x1b[{y};{x}H".encode() + self.get_kyoku_sjis_bytes() + b" " + self.get_honba_sjis_bytes()
    else:
      s = f"\x1b[{y};{x}H".encode() + self.get_kyoku_sjis_bytes()
    x68k.dos(x68k.d.CONCTRL,pack('hl',1,addressof(s)))  

  # 風・スコア・親情報表示
  #@micropython.viper
  def print_scores(self):
    kp = Game.sjis_ton + Game.sjis_cha if self.kaze_player == 0 else Game.sjis_sha + Game.sjis_cha
    kc = Game.sjis_ton + Game.sjis_cha if self.kaze_computer == 0 else Game.sjis_sha + Game.sjis_cha
    if self.oya:
      kp += b' ' + Game.sjis_oya
    else:
      kc += b' ' + Game.sjis_oya
    s = f"\x1b[1;1HCOMPUTER {self.score_computer}".encode() + Game.sjis_ten + b' ' + kc + \
        f"\x1b[31;1HPLAYER {self.score_player}".encode() + Game.sjis_ten + b' ' + kp 
    x68k.dos(x68k.d.CONCTRL,pack('hl',1,addressof(s)))

  # 牌セット取得
  def get_hais(self, hai_file_name):

    # 牌画像データ読み込み (起牌 7+3*9+3種 + 背面 1種 + 倒牌 7+3*9+3種)
    hai_image = bytearray()
    with open(hai_file_name,"rb") as f:
      while True:
        h = f.read()
        if len(h) == 0:
          break
        hai_image.extend(h)

    # パターン登録
    #  起牌(37) 字牌(7) + 萬子(9) + 筒子(9) + 索子(9) + 赤5(3)
    #  背面(1)
    #  倒牌(37) 字牌(7) + 萬子(9) + 筒子(9) + 索子(9) + 赤5(3)
    patterns = []
    for i in range( 7 + 9 * 3 + 3 + 1 + 7 + 9 * 3 + 3):    
      patterns.append(bytes(hai_image[ 24 * 36 * 2 * i : 24 * 36 * 2 * ( i + 1 ) ]))
    Hai.patterns = patterns

    # 牌インスタンス作成 字牌(7) + 萬子(9) + 筒子(9) + 索子(9) 
    hais = []
    for i in range(34*4):
      t = i % 34
      h = Hai(i, t)
      hais.append(h)

    return hais

  # 洗牌
  #@micropython.viper
  def shuffle_hais(self, hais):
    for i in range(len(hais) * 8):
      a = random.randrange(0,len(hais)-1)
      b = random.randrange(0,len(hais)-1)
      c = hais[a]
      hais[a] = hais[b]
      hais[b] = c

  # カーソル取得
  def get_cursor(self):
    return Cursor()

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

  # title credit
  print("\x1b[1mMicro Mahjong PRO-68K\x1b[m for MicroPython X680x0")
  print(f"version {VERSION} by tantan\n")

  # ゲームインスタンス作成
  game = Game()

  # 牌パターンデータ読み込み
  print("Now loading...")
  hais = game.get_hais("hai.dat")

  # カーソルインスタンス取得
  cursor = game.get_cursor()

  # 雀卓クリア
  game.clear_jantaku()

  # 局・本場情報表示
  game.print_kyoku_honba()

  # スコア・親報表示
  game.print_scores()

  # 洗牌
  game.shuffle_hais(hais)

  # 王牌
  for i,h in enumerate(reversed(hais[-14:])):
    x68k.vsync()
    h.hai_status = 2    # 背面
    h.put(2,i//2)

  # ドラ表示牌
  time.sleep(0.5)
  x68k.vsync()
  hais[-5].hai_status = 0
  hais[-5].put(2,2)

  # 相手の牌ならべる
  for i,h in enumerate(hais[13:26]):
    for v in range(3):
      x68k.vsync()
    h.hai_status = 2    # 背面
    h.put(0,i)

  # 自分の牌ならべる
  for i,h in enumerate(hais[0:13]):
    for v in range(3):
      x68k.vsync()
    h.hai_status = 0    # 起牌
    h.put(1,i)

  # 一度伏せて
  for i,h in enumerate(hais[0:13]):
    for v in range(3):
      x68k.vsync()
    h.hai_status = 2    # 背面
    h.put(1,i)

  # 理牌
  for i,h in enumerate(sorted(hais[0:13],key=lambda h: h.hai_type)):
    for v in range(3):
      x68k.vsync()
    h.hai_status = 0
    h.put(1,i)

  # ツモ牌
  h = hais[26]
  h.hai_status = 0
  h.put(1,13)

  # カーソル表示
  cursor.scroll()

  # メインループ
  while True:

    # check left and right keys 
    if x68k.iocs(x68k.i.B_KEYSNS):
      scan_code = ( x68k.iocs(x68k.i.B_KEYINP) >> 8 ) & 0x7f
      if scan_code == 0x01:       # esc key
        break
      elif scan_code == 0x3b:     # left key
        cursor.move_left()
      elif scan_code == 0x3d:     # right key
        cursor.move_right()

  # flush key buffer
  x68k.dos(x68k.d.KFLUSH,pack('h',0))  

  # resume function key display mode
  x68k.dos(x68k.d.CONCTRL,pack('hh',14,funckey_mode))

  # cursor on
  x68k.curon()

if __name__ == "__main__":
  main()