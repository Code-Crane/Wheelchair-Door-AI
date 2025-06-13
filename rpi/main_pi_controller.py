import cv2
import numpy as np
import tensorflow as tf
from picamera2 import Picamera2
import gpiod
import time
import threading

CONTROL_PINS = [14, 15, 18, 23]
STEP_COUNT = 512
STEP_DELAY = 0.001

chip = gpiod.Chip('/dev/gpiochip0')
lines = [chip.get_line(pin) for pin in CONTROL_PINS]
for line in lines:
    line.request(consumer='StepperMotor', type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0])

SEQ_RIGHT = [
    [1, 0, 0, 0], [1, 1, 0, 0], [0, 1, 0, 0], [0, 1, 1, 0],
    [0, 0, 1, 0], [0, 0, 1, 1], [0, 0, 0, 1], [1, 0, 0, 1]
]
SEQ_LEFT = [
    [0, 0, 0, 1], [0, 0, 1, 1], [0, 0, 1, 0], [0, 1, 1, 0],
    [0, 1, 0, 0], [1, 1, 0, 0], [1, 0, 0, 0], [1, 0, 0, 1]
]

def rotate_motor(direction='right'):
    # 스텝 모터를 지정된 방향으로 회전
    seq = SEQ_RIGHT if direction == 'right' else SEQ_LEFT
    for _ in range(STEP_COUNT*1):
        for halfstep in range(8):
            for pin in range(4):
                lines[pin].set_value(seq[halfstep][pin])
            time.sleep(STEP_DELAY)
    time.sleep(10)
    seq = SEQ_LEFT if direction == 'right' else SEQ_RIGHT
    for _ in range(STEP_COUNT*1):
        for halfstep in range(8):
            for pin in range(4):
                lines[pin].set_value(seq[halfstep][pin])
            time.sleep(STEP_DELAY)
    time.sleep(3)

frame = None
frame_lock = threading.Lock()
running = True
motor_active = False
THRESHOLD = 0.5

def start_motor_async(direction='right'):
    # 모터를 비동기로 동작시켜 메인 루프가 멈추지 않도록 함
    global motor_active
    if not motor_active:
        motor_active = True
        def run():
            rotate_motor(direction)
            global motor_active
            motor_active = False
        threading.Thread(target=run, daemon=True).start()

model = tf.keras.models.load_model('/home/pi03/best_model_effnetb34.h5')

picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"format": "RGB888", "size": (640, 480)})
picam2.configure(config)
picam2.start()

def camera_capture_loop():
    # 카메라에서 프레임을 지속적으로 읽어옴
    global frame, running
    while running:
        try:
            img = picam2.capture_array()
            with frame_lock:
                frame = img
            time.sleep(0.01)
        except Exception:
            pass

cam_thread = threading.Thread(target=camera_capture_loop)
cam_thread.start()

try:
    while True:
        with frame_lock:
            current_frame = frame.copy() if frame is not None else None

        if current_frame is None:
            time.sleep(0.05)
            continue

        if motor_active:
            time.sleep(0.1)
            continue

        # 이미지 전처리
        img = cv2.resize(current_frame, (224, 224))
        img = img.astype('float32') / 255.0
        img = np.expand_dims(img, axis=0)

        # 모델 예측 수행
        pred = model.predict(img, verbose=0)[0][0]

        if pred >= THRESHOLD:
            # 휠체어가 감지되면 모터 동작
            start_motor_async(direction='right')
            label = f"Wheelchair ({pred:.2f})"
            color = (0, 255, 0)
        else:
            label = f"No Wheelchair ({pred:.2f})"
            color = (0, 0, 255)

        # 결과를 화면에 표시
        cv2.putText(current_frame, label, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)
        cv2.imshow("Wheelchair Detection", current_frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

finally:
    running = False
    cam_thread.join()
    for line in lines:
        line.release()
    picam2.stop()
    cv2.destroyAllWindows()
