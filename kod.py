from machine import Pin, PWM, ADC
import time

# Servo motor ayarları
servo_pins = [14, 15, 12, 13]  # Servo motor pinleri
servos = {f"servo{i+1}": PWM(Pin(pin)) for i, pin in enumerate(servo_pins)}  # Servo nesneleri oluştur
for servo in servos.values():
    servo.freq(50)  # Servo frekansını 50 Hz olarak ayarla

# Buzzer ayarları
buzzer_pin = 18
buzzer = PWM(Pin(buzzer_pin))

# Buzzer melodisi çalma fonksiyonları
def play_buzzer_melody1():
    melody = [262, 294, 330, 349, 392, 440, 494, 523]  # Do, Re, Mi, Fa, Sol, La, Si, Do
    duration = 0.1  # Her nota için süre
    for note in melody:
        buzzer.freq(note)
        buzzer.duty_u16(1000)  # Buzzer sesini aç
        time.sleep(duration)
    buzzer.duty_u16(0)  # Buzzer sesini kapat

def play_buzzer_melody2():
    melody = [523, 494, 440, 392, 349, 330, 294, 262]  # Do, Si, La, Sol, Fa, Mi, Re, Do
    duration = 0.1  # Her nota için süre
    for note in melody:
        buzzer.freq(note)
        buzzer.duty_u16(1000)  # Buzzer sesini aç
        time.sleep(duration)
    buzzer.duty_u16(0)  # Buzzer sesini kapat

# Buzzer kısa bip fonksiyonu
def buzzer_beep():
    buzzer.freq(1000)  # Bip frekansı
    buzzer.duty_u16(1000)  # Buzzer sesini aç
    time.sleep(0.2)  # Bip süresi
    buzzer.duty_u16(0)  # Buzzer sesini kapat

# Servo pozisyon fonksiyonu
def set_servo_position(servo, angle):
    pulse_width = int((angle * 2.0 / 180 + 0.5) * 1000)
    servo.duty_u16(int(pulse_width * 65535 / 20000))

# Joystick ve buton ayarları
joystick_x_pin = 27
joystick_y_pin = 28
joystick_button_pin = Pin(20, Pin.IN, Pin.PULL_UP)  # Joystick buton pin ayarı, toprağa çekiliyor
record_button_pin = Pin(22, Pin.IN, Pin.PULL_UP)  # Kayıt buton pin ayarı, toprağa çekiliyor
playback_button_pin = Pin(21, Pin.IN, Pin.PULL_UP)  # Kaydedilen hareketleri oynatma buton pin ayarı, toprağa çekiliyor
select_button_pin = Pin(19, Pin.IN, Pin.PULL_UP)  # Pozisyon listesi seçim buton pin ayarı, toprağa çekiliyor
threshold = 500  # Merkez tolerans aralığı
servo_pos = {"servo1": 90, "servo2": 90, "servo3": 90, "servo4": 90}  # Servo motor başlangıç açıları
positions1 = []  # İlk pozisyonlar listesi
positions2 = []  # İkinci pozisyonlar listesi
current_positions = positions1  # Başlangıçta kullanılan pozisyon listesi
select_button_last_state = 1  # Seçim butonunun önceki durumu
current_positions_label = "positions1"

# Başlangıç pozisyonunu ayarla
for servo, pos in servo_pos.items():
    set_servo_position(servos[servo], pos)

# Başlangıç durumu
current_state = 1
print("Current State:", current_state)

# Kaydedilen pozisyonlar arasında interpolasyon yaparak yumuşak bir geçiş sağlar
def interpolate_positions(start_pos, end_pos, steps):
    interpolated_positions = []
    for i in range(steps):
        # Lineer interpolasyon hesaplama
        interpolated_pos = {}
        for servo in start_pos.keys():
            interpolated_pos[servo] = start_pos[servo] + (end_pos[servo] - start_pos[servo]) * (i / steps)
        interpolated_positions.append(interpolated_pos)
    return interpolated_positions

