import cv2
import time
import yaml
from ultralytics import YOLO
from collections import defaultdict

from app.db import init_db, insert_violation
from app.utils import process_frame, load_yaml, save_crop

# Initialize DB
init_db()

# Load config and fines
config = load_yaml("app/config.yaml")
fines = load_yaml("app/fines.yaml")

# Load YOLO models
model_helmet = YOLO("models/helmet_triple_best.pt")
model_seatbelt = YOLO("models/seatbelt_best.pt")

video_path = "videos/delhi_traffic.mp4"
cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print("❌ Error: Could not open video file.")
    exit()

last_detection_time = defaultdict(float)
cooldown_sec = config["cooldown_sec"]

while True:
    ret, frame = cap.read()
    if not ret:
        print("✅ End of video reached.")
        break

    now = time.time()

    for model, tag in [(model_helmet, "helmet_triple"), (model_seatbelt, "seatbelt")]:
        results = model.predict(frame, conf=config["conf_thresholds"][tag])
        for r in results:
            for box in r.boxes:
                cls_name = r.names[int(box.cls[0])]
                if cls_name not in fines:
                    continue  # not a violation

                # cooldown check
                if now - last_detection_time[cls_name] < cooldown_sec:
                    continue

                last_detection_time[cls_name] = now

                # Save cropped image
                xyxy = box.xyxy[0].tolist()
                crop_path = save_crop(frame, xyxy, out_dir="crops", prefix=cls_name)

                # Save violation to DB with cropped image path
                insert_violation(
                    file_path=crop_path,
                    violation_type=cls_name,
                    fine=fines[cls_name]
                )

    cv2.imshow("Detection (Video)", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()