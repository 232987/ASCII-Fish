import config
from dirty import DirtyRenderer
from st7789 import ST7789


class ESP32Screen(DirtyRenderer):
    def __init__(self):
        DirtyRenderer.__init__(self, ST7789(), config.SCREEN_W, config.SCREEN_H)
