# Gemini API Configuration
# Add your Gemini API key here or set it as an environment variable GEMINI_API_KEY
import os

GEMINI_API_KEY = os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")  # Add your API key here

# Alternative: You can also set the API key as an environment variable:
# export GEMINI_API_KEY="your_api_key_here"
# or on Windows: set GEMINI_API_KEY=your_api_key_here

# The system will first check for the environment variable,
# then fall back to the key defined above
