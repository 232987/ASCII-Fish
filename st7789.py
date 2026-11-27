import time
from machine import Pin, SPI
import config

_SWRESET = 0x01
_SLPOUT = 0x11
_NORON = 0x13
_INVON = 0x21
_DISPON = 0x29
_MADCTL = 0x36
_COLMOD = 0x3A
_FRCTRL2 = 0xC6

_FR_TABLE = ((119, 0x00), (111, 0x01), (105, 0x02), (99, 0x03), (94, 0x04), (90, 0x05),
             (86, 0x06), (82, 0x07), (78, 0x08), (75, 0x09), (72, 0x0A), (69, 0x0B),
             (67, 0x0C), (64, 0x0D), (62, 0x0E), (60, 0x0F))


_B_CASET = b"\x2a"
_B_RASET = b"\x2b"
_B_RAMWR = b"\x2c"


class ST7789:
    def __init__(self):
        c = config
        self.spi = SPI(1, baudrate=c.SPI_BAUD, polarity=c.SPI_POLARITY, phase=c.SPI_PHASE,
                       sck=Pin(c.PIN_SCK), mosi=Pin(c.PIN_MOSI))
        self.dc = Pin(c.PIN_DC, Pin.OUT, value=0)
        self.cs = Pin(c.PIN_CS, Pin.OUT, value=1) if c.PIN_CS is not None else None
        self.rst = Pin(c.PIN_RST, Pin.OUT, value=1) if c.PIN_RST is not None else None
        self.xo = c.X_OFFSET
        self.yo = c.Y_OFFSET
        mx = getattr(c, "MIRROR_X", False)
        my = getattr(c, "MIRROR_Y", False)
        self.mad = (0x08 if c.BGR else 0x00) | (0x40 if mx else 0x00) | (0x80 if my else 0x00)
        if my:
            self.yo += 80
        self._ca = bytearray(4)
        self._ra = bytearray(4)
        self._reset()
        self._init()
        self._backlight(c.BL_LEVEL)

    def _reset(self):
        if self.rst is not None:
            self.rst.value(1)
            time.sleep_ms(10)
            self.rst.value(0)
            time.sleep_ms(20)
            self.rst.value(1)
            time.sleep_ms(120)

    def _cmd(self, cmd, data=None):
        if self.cs is not None:
            self.cs.value(0)
        self.dc.value(0)
        self.spi.write(bytes([cmd]))
        if data is not None:
            self.dc.value(1)
            self.spi.write(data)
        if self.cs is not None:
            self.cs.value(1)

    def _init(self):
        self._cmd(_SWRESET)
        time.sleep_ms(150)
        self._cmd(_SLPOUT)
        time.sleep_ms(120)
        self._cmd(_COLMOD, b"\x55")
        self._cmd(_MADCTL, bytes([self.mad]))
        hz = config.REFRESH_HZ
        if hz and hz != 60:
            best = _FR_TABLE[0]
            for row in _FR_TABLE:
                if abs(row[0] - hz) < abs(best[0] - hz):
                    best = row
            self._cmd(_FRCTRL2, bytes([best[1]]))
        if config.INVERT:
            self._cmd(_INVON)
        self._cmd(_NORON)
        time.sleep_ms(10)
        self._cmd(_DISPON)
        time.sleep_ms(120)

    def _backlight(self, level):
        pin = config.PIN_BL
        if pin is None:
            return
        try:
            from machine import PWM
            self.pwm = PWM(Pin(pin), freq=1000, duty_u16=int(65535 * level / 100))
        except Exception:
            Pin(pin, Pin.OUT, value=1 if level > 0 else 0)

    def blit(self, x, y, w, h, data):
        x0 = x + self.xo
        x1 = x0 + w - 1
        y0 = y + self.yo
        y1 = y0 + h - 1
        ca = self._ca
        ca[0] = x0 >> 8
        ca[1] = x0 & 255
        ca[2] = x1 >> 8
        ca[3] = x1 & 255
        ra = self._ra
        ra[0] = y0 >> 8
        ra[1] = y0 & 255
        ra[2] = y1 >> 8
        ra[3] = y1 & 255
        cs = self.cs
        dc = self.dc
        spi = self.spi
        if cs is not None:
            cs.value(0)
        dc.value(0)
        spi.write(_B_CASET)
        dc.value(1)
        spi.write(ca)
        if cs is not None:
            cs.value(1)
            cs.value(0)
        dc.value(0)
        spi.write(_B_RASET)
        dc.value(1)
        spi.write(ra)
        if cs is not None:
            cs.value(1)
            cs.value(0)
        dc.value(0)
        spi.write(_B_RAMWR)
        if cs is not None:
            cs.value(1)
            cs.value(0)
        dc.value(1)
        spi.write(data)
        if cs is not None:
            cs.value(1)
