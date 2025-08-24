import cv2
import time
import yaml
import sys
import argparse
import os
from ultralytics import YOLO
from collections import defaultdict
from pathlib import Path

# Add the project root to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.dbsql import init_db, insert_violation
from app.utils import load_yaml

def process_video(video_path, show_display=True):
    """Process video for traffic violations detection"""
    
    # Initialize DB
    init_db()

    # Load config and fines
    config = load_yaml("app/config.yaml")
    fines = load_yaml("app/fines.yaml")

    # Load your single YOLO model (helmet + triple seat combined)
    model = YOLO("models/best.pt")

    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"❌ Error: Could not open video file: {video_path}")
        return False

    last_detection_time = defaultdict(float)
    cooldown_sec = config["cooldown_sec"]
    
    print(f"🎥 Processing video: {video_path}")
    violations_detected = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("✅ End of video reached.")
            break

        now = time.time()

        # Run detection with your model
        results = model.predict(frame, conf=config["conf_thresholds"]["helmet_triple"])

        detected = False  # Flag to check if any violation is detected

        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])  # since model has only one class
                cls_name = str(cls_id)    # treat it as "0"

                if cls_name not in fines:
                    continue

                if now - last_detection_time[cls_name] < cooldown_sec:
                    continue

                last_detection_time[cls_name] = now

                # Draw bounding box and label on the frame
                xyxy = box.xyxy[0].tolist()
                x1, y1, x2, y2 = map(int, xyxy)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(frame, "No helmet", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

                detected = True

        # If any violation detected, save the full annotated frame
        if detected:
            violations_detected += 1
            img_name = f"annotated_{int(time.time()*1000)}.jpg"
            img_path = str(Path("crops") / img_name)
            Path("crops").mkdir(parents=True, exist_ok=True)
            cv2.imwrite(img_path, frame)

            # Save violation to DB with full frame path
            insert_violation(
                file_path=img_path,
                violation_type="No helmet",
                fine=fines["0"]
            )

        # Only show display if requested (for standalone use)
        if show_display:
            cv2.imshow("Detection (Video)", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    if show_display:
        cv2.destroyAllWindows()
    
    print(f"Total violations detected: {violations_detected}")
    return True

def main():
    """Main function to handle command line arguments"""
    parser = argparse.ArgumentParser(description="Traffic Violation Detection")
    parser.add_argument("video_path", nargs="?", default="videos/no_helmet.mp4", 
                       help="Path to video file")
    parser.add_argument("--no-display", action="store_true", 
                       help="Run without GUI display (for web integration)")
    
    args = parser.parse_args()
    
    show_display = not args.no_display
    success = process_video(args.video_path, show_display)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
