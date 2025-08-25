#!/usr/bin/env python3
"""
Simple YOLO Model Evaluation using built-in validation
"""

from ultralytics import YOLO
import os

def evaluate_yolo_model(model_path="models/best.pt", data_yaml_path="data/data.yaml"):
    """
    Evaluate YOLO model using built-in validation method
    
    Args:
        model_path: Path to your trained YOLO model (.pt file)
        data_yaml_path: Path to data.yaml file (optional - add manually later)
    """
    
    if not os.path.exists(model_path):
        print(f"❌ Model not found: {model_path}")
        return None
    
    print(f"🔍 Loading model: {model_path}")
    model = YOLO(model_path)
    
    try:
        if data_yaml_path and os.path.exists(data_yaml_path):
            print(f"📁 Using dataset config: {data_yaml_path}")
            results = model.val(data=data_yaml_path)
        else:
            print("📁 Using model's built-in dataset configuration")
            results = model.val()
        
        # Print key metrics
        print("\n📊 Validation Results:")
        print("-" * 40)
        print(f"mAP50:     {results.box.map50:.4f}")
        print(f"mAP50-95:  {results.box.map:.4f}")
        print(f"Precision: {results.box.mp:.4f}")
        print(f"Recall:    {results.box.mr:.4f}")
        print(f"F1-Score:  {results.box.f1:.4f}")
        print("-" * 40)
        
        return results
        
    except Exception as e:
        print(f"❌ Validation failed: {str(e)}")
        print("💡 This usually means:")
        print("   - No validation dataset is configured in the model")
        print("   - You need to provide a data.yaml file")
        print("   - The dataset paths in data.yaml are incorrect")
        return None

def main():
    """Main evaluation function"""
    print("🎯 YOLO Model Evaluation")
    print("=" * 50)
    
    # Data configuration file path
    data_yaml_path = "data/data.yaml"
    
    # Evaluate your main model
    model_path = "models/best.pt"
    results = evaluate_yolo_model(model_path, data_yaml_path)
    
    if results is None:
        print("\n💡 To get proper validation metrics:")
        print("1. Create a data.yaml file with your dataset configuration")
        print("2. Update the 'data_yaml_path' variable above")
        print("3. Run this script again")
        print("\nExample data.yaml structure:")
        print("```yaml")
        print("train: path/to/train/images")
        print("val: path/to/val/images")
        print("nc: 1  # number of classes")
        print("names: ['no_helmet']  # class names")
        print("```")

if __name__ == "__main__":
    main()
