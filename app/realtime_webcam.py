import cv2
import time
from ultralytics import YOLO
from collections import defaultdict

from app.db import init_db, insert_violation
from app.utils import load_yaml, save_crop

# Load configs
cfg = load_yaml("app/config.yaml")
fines = load_yaml("app/fines.yaml")

def main():
    init_db()

    # Load models
    model1 = YOLO("models/helmet_triple_best.pt")
    model2 = YOLO("models/seatbelt_best.pt")

    #cap = cv2.VideoCapture(cfg["camera_index"])
    cap = cv2.VideoCapture("traffic_sample.mp4")
    assert cap.isOpened(), "Camera not found!"

    last_saved = defaultdict(float)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        now = time.time()

        for model, tag in [(model1, "helmet_triple"), (model2, "seatbelt")]:
            results = model.predict(frame, conf=cfg["conf_thresholds"][tag])
            for r in results:
                for box in r.boxes:
                    cls_name = r.names[int(box.cls[0])]
                    if cls_name not in fines:
                        continue  # not a violation

                    # cooldown check
                    if now - last_saved[cls_name] < cfg["cooldown_sec"]:
                        continue

                    xyxy = box.xyxy[0].tolist()
                    crop_path = save_crop(frame, xyxy, prefix=cls_name)
                    fine = fines[cls_name]
                    insert_violation(crop_path, cls_name, fine)

                    last_saved[cls_name] = now

                    # draw on frame
                    x1,y1,x2,y2 = map(int, xyxy)
                    cv2.rectangle(frame, (x1,y1), (x2,y2), (0,0,255), 2)
                    cv2.putText(frame, f"{cls_name} Rs.{fine}", 
                                (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)

        cv2.imshow("Traffic Violations", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
