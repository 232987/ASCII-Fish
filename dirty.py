import framebuf
import config
import glyphs

S = config.SCALE
BAND_PIXELS = 3072

SMOOTH = False
if config.SMOOTH_FONT and S == 2:
    try:
        import fontdata
        SMOOTH = fontdata.SCALE == S
    except ImportError:
        SMOOTH = False


def swap565(color):
    r, g, b = color
    c = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    return ((c & 0xFF) << 8) | (c >> 8)


class DirtyRenderer:
    def __init__(self, display, width, height):
        self.d = display
        self.w = width
        self.h = height
        self.items = []
        self.prev = None
        self.buf = bytearray(BAND_PIXELS * 2)
        self.cc = {}
        self.gfb = [{}, {}, {}]
        self.pal = {}
        self.cids = {}
        self.cols = [None]
        self.mv = memoryview(self.buf)
        self.fbs = {}
        self.gs = {}
        self.cwf = {}
        for f in (0, 1, 2):
            gw, gh = glyphs.size(f)
            self.gs[f] = (gw * S, gh * S)
            self.cwf[f] = gw
        self.tw = (width + 15) >> 4
        self.th = (height + 15) >> 4
        self.bins = [[] for _ in range(self.th)]

    def _glyph(self, font, ch):
        tab = self.gfb[font]
        g = tab.get(ch)
        if g is None:
            data = fontdata.GLYPHS.get((font, ch))
            if data is None:
                g = False
            else:
                gw, gh = fontdata.DIMS[font]
                g = framebuf.FrameBuffer(bytearray(data), gw, gh, framebuf.GS4_HMSB)
            tab[ch] = g
        return g

    def _palette(self, cid):
        p = self.pal.get(cid)
        if p is None:
            p = framebuf.FrameBuffer(bytearray(32), 16, 1, framebuf.RGB565)
            r, g, b = self.cols[cid]
            for i in range(16):
                p.pixel(i, 0, swap565((r * i // 15, g * i // 15, b * i // 15)))
            self.pal[cid] = p
        return p

    def clear(self):
        self.items = []

    def text(self, s, x, y, color, font=0):
        gs = self.gs[font]
        gw = gs[0]
        gh = gs[1]
        cw = self.cwf[font]
        cid = self.cids.get(color)
        if cid is None:
            cid = len(self.cols)
            self.cids[color] = cid
            self.cols.append(color)
        tab = self.gfb[font]
        items = self.items
        py = round(y * S)
        if py + gh <= 0 or py >= self.h:
            return
        for i in range(len(s)):
            ch = s[i]
            if ch == " ":
                continue
            if SMOOTH:
                g = tab.get(ch)
                if g is None:
                    g = self._glyph(font, ch)
                if not g:
                    continue
            elif not glyphs.pixels(font, ch):
                continue
            px = round((x + i * cw) * S)
            if px + gw <= 0 or px >= self.w:
                continue
            items.append((font, ch, px, py, cid))

    def show(self):
        new = self.items
        newset = set(new)
        w = self.w
        h = self.h
        tw = self.tw
        th = self.th
        rows = [0] * th
        if self.prev is None:
            full = (1 << tw) - 1
            for r in range(th):
                rows[r] = full
        else:
            gs = self.gs
            for it in self.prev ^ newset:
                gw, gh = gs[it[0]]
                x0 = it[2]
                y0 = it[3]
                x1 = x0 + gw
                y1 = y0 + gh
                if x0 < 0:
                    x0 = 0
                if y0 < 0:
                    y0 = 0
                if x1 > w:
                    x1 = w
                if y1 > h:
                    y1 = h
                if x1 <= x0 or y1 <= y0:
                    continue
                a = x0 >> 4
                b = (x1 - 1) >> 4
                m = (1 << (b + 1)) - (1 << a)
                for r in range(y0 >> 4, ((y1 - 1) >> 4) + 1):
                    rows[r] |= m
        self.prev = newset

        rects = []
        active = {}
        for r in range(th):
            m = rows[r]
            cur = {}
            x = 0
            while m:
                if m & 1:
                    s = x
                    while m & 1:
                        m >>= 1
                        x += 1
                    key = (s, x - 1)
                    cur[key] = active.get(key, r)
                else:
                    m >>= 1
                    x += 1
            for key in active:
                if key not in cur:
                    rects.append((key[0], active[key], key[1], r - 1))
            active = cur
        for key in active:
            rects.append((key[0], active[key], key[1], th - 1))
        if not rects:
            return

        bins = self.bins
        for b in bins:
            del b[:]
        gs = self.gs
        for i in range(len(new)):
            it = new[i]
            gh = gs[it[0]][1]
            y0 = it[3]
            y1 = y0 + gh
            if y0 < 0:
                y0 = 0
            if y1 > h:
                y1 = h
            if y1 <= y0:
                continue
            for r in range(y0 >> 4, ((y1 - 1) >> 4) + 1):
                bins[r].append(i)

        for rc in rects:
            ta, ra, tb, rb = rc
            x0 = ta << 4
            x1 = (tb + 1) << 4
            if x1 > w:
                x1 = w
            y0 = ra << 4
            y1 = (rb + 1) << 4
            if y1 > h:
                y1 = h
            seen = set()
            idx = []
            for r in range(ra, rb + 1):
                for i in bins[r]:
                    if i not in seen:
                        seen.add(i)
                        idx.append(i)
            idx.sort()
            sel = [new[i] for i in idx]
            self._region(x0, y0, x1, y1, sel)

    def _region(self, x0, y0, x1, y1, items):
        w = x1 - x0
        rows = BAND_PIXELS // w
        if rows < 1:
            rows = 1
        y = y0
        while y < y1:
            h = rows if y + rows <= y1 else y1 - y
            self._band(x0, y, w, h, items)
            y += h

    def _band(self, x, y, w, h, items):
        key = (w, h)
        fb = self.fbs.get(key)
        if fb is None:
            if len(self.fbs) > 40:
                self.fbs = {}
            fb = framebuf.FrameBuffer(self.buf, w, h, framebuf.RGB565)
            self.fbs[key] = fb
        fb.fill(0)
        gs = self.gs
        gfb = self.gfb
        pal = self.pal
        for it in items:
            px = it[2]
            py = it[3]
            g = gs[it[0]]
            if px < x + w and px + g[0] > x and py < y + h and py + g[1] > y:
                gx = px - x
                gy = py - y
                if SMOOTH:
                    p = pal.get(it[4])
                    if p is None:
                        p = self._palette(it[4])
                    fb.blit(gfb[it[0]][it[1]], gx, gy, 0, p)
                    continue
                c = self.cc.get(it[4])
                if c is None:
                    c = swap565(self.cols[it[4]])
                    self.cc[it[4]] = c
                for p in glyphs.pixels(it[0], it[1]):
                    fb.fill_rect(gx + p[0] * S, gy + p[1] * S, S, S, c)
        self.d.blit(x, y, w, h, self.mv[:w * h * 2])
