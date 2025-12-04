from machine import Pin, TouchPad, PWM
import time
import dht

# ------------------------------
# DHT 感測器
# ------------------------------
sensor = dht.DHT11(Pin(4))

# ------------------------------
# LED 指示燈
# ------------------------------
red = Pin(19, Pin.OUT)
yellow = Pin(21, Pin.OUT)
green = Pin(22, Pin.OUT)

# ------------------------------
# 蜂鳴器 (PWM)
# ------------------------------
buzzer = PWM(Pin(23))
buzzer.freq(2000)
buzzer.duty(0)

# ------------------------------
# TouchPad（觸控切換）
# ------------------------------
touch_toggle = TouchPad(Pin(13))  # 切換警報開/關
touch_pause = TouchPad(Pin(12))

# 閾值
TOUCH_THRESHOLD_TOGGLE = 300
TOUCH_THRESHOLD_PAUSE = 300

# 警報狀態（False = 預設關閉）
alarm_enabled = False

# 暫停功能（True = 15 秒內蜂鳴器不會響）
alarm_pause = False
pause_until = 0    # 恢復時間

# 防抖
last_touch_time_toggle = 0
last_touch_time_pause = 0

# 防止開機誤觸（前 2 秒忽略觸控）
boot_time = time.ticks_ms()
TOUCH_BLOCK_MS = 2000


# ------------------------------
# 蜂鳴器功能
# ------------------------------
def beep_once():
    buzzer.duty(800)
    time.sleep(0.2)
    buzzer.duty(0)
    time.sleep(0.1)


def warning_beep():
    if alarm_pause:
        return
    for _ in range(3):
    	buzzer.duty(800)
    	time.sleep(0.15)
    	buzzer.duty(0)
    	time.sleep(0.1)


# ------------------------------
# LED 控制
# ------------------------------
def set_led(r, y, g):
    red.value(r)
    yellow.value(y)
    green.value(g)


# ------------------------------
# 觸控：切換警報開/關（Pin13）
# ------------------------------
def read_touch_toggle():
    global alarm_enabled, last_touch_time_toggle

    now = time.ticks_ms()

    # 開機前 2 秒忽略觸控
    if time.ticks_diff(now, boot_time) < TOUCH_BLOCK_MS:
        return

    t = touch_toggle.read()

    # 防抖（800ms）
    if t < TOUCH_THRESHOLD_TOGGLE and time.ticks_diff(now, last_touch_time_toggle) > 800:
        alarm_enabled = not alarm_enabled
        last_touch_time_toggle = now

        print("警報開啟" if alarm_enabled else "警報關閉")
        beep_once()


# ------------------------------
# 觸控：暫停警報 15 秒（Pin12）
# ------------------------------
def read_touch_pause():
    global alarm_pause, pause_until, last_touch_time_pause

    now = time.ticks_ms()

    if time.ticks_diff(now, boot_time) < TOUCH_BLOCK_MS:
        return

    t = touch_pause.read()

    if t < TOUCH_THRESHOLD_PAUSE and time.ticks_diff(now, last_touch_time_pause) > 800:
        alarm_pause = True
        pause_until = now + 15000
        last_touch_time_pause = now
        print("警報暫停 15 秒")
        beep_once()


# ------------------------------
# 檢查是否恢復警報
# ------------------------------
def check_pause_recovery():
    global alarm_pause

    if alarm_pause and time.ticks_ms() > pause_until:
        alarm_pause = False
        print("警報恢復")
        beep_once()


# ------------------------------
# 主迴圈
# ------------------------------
while True:
    read_touch_toggle()
    read_touch_pause()
    check_pause_recovery()

    try:
        sensor.measure()
        temp = sensor.temperature()
        humi = sensor.humidity()

        print("溫度:", temp, "濕度:", humi)

        set_led(0, 0, 0)

        warning = False

        # ------ 溫度異常 ------
        if temp > 30:
            warning = True
            red.value(1)
            if alarm_enabled and not alarm_pause:
                warning_beep()

        # ------ 濕度異常 ------
        elif humi > 80:
            warning = True
            yellow.value(1)

        # ------ 正常狀態 ------
        if not warning:
            green.value(1)

    except OSError:
        print("DHT 讀取失敗")

    time.sleep(2)