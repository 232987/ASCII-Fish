import math
import random
import config


def rnd(a, b):
    return a + (b - a) * random.random()


FISH_RIGHT = "><(((o>"
FISH_LEFT = "<o)))><"
FISH_N = len(FISH_RIGHT)
FISH_W = FISH_N * config.CELL_W
WORDS = config.WORDS
WORD_LIFE = config.WORD_FADE_IN + config.WORD_GLOW + config.WORD_SETTLE + config.WORD_FADE_OUT


def lerp_color(a, b, u):
    n = config.WORD_STEPS
    u = int(u * n + 0.5) / n
    if u < 0:
        u = 0
    if u > 1:
        u = 1
    return (int(a[0] + (b[0] - a[0]) * u + 0.5),
            int(a[1] + (b[1] - a[1]) * u + 0.5),
            int(a[2] + (b[2] - a[2]) * u + 0.5))


def word_look(age):
    n1 = config.WORD_FADE_IN
    n2 = n1 + config.WORD_GLOW
    n3 = n2 + config.WORD_SETTLE
    if age < n1:
        return lerp_color((0, 0, 0), config.COLOR_WORD_BRIGHT, age / n1), None
    if age < n2:
        glow = config.COLOR_WORD_GLOW if config.WORD_GLOW_ON else None
        return config.COLOR_WORD_BRIGHT, glow
    if age < n3:
        return lerp_color(config.COLOR_WORD_BRIGHT, config.COLOR_WORD, (age - n2) / config.WORD_SETTLE), None
    u = (age - n3) / config.WORD_FADE_OUT
    return lerp_color(config.COLOR_WORD, config.COLOR_WORD_END, u), None


