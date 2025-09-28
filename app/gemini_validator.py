import google.generativeai as genai
import json
import base64
from PIL import Image
import io
import os
from dotenv import load_dotenv
from app.gemini_config import GEMINI_API_KEY

# Load environment variables from .env file
load_dotenv()

class GeminiValidator:
    def __init__(self, api_key=None):
        """Initialize Gemini validator with API key"""
        self.api_key = api_key or os.getenv('GEMINI_API_KEY', '') or GEMINI_API_KEY
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            print(f"🤖 Gemini API initialized with key: {self.api_key[:10]}...{self.api_key[-4:]}")
        else:
            self.model = None
            print("⚠️  Gemini API key not found - validation will be bypassed")
    
    def get_system_prompt(self):
        """Get the system prompt for detection validation"""
        return """You are an AI traffic violation detection validator. Your task is to analyze annotated images and determine if the detected violations are correct.

You will receive images with bounding boxes and labels showing detected violations. The possible violations are:
1. "No helmet" - Person riding motorcycle/scooter without helmet
2. "Triple Riding" - More than 2 people on a single motorcycle/scooter
3. "No-seat-belt" - Person in car not wearing seatbelt

Analyze the image carefully and determine if the detection is accurate:
- Check if the bounding box correctly identifies the violation
- Verify the violation type matches what's actually shown
- Consider if the detection is a false positive

Respond ONLY with a JSON object in this exact format:
{
    "status": "correct" or "incorrect",
    "confidence": 0.0 to 1.0,
    "reason": "Brief explanation of your decision"
}

Be strict in your validation - only mark as "correct" if you are confident the detection is accurate."""

    def validate_detection(self, image_path, violation_type):
        """
        Validate a detection using Gemini API
        
        Args:
            image_path: Path to the annotated image
            violation_type: Type of violation detected
            
        Returns:
            dict: Validation result with status, confidence, and reason
        """
        if not self.model or not self.api_key:
            # If no API key, default to accepting all detections
            print("⚠️  Gemini API not available - bypassing validation (accepting detection)")
            return {
                "status": "correct",
                "confidence": 1.0,
                "reason": "Gemini API not configured - accepting detection"
            }
        
        try:
            # Load and prepare image
            image = Image.open(image_path)
            
            # Create prompt with context
            prompt = f"""
{self.get_system_prompt()}

The detected violation type is: "{violation_type}"

Please analyze this annotated image and validate if the detection is correct.
"""
            
            print(f"🔍 Calling Gemini API to validate '{violation_type}' detection...")
            # Send to Gemini
            response = self.model.generate_content([prompt, image])
            print(f"✅ Received response from Gemini API")
            
            # Parse JSON response
            try:
                result = json.loads(response.text.strip())
                
                # Validate response format
                if not all(key in result for key in ["status", "confidence", "reason"]):
                    raise ValueError("Invalid response format")
                
                if result["status"] not in ["correct", "incorrect"]:
                    raise ValueError("Invalid status value")
                
                if not (0.0 <= result["confidence"] <= 1.0):
                    raise ValueError("Invalid confidence value")
                
                return result
                
            except (json.JSONDecodeError, ValueError) as e:
                print(f"❌ Error parsing Gemini response: {e}")
                print(f"📄 Raw Gemini response: {response.text}")
                
                # Fallback: try to extract status from text
                response_lower = response.text.lower()
                if "correct" in response_lower and "incorrect" not in response_lower:
                    print("🔄 Fallback: Parsed 'correct' from text response")
                    return {
                        "status": "correct",
                        "confidence": 0.7,
                        "reason": "Parsed from text response"
                    }
                else:
                    print("🔄 Fallback: Parsed 'incorrect' from text response")
                    return {
                        "status": "incorrect",
                        "confidence": 0.7,
                        "reason": "Parsed from text response"
                    }
        
        except Exception as e:
            print(f"❌ Error validating with Gemini API: {e}")
            print("🔄 Defaulting to accepting detection due to API error")
            # On error, default to accepting detection
            return {
                "status": "correct",
                "confidence": 0.5,
                "reason": f"Validation error: {str(e)}"
            }

    def is_available(self):
        """Check if Gemini API is available"""
        return self.model is not None and bool(self.api_key)
