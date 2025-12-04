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
touch = TouchPad(Pin(13))

# TouchPad 閾值（開機後才校正）
TOUCH_THRESHOLD = 300

# 警報狀態（False = 預設關閉）
alarm_enabled = False

# 防抖動用
last_touch_time = 0

# 防止開機誤觸的時間（2 秒內不觸發）
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
# 讀取觸控
# ------------------------------
def read_touch():
    global alarm_enabled, last_touch_time

    now = time.ticks_ms()

    if time.ticks_diff(now, boot_time) < TOUCH_BLOCK_MS:
        return

    t = touch.read()

    # 噪音防抖動 (800ms)
    if t < TOUCH_THRESHOLD and time.ticks_diff(now, last_touch_time) > 800:
        alarm_enabled = not alarm_enabled
        last_touch_time = now

        print("警報開啟" if alarm_enabled else "警報關閉")
        beep_once()


# ------------------------------
# 主迴圈
# ------------------------------
while True:
    read_touch()

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
            if alarm_enabled:
                warning_beep()

        # ------ 濕度異常 ------
        elif humi > 90:
            warning = True
            yellow.value(1)

        # ------ 正常狀態 ------
        if not warning:
            green.value(1)

    except OSError:
        print("DHT 讀取失敗")

    time.sleep(2)