class Fish:
    def __init__(self):
        self.x = rnd(10, config.W - FISH_W - 10)
        self.y = rnd(config.FISH_Y[0], config.FISH_Y[1])
        self.y_goal = self.y
        self.dir = 1 if random.random() < 0.5 else -1
        self.next_dir = self.dir
        self.v = 0.0
        self.vy = 0.0
        self.sv = 0.0
        self.speed_goal = 0.0
        self.mode = "idle"
        self.timer = rnd(30, 90)
        self.wag = rnd(0, 6)
        self.phase = rnd(0, 6)
        self.just_ate = False
        self.eaten_at = (0, 0)
        self.chew = 0.0
        self.munch_t = 0.0
        self.target = None
        self.unseen = 0.0
        self.chase_t = 0.0

    def mouth(self):
        mx = self.x + FISH_W if self.dir > 0 else self.x
        return mx, self.y + 4

    def clamp(self):
        if self.x < 0:
            self.x = 0
        if self.x > config.W - FISH_W:
            self.x = config.W - FISH_W

    def update(self, frame, foods, k):
        self.just_ate = False
        y_before = self.y
        if self.munch_t > 0:
            self.munch_t -= k
        target = self.target
        if target is not None:
            alive = False
            for g in foods:
                if g is target:
                    alive = True
                    break
            self.chase_t += k
            if not alive or self.chase_t > 400:
                target = None
        if target is None:
            self.chase_t = 0.0
            if foods:
                r2 = config.FOOD_CHASE_Y ** 2
                cx = self.x + FISH_W / 2
                cy = self.y + 4
                best = 1e9
                far_best = 1e9
                far = None
                for f in foods:
                    if f[1] < 2:
                        continue
                    d = (f[0] - cx) ** 2 + (f[1] - cy) ** 2
                    if d < r2:
                        if d < best:
                            best = d
                            target = f
                    elif d < far_best:
                        far_best = d
                        far = f
                if target is None and far is not None:
                    self.unseen += k
                    if self.unseen > 240:
                        target = far
                if target is not None:
                    self.unseen = 0.0
            else:
                self.unseen = 0.0
        self.target = target
        if target is not None:
            self.feed(target, foods, k)
        else:
            self.chew = 0.0
            if self.mode == "feed":
                self.mode = "idle"
                self.speed_goal = 0.0
                self.timer = rnd(20, 60)
            self.wander(k)
        self.vy += (abs(self.y - y_before) / k - self.vy) * 0.3
        self.sv = math.sqrt(self.v * self.v + self.vy * self.vy)
        self.wag += (0.10 + 0.22 * min(self.sv, 1.4)) * k * config.WAG_SPEED

    def feed(self, f, foods, k):
        self.mode = "feed"
        spd = config.FEED_SPEED
        fx = f[0]
        d_r = fx - (self.x + FISH_W)
        d_l = self.x - fx
        if self.dir > 0 and -6 <= d_r <= 6:
            want = 1
            step = d_r if d_r > 0 else 0.0
        elif self.dir < 0 and -6 <= d_l <= 6:
            want = -1
            step = -d_l if d_l > 0 else 0.0
        elif d_r > 2:
            want = 1
            step = d_r
        elif d_l > 2:
            want = -1
            step = -d_l
        else:
            over_r = fx - self.x
            over_l = self.x + FISH_W - fx
            ok_r = fx <= config.W - FISH_W - 2
            ok_l = fx >= FISH_W + 2
            if ok_r and not ok_l:
                want = 1
            elif ok_l and not ok_r:
                want = -1
            elif over_r + 4 < over_l:
                want = 1
            elif over_l + 4 < over_r:
                want = -1
            else:
                want = self.dir
            step = want * spd
        self.dir = want
        self.next_dir = want
        lim = spd
        chewing = self.chew > 0
        if chewing:
            self.chew -= k
            lim = 0.25
        if step > lim:
            step = lim
        elif step < -lim:
            step = -lim
        self.x += step * k
        self.v = abs(step)
        ty = f[1] - 4
        if ty < 2:
            ty = 2
        if ty > config.H - 12:
            ty = config.H - 12
        vy = (ty - self.y) * 0.08
        if not chewing:
            if vy > spd:
                vy = spd
            elif vy < -spd:
                vy = -spd
        self.y += vy * k
        self.clamp()
        mx, my = self.mouth()
        eaten = 0
        for g in list(foods):
            if eaten < 2 and (g[0] - mx) ** 2 + (g[1] - my) ** 2 < 100:
                foods.remove(g)
                eaten += 1
                self.eaten_at = (g[0], g[1])
        if eaten:
            self.just_ate = True
            self.chew = 8.0
            self.munch_t = config.MUNCH_FRAMES

    def decide(self):
        if self.mode == "swim" and random.random() < config.FISH_STOP_CHANCE:
            self.mode = "idle"
            self.speed_goal = 0.0
            self.timer = rnd(config.FISH_IDLE_TIME[0], config.FISH_IDLE_TIME[1])
        else:
            self.mode = "swim"
            self.speed_goal = rnd(config.FISH_SPEED[0], config.FISH_SPEED[1])
            self.timer = rnd(config.FISH_SWIM_TIME[0], config.FISH_SWIM_TIME[1])
            if random.random() < config.FISH_TURN_CHANCE:
                self.next_dir = -self.dir
        if random.random() < config.FISH_DEPTH_CHANCE:
            if random.random() < config.FISH_FAR_CHANCE:
                if random.random() < 0.5:
                    up = config.FISH_UP
                    self.y_goal = rnd(up[0], up[1])
                else:
                    dn = config.FISH_DOWN
                    self.y_goal = rnd(dn[0], dn[1])
            else:
                self.y_goal = rnd(config.FISH_Y[0], config.FISH_Y[1])

    def wander(self, k):
        self.timer -= k
        if self.timer <= 0:
            self.decide()
        m = config.FISH_WALL_MARGIN
        if self.dir > 0 and self.x > config.W - FISH_W - m:
            self.next_dir = -1
        elif self.dir < 0 and self.x < m:
            self.next_dir = 1
        want = self.speed_goal
        rate = 0.05
        if self.next_dir != self.dir:
            want = 0.0
            rate = 0.12
            if self.v < 0.12:
                self.dir = self.next_dir
                want = self.speed_goal
        self.v += (want - self.v) * rate * k
        self.x += self.dir * self.v * k
        self.y += (self.y_goal - self.y) * 0.02 * k
        self.clamp()

    def draw(self, screen, frame):
        s = FISH_RIGHT if self.dir > 0 else FISH_LEFT
        gap = 0.0
        if self.munch_t > 0:
            done = config.MUNCH_FRAMES - self.munch_t
            if int(done / config.MOUTH_PERIOD) % 2 == 0:
                if self.dir > 0:
                    s = s[:-1] + "<"
                else:
                    s = ">" + s[1:]
            gap = config.SWELL * math.sin(math.pi * done / config.MUNCH_FRAMES)
        amp = (0.9 + 1.6 * min(self.sv, 1.4) / 1.4) * config.WAG_AMP
        bob = math.sin(frame * 0.05 + self.phase) * 0.8 if self.mode == "idle" else 0
        bx = self.x - gap * (FISH_N - 1) / 2
        by = self.y + bob
        for i in range(FISH_N):
            h = (FISH_N - 1 - i) if self.dir > 0 else i
            w = 0.15 + 0.85 * h / (FISH_N - 1)
            off = math.sin(self.wag - h * 0.9) * amp * w
            screen.text(s[i], bx + i * (config.CELL_W + gap), by + off, config.COLOR_FISH)


