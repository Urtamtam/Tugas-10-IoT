
import random
import time

import paho.mqtt.client as mqtt

NIM = "2410020014"          
BROKER = "localhost"
PORT = 1883
INTERVAL = 3             

TOPIC_SUHU = f"iot/{NIM}/sensor/suhu"
TOPIC_RELAY = f"iot/{NIM}/aktuator/relay"
TOPIC_PWM = f"iot/{NIM}/aktuator/pwm"

GPIO_RELAY = 26
GPIO_LED = 2


sudah_terhubung = False  


def on_connect(client, userdata, flags, reason_code, properties):
    global sudah_terhubung
    if reason_code.is_failure:
        print(f"Gagal terhubung ke broker: {reason_code}")
        return
    # Subscribe ulang di setiap (re)connect agar tidak hilang, tetapi tanpa mencetak ulang
    client.subscribe([(TOPIC_RELAY, 0), (TOPIC_PWM, 0)])
    if not sudah_terhubung:
        sudah_terhubung = True
        print(f"Terhubung ke broker (kode: {reason_code})")
        print(f"Subscribe: {TOPIC_RELAY} dan {TOPIC_PWM}")


def on_message(client, userdata, msg):
    payload = msg.payload.decode().strip()
    if msg.topic == TOPIC_RELAY:
        nilai = payload.upper()
        if nilai == "ON":
            print(f"← [GPIO {GPIO_RELAY}] RELAY MENYALA (HIGH)")
        elif nilai == "OFF":
            print(f"← [GPIO {GPIO_RELAY}] RELAY MATI (LOW)")
        else:
            print(f"← Perintah relay tidak dikenal: {payload!r}")
    elif msg.topic == TOPIC_PWM:
        try:
            duty = max(0, min(255, int(float(payload))))
        except ValueError:
            print(f"← Nilai PWM tidak valid: {payload!r}")
            return
        persen = round(duty / 255 * 100)
        bar = "#" * (persen // 5)
        print(f"← [GPIO {GPIO_LED}] PWM = {duty}/255 ({persen}%) |{bar:<20}|")


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"ESP32-{NIM}")
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, 60)
client.loop_start()

print("Simulator ESP32 berjalan... Ctrl+C untuk stop")
suhu = 28.0
try:
    while True:
        suhu = max(24.0, min(36.0, suhu + random.uniform(-0.6, 0.6) + (28.0 - suhu) * 0.05))
        client.publish(TOPIC_SUHU, f"{suhu:.1f}")
        print(f"→ Suhu {suhu:.1f} °C  ke {TOPIC_SUHU}")
        time.sleep(INTERVAL)
except KeyboardInterrupt:
    pass
finally:
    client.loop_stop()
    client.disconnect()