# Kaydedilen hareketleri oynat
def playback_recorded_positions(recorded_positions):
    play_buzzer_melody1()  # Melodi çal
    for i in range(len(recorded_positions) - 1):
        start_pos = recorded_positions[i]
        end_pos = recorded_positions[i + 1]
        # Her iki pozisyon arasında interpolasyon yaparak yumuşak geçiş sağla
        interpolated_positions = interpolate_positions(start_pos, end_pos, 120)  # 10 adımda geçiş yap
        for pos in interpolated_positions:
            for servo, angle in pos.items():
                set_servo_position(servos[servo], angle)
            time.sleep(0.01)  # Küçük bir bekleme süresi

while True:
    x_val = ADC(Pin(joystick_x_pin)).read_u16() // 64  # Joystick'in x değeri
    y_val = ADC(Pin(joystick_y_pin)).read_u16() // 64  # Joystick'in y değeri

    # Joystick buton durumunu kontrol et
    if joystick_button_pin.value() == 0:  # Joystick butona basıldığında
        if current_state == 1:
            current_state = 2
        else:
            current_state = 1
        print("Button Pressed: Mode Change -> State:", current_state)
        time.sleep(0.3)  # Butona basıldığında yanlış algılamayı önlemek için bekleme süresi

    # Kayıt buton durumunu kontrol et
    if record_button_pin.value() == 0:  # Kayıt butonuna basıldığında
        current_positions.append(servo_pos.copy())  # Mevcut pozisyonları kaydet
        print("Position Recorded:", servo_pos, "in", current_positions_label)
        if current_positions_label == "positions1":
            play_buzzer_melody1()  # positions1 için melodi 1 çal
        else:
            play_buzzer_melody2()  # positions2 için melodi 2 çal
        time.sleep(0.3)  # Butona basıldığında yanlış algılamayı önlemek için bekleme süresi

    # Kaydedilen hareketleri oynatma buton durumunu kontrol et
    if playback_button_pin.value() == 0:  # Kaydedilen hareketleri oynatma butonuna basıldığında
        print("Playing back recorded positions in", current_positions_label, "...")
        playback_recorded_positions(current_positions)
        time.sleep(0.3)  # Butona basıldığında yanlış algılamayı önlemek için bekleme süresi

    # Pozisyon listesi seçim buton durumunu kontrol et
    select_button_state = select_button_pin.value()
    if select_button_state == 0 and select_button_last_state == 1:  # Seçim butonuna bir defa basıldığında
        if current_positions == positions1:
            current_positions = positions2
            current_positions_label = "positions2"
            print("Switched to positions2")
        else:
            current_positions = positions1
            current_positions_label = "positions1"
            print("Switched to positions1")
        buzzer_beep()  # Seçim butonuna basıldığında bip sesi çıkar
        time.sleep(0.3)  # Butona basıldığında yanlış algılamayı önlemek için bekleme süresi

    select_button_last_state = select_button_state  # Seçim butonunun durumunu güncelle

    # Motor pozisyonlarını güncelle
    if current_state == 1:  # İlk durum, 1. ve 2. motoru kontrol eder
        servo_pos["servo1"] += 2 if y_val > (512 + threshold) else (-2 if y_val < (512 - threshold) else 0)
        servo_pos["servo2"] += 2 if x_val > (512 + threshold) else (-2 if x_val < (512 - threshold) else 0)
    else:  # İkinci durum, 3. ve 4. motoru kontrol eder
        servo_pos["servo3"] += 2 if y_val > (512 + threshold) else (-2 if y_val < (512 - threshold) else 0)
        servo_pos["servo4"] += 1 if x_val > (512 + threshold) else (-1 if x_val < (512 - threshold) else 0)

    # Servo pozisyonlarını sınırla (0 ile 180 derece arasında)
    for servo, pos in servo_pos.items():
        servo_pos[servo] = max(18, min(180, pos))

    # Servo motor pozisyonlarını ayarla
    for servo, pos in servo_pos.items():
        set_servo_position(servos[servo], pos)

    # Değerleri ekrana yazdır
    print("X: {} Y: {} Joystick Button: {} Record Button: {} Playback Button: {} Select Button: {} Current State: {} Servo Positions: {}".format(
        x_val, y_val, joystick_button_pin.value(), record_button_pin.value(), playback_button_pin.value(), select_button_pin.value(), current_state, servo_pos))

    time.sleep(0.05)  # Küçük bir bekleme süresi
