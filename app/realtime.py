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
from app.gemini_validator import GeminiValidator

def process_video(video_path, show_display=True):
    """Process video for traffic violations detection"""
    
    # Initialize DB
    init_db()
    
    # Initialize Gemini validator
    gemini_validator = GeminiValidator()

    # Load config and fines
    config = load_yaml("app/config.yaml")
    fines = load_yaml("app/fines.yaml")

    # Load all YOLO models
    main_model = YOLO("models/best.pt")  # Original model
    helmet_model = YOLO("models/helmet_triple_best.pt")  # Helmet and triple riding model
    seatbelt_model = YOLO("models/seatbelt_best.pt")  # Seatbelt model

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

        # Run detection with all models
        main_results = main_model.predict(frame, conf=config["conf_thresholds"]["helmet_triple"])
        helmet_results = helmet_model.predict(frame, conf=config["conf_thresholds"]["helmet_triple"])
        seatbelt_results = seatbelt_model.predict(frame, conf=config["conf_thresholds"]["helmet_triple"])

        detected = False  # Flag to check if any violation is detected
        violations_in_frame = []  # Store all violations detected in this frame

        # Process main model results (original violations)
        for r in main_results:
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

                violations_in_frame.append({
                    'type': 'No helmet',
                    'fine': fines[cls_name]
                })
                detected = True

        # Process helmet model results (triple riding and helmetless)
        for r in helmet_results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                # Get class names from the model
                class_names = helmet_model.names
                cls_name = class_names[cls_id] if cls_id in class_names else str(cls_id)
                
                # Only process triple riding violations from this model
                if cls_name.lower() == 'triple riding':
                    violation_key = 'triple riding'
                    
                    if violation_key not in fines:
                        continue

                    if now - last_detection_time[violation_key] < cooldown_sec:
                        continue

                    last_detection_time[violation_key] = now

                    # Draw bounding box and label on the frame
                    xyxy = box.xyxy[0].tolist()
                    x1, y1, x2, y2 = map(int, xyxy)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)  # Blue for triple riding
                    cv2.putText(frame, "Triple Riding", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)

                    violations_in_frame.append({
                        'type': 'Triple Riding',
                        'fine': fines[violation_key]
                    })
                    detected = True

        # Process seatbelt model results
        for r in seatbelt_results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                # Get class names from the model
                class_names = seatbelt_model.names
                cls_name = class_names[cls_id] if cls_id in class_names else str(cls_id)
                
                # Process No-seat-belt violations from this model
                if cls_name.lower() == 'no-seat-belt' or cls_name == 'No-seat-belt':
                    violation_key = 'No-seat-belt'
                    
                    if violation_key not in fines:
                        continue

                    if now - last_detection_time[violation_key] < cooldown_sec:
                        continue

                    last_detection_time[violation_key] = now

                    # Draw bounding box and label on the frame
                    xyxy = box.xyxy[0].tolist()
                    x1, y1, x2, y2 = map(int, xyxy)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Green for seatbelt
                    cv2.putText(frame, "No Seatbelt", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

                    violations_in_frame.append({
                        'type': 'No-seat-belt',
                        'fine': fines[violation_key]
                    })
                    detected = True

        # If any violation detected, save the full annotated frame and validate with Gemini
        if detected:
            violations_detected += 1
            img_name = f"annotated_{int(time.time()*1000)}.jpg"
            img_path = str(Path("crops") / img_name)
            Path("crops").mkdir(parents=True, exist_ok=True)
            cv2.imwrite(img_path, frame)

            # Validate and save each violation to DB
            for violation in violations_in_frame:
                # Validate detection with Gemini
                validation_result = gemini_validator.validate_detection(
                    img_path, violation['type']
                )
                
                print(f"Gemini validation for {violation['type']}: {validation_result['status']} (confidence: {validation_result['confidence']:.2f})")
                print(f"Reason: {validation_result['reason']}")
                
                # Only save to DB if validation is correct
                if validation_result['status'] == 'correct':
                    insert_violation(
                        file_path=img_path,
                        violation_type=violation['type'],
                        fine=violation['fine']
                    )
                    print(f"✅ Violation saved to database: {violation['type']}")
                else:
                    print(f"❌ Violation rejected by Gemini: {violation['type']}")
                    # Optionally, you could save rejected detections to a separate folder
                    # for manual review later

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