class Tank:
    def __init__(self):
        self.frame = 0
        self.k = config.FRAME_MS / 33.0
        self.fish = [Fish() for _ in range(config.FISH_COUNT)]
        self.weeds = []
        for wx in config.WEED_X:
            self.weeds.append([wx, random.randint(2, 3), rnd(0, 6)])
        self.bubbles = []
        self.foods = []
        self.words = []
        self.word_cd = 0.0

    def weed_sway(self, w, i):
        return math.sin(self.frame * 0.08 + w[2] + i * 0.5) * (1 + i * 0.4)

    def add_bubble(self, x, y, big=False):
        size = "1" if random.random() < config.BUBBLE_SMALL_RATIO else "2"
        if big:
            stop = rnd(6, 34)
        else:
            stop = rnd(5, 16)
        self.bubbles.append([x, y, rnd(0.15, 0.4), rnd(0, 6), size, None, stop])

    def drop_food(self, x=None):
        if x is None:
            x = rnd(24, config.W - 24)
        n = config.FOOD_FLAKES
        if isinstance(n, tuple):
            n = int(rnd(n[0], n[1] + 1))
        for _ in range(n):
            r = random.random()
            kind = "0" if r < 0.6 else ("*" if r < 0.85 else ".")
            fx = x + rnd(-22, 22)
            if fx < 4:
                fx = 4
            if fx > config.W - 8:
                fx = config.W - 8
            self.foods.append([fx, rnd(-30, -2), 0, rnd(-0.4, 0.4), rnd(config.FOOD_SINK[0], config.FOOD_SINK[1]), kind])
        nb = config.DROP_BUBBLES
        if isinstance(nb, tuple):
            nb = int(rnd(nb[0], nb[1] + 1))
        for _ in range(nb):
            self.add_bubble(x + rnd(-18, 18), rnd(4, 20), True)

    def step(self, ms=None):
        if ms is None:
            k = self.k
        else:
            k = ms / 33.0
            if k > 3.0:
                k = 3.0
            if k < 0.05:
                k = 0.05
        self.frame += k
        if self.weeds and random.random() < config.WEED_BUBBLE_CHANCE * k:
            w = random.choice(self.weeds)
            bx = w[0] + self.weed_sway(w, w[1] - 1) + 1
            by = config.H - config.CELL_H * w[1] - 2
            self.add_bubble(bx, by)
        alive = []
        for b in self.bubbles:
            if b[5] is None:
                b[1] -= b[2] * k
                if b[1] <= b[6]:
                    b[1] = b[6]
                    b[5] = rnd(60, 200)
            else:
                b[5] -= k
            if b[5] is None or b[5] > 0:
                alive.append(b)
        self.bubbles = alive
        for f in self.foods:
            f[2] += k
            f[0] += f[3] * k
            f[3] *= 1.0 - 0.01 * k
            if f[0] < 2:
                f[0] = 2
                f[3] = abs(f[3])
            elif f[0] > config.W - 6:
                f[0] = config.W - 6
                f[3] = -abs(f[3])
            if f[1] < config.H - 16:
                f[1] += f[4] * k
        self.foods = [f for f in self.foods if f[2] < config.FOOD_LIFETIME]
        for fi in self.fish:
            fi.update(self.frame, self.foods, k)
            if fi.just_ate:
                self.munch(fi)
            elif fi.mode != "feed" and random.random() < config.MOUTH_BUBBLE_CHANCE * k:
                self.spit(fi)
        if self.word_cd > 0:
            self.word_cd -= k
        for wd in self.words:
            wd[3] += k
            wd[1] -= 0.1 * k
        self.words = [wd for wd in self.words if wd[3] < WORD_LIFE]

    def spit(self, fi):
        mx, my = fi.mouth()
        self.add_bubble(mx + (1 if fi.dir > 0 else -5), my - 2)

    def munch(self, fi):
        ex, ey = fi.eaten_at
        if random.random() < 0.6:
            self.spit(fi)
        if self.word_cd > 0 or len(self.words) >= 3:
            return
        shown = [o[2] for o in self.words]
        choices = [x for x in WORDS if x not in shown]
        if not choices:
            return
        text = random.choice(choices)
        w = len(text) * 4
        for _ in range(5):
            wx = ex - w / 2 + rnd(-10, 10)
            wy = ey - 10 + rnd(-6, 4)
            if wx < 0:
                wx = 0
            if wx > config.W - w:
                wx = config.W - w
            if wy < 0:
                wy = 0
            ok = True
            for o in self.words:
                if wx < o[0] + len(o[2]) * 4 + 2 and o[0] < wx + w + 2 and abs(wy - o[1]) < 8:
                    ok = False
                    break
            if ok:
                self.words.append([wx, wy, text, 0])
                self.word_cd = WORD_LIFE + config.WORD_GAP
                return

    def draw(self, screen):
        screen.clear()
        c = config.CELL_H
        for w in self.weeds:
            for i in range(w[1]):
                ch = ")" if i % 2 else "("
                screen.text(ch, w[0] + self.weed_sway(w, i), config.H - c * (i + 1), config.COLOR_WEED)
        for b in self.bubbles:
            bx = b[0] + math.sin(self.frame * 0.1 + b[3]) * 1.5
            screen.text(b[4], bx - 4, b[1] - 4, config.COLOR_BUBBLE, 2)
        for f in self.foods:
            screen.text(f[5], f[0], f[1], config.COLOR_FOOD, 1)
        for fi in self.fish:
            fi.draw(screen, self.frame)
        for wd in self.words:
            color, glow = word_look(wd[3])
            if glow is not None:
                g = config.WORD_GLOW_SPREAD
                for dx, dy in ((-g, 0), (g, 0), (0, -g), (0, g)):
                    screen.text(wd[2], wd[0] + dx, wd[1] + dy, glow, 1)
            screen.text(wd[2], wd[0], wd[1], color, 1)
