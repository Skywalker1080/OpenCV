from ultralytics import YOLO

if __name__ == "__main__":
    # Load a pretrained YOLOv8 small model
    model = YOLO("yolov8s.pt")

    # Train on helmet + triple riding dataset
    model.train(
        data="data/helmet_triple/data.yaml",  # path to your yaml
        epochs=80,              # increase if model underfits
        imgsz=832,              # larger helps small helmets
        batch=16,               # reduce if GPU OOM (try 8)
        device="cpu",               # 0=GPU0, or "cpu"
        patience=20,            # stop early if no improvement
        project="runs", 
        name="helmet_triple"
    )
