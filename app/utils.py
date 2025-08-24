from pathlib import Path
import cv2
import yaml
import time

def load_yaml(path):
    return yaml.safe_load(Path(path).read_text())

def save_crop(img, xyxy, out_dir="crops", prefix="triple-riding"):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    x1, y1, x2, y2 = map(int, xyxy)
    crop = img[y1:y2, x1:x2]
    fname = f"{prefix}_{int(time.time()*1000)}.jpg"
    fpath = str(Path(out_dir)/fname)
    cv2.imwrite(fpath, crop)
    return fpath

def process_frame(frame, models, config, last_detection_time, fines):
    """
    Runs YOLO models on the frame, annotates violations, and returns detections.
    """
    violations = []
    now = time.time()
    for model, tag in models:
        results = model.predict(frame, conf=config["conf_thresholds"][tag])
        for r in results:
            for box in r.boxes:
                cls_name = r.names[int(box.cls[0])]
                if cls_name not in fines:
                    continue
                # cooldown check
                if now - last_detection_time.get(cls_name, 0) < config["cooldown_sec"]:
                    continue
                last_detection_time[cls_name] = now
                xyxy = box.xyxy[0].tolist()
                violations.append({
                    "type": cls_name,
                    "bbox": xyxy,
                    "fine": fines[cls_name]
                })
                # Optionally draw box
                x1, y1, x2, y2 = map(int, xyxy)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0,0,255), 2)
                cv2.putText(frame, cls_name, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,0,255), 2)
    return frame, violations
