import time
import config
from st7789 import ST7789

d = ST7789()
W = config.SCREEN_W
H = config.SCREEN_H


def px(color):
    r, g, b = color
    c = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    return bytes([c >> 8, c & 255])


def fill(color):
    row = px(color) * W
    for y in range(0, H, 8):
        d.blit(0, y, W, 8, row * 8)


for name, col in (("红", (255, 0, 0)), ("绿", (0, 255, 0)), ("蓝", (0, 0, 255)),
                  ("白", (255, 255, 255)), ("黑", (0, 0, 0))):
    print("现在应该是纯", name, "色")
    fill(col)
    time.sleep(1.5)


print("现在应该是黑底，四条边各有一条白线，贴着屏幕边缘")
white = px((255, 255, 255))
d.blit(0, 0, W, 1, white * W)
d.blit(0, H - 1, W, 1, white * W)
d.blit(0, 0, 1, H, white * H)
d.blit(W - 1, 0, 1, H, white * H)
print("检查：")
print("  颜色像底片、黑变白  -> config.py 里把 INVERT 改成 False")
print("  红蓝互换            -> 把 BGR 改成 True")
print("  白线没贴边或缺一边   -> 调 X_OFFSET / Y_OFFSET")
print("  花屏或闪             -> 把 SPI_BAUD 调小，检查接线")
