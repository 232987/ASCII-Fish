import time
import gc
import config
import tank
from machine import Pin
from screen_esp32 import ESP32Screen

screen = ESP32Screen()
t = tank.Tank()
btn = Pin(config.PIN_BTN, Pin.IN, Pin.PULL_UP) if config.PIN_BTN is not None else None
btn_prev = 1

last = time.ticks_ms()
fps_t = last
frames = 0
work_sum = 0
work_max = 0
gc_every = config.GC_EVERY

while True:
    now = time.ticks_ms()
    dt = time.ticks_diff(now, last)
    last = now

    if btn is not None:
        v = btn.value()
        if v == 0 and btn_prev == 1:
            t.drop_food()
        btn_prev = v

    t.step(dt)
    t.draw(screen)
    screen.show()

    frames += 1
    spent = time.ticks_diff(time.ticks_ms(), now)
    work_sum += spent
    if spent > work_max:
        work_max = spent
    if config.SHOW_FPS and time.ticks_diff(now, fps_t) >= 2000:
        print("fps:", frames * 1000 // time.ticks_diff(now, fps_t), " 每帧平均", work_sum // frames, "ms 最慢", work_max, "ms")
        frames = 0
        work_sum = 0
        work_max = 0
        fps_t = now
    if gc_every and frames % gc_every == 0:
        gc.collect()
        spent = time.ticks_diff(time.ticks_ms(), now)
    if spent < config.FRAME_MS:
        time.sleep_ms(config.FRAME_MS - spent)
