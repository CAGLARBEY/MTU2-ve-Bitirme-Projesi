import cv2
import numpy as np
import serial
import time

# Seri bağlantısını başlat
ser = serial.Serial('COM4', 9600, timeout=1)  # Arduino'nun bağlı olduğu seri port ve baud rate

# Kamera bağlantısını başlat
cap = cv2.VideoCapture(1)    #droid 1 0 wepcam

# Kamera çözünürlüğünü al
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Merkez alanın boyutlarını belirle (örneğin, kameranın yarısı)
center_x = width // 2
center_y = height // 2
box_size = 100  # Merkezdeki alanın boyutu (kare şeklinde)

while True:
    # Kameradan bir kare al
    ret, frame = cap.read()

    # Eğer kare alınamazsa döngüden çık
    if not ret:
        break

    # Görüntüyü HSV (Renk Tonu, Doğruluğu, Parlaklık) renk uzayına dönüştür
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Turuncu rengi tanımlamak için güncellenmiş HSV aralığı
    lower_orange = np.array([5, 100, 100])
    upper_orange = np.array([15, 255, 255])

    # Siyah rengi tanımlamak için güncellenmiş RGB aralığı
    lower_black_rgb = np.array([0, 0, 0])
    upper_black_rgb = np.array([50, 50, 50])

    # Maske oluştur ve turuncu renkli alanları beyaz, diğerlerini siyah yap
    mask_orange = cv2.inRange(hsv, lower_orange, upper_orange)

    # Maske oluştur ve siyah renkli alanları beyaz, diğerlerini siyah yap
    mask_black = cv2.inRange(frame, lower_black_rgb, upper_black_rgb)

    # Merkez alanı belirle
    roi_orange = mask_orange[center_y - box_size // 2:center_y + box_size // 2, 
                             center_x - box_size // 2:center_x + box_size // 2]

    roi_black = mask_black[center_y - box_size // 2:center_y + box_size // 2, 
                           center_x - box_size // 2:center_x + box_size // 2]

    # Merkez alan içindeki turuncu ve siyah piksellerin sayısını hesapla
    orange_pixels = cv2.countNonZero(roi_orange)
    black_pixels = cv2.countNonZero(roi_black)

    # Siyah üzerindeki turuncu piksel oranını hesapla
    if black_pixels > 0:
        orange_ratio = orange_pixels / black_pixels
    else:
        orange_ratio = 0.0

    # Turuncu piksellerin parlaklık değerlerini al
    orange_values = hsv[mask_orange > 0][:, 2]
    if len(orange_values) > 0:
        orange_brightness = np.mean(orange_values)
    else:
        orange_brightness = 0

    # Orana göre durumu belirle
    if orange_ratio <= 0.1:
        status = "BOS"
        message = "M"
    elif orange_ratio <= 0.45:
        status = "KUCUK"
        message = "K"
    else:
        status = "BUYUK"
        message = "B"

    # Turuncu ve siyah piksel sayılarını ekranda göster
    cv2.putText(frame, f'Orange Pixels: {orange_pixels}', (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(frame, f'Black Pixels: {black_pixels}', (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(frame, f'Orange Brightness: {orange_brightness:.2f}', (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Durumu ve oranı ekranda göster
    cv2.putText(frame, f'Status: {status}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(frame, f'Orange Ratio: {orange_ratio:.2f}', (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Pencerede görüntüleri göster
    cv2.imshow('Original', frame)
    cv2.imshow('Mask Orange', mask_orange)
    cv2.imshow('Mask Black', mask_black)

    # Arduino'ya mesaj gönder
    ser.write(message.encode())

    # 'q' tuşuna basıldığında döngüyü kır
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Pencereyi kapat, seri bağlantıyı kapat ve kamera bağlantısını serbest bırak
cap.release()
ser.close()
cv2.destroyAllWindows()
