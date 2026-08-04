import os
import base64
import json
from typing import Dict, Any, Optional
from datetime import datetime
import google.generativeai as genai
from PIL import Image as PILImage
import io

from app.core.config import settings
from app.models.image import Image, ImageMetadata
from app.core.database import SessionLocal


class GeminiVisionService:
    # Service for interacting with Gemini Vision API
    
    def __init__(self):
        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY not set in environment variables")
        
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(settings.VISION_MODEL)
        print(f'Gemini service initialized with model: {settings.VISION_MODEL}')
        print(f'API Key: {settings.GOOGLE_API_KEY[:15]}...')
        
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        # Analyze an image using Gemini Vision
        try:
            print(f'Opening image: {image_path}')
            img = PILImage.open(image_path)
            print(f'Image opened: {img.size}')
            
            prompt = """Analyze this image and provide the following information in JSON format:
            {
                "subject": "The main subject of the image (be specific, use common names)",
                "category": "The category (animal, landscape, vehicle, person, food, building, object, nature, art)",
                "caption": "A brief, descriptive caption (1 sentence)",
                "tags": ["tag1", "tag2", "tag3", "tag4"],
                "confidence": 0.95
            }
            
            Rules:
            - subject: Be specific (e.g., 'red fox', not just 'animal')
            - category: Choose one from: animal, plant, landscape, person, vehicle, food, building, object, nature, art
            - caption: Write a natural, descriptive sentence
            - tags: Include relevant tags like color, action, environment, mood
            - confidence: Your confidence in identifying the subject (0.0 to 1.0)
            
            Return ONLY valid JSON, no other text, no markdown code blocks."""
            
            print('Sending to Gemini...')
            response = self.model.generate_content([prompt, img])
            print(f'Received response from Gemini: {response.text[:100]}...')
            
            result = self._parse_response(response.text)
            print(f'Parsed result: {result}')
            return result
            
        except Exception as e:
            print(f'Error in analyze_image: {e}')
            import traceback
            traceback.print_exc()
            return {
                "error": str(e),
                "subject": "unknown",
                "category": "unknown",
                "caption": f"Analysis failed: {str(e)}",
                "tags": ["error"],
                "confidence": 0.0
            }
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        # Parse Gemini response and validate schema
        try:
            text = response_text.strip()
            if text.startswith("`json"):
                text = text[7:]
            if text.startswith("`"):
                text = text[3:]
            if text.endswith("`"):
                text = text[:-3]
            text = text.strip()
            
            data = json.loads(text)
            
            required_fields = ["subject", "category", "caption", "tags", "confidence"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            if not 0 <= data["confidence"] <= 1:
                data["confidence"] = 0.5
            
            if not isinstance(data["tags"], list):
                data["tags"] = [str(data["tags"])]
            
            data["tags"] = data["tags"][:5]
            
            return data
            
        except json.JSONDecodeError as e:
            return {
                "error": f"JSON parsing failed: {str(e)}",
                "subject": "unknown",
                "category": "unknown",
                "caption": f"Parsing failed: {response_text[:100]}...",
                "tags": ["parse_error"],
                "confidence": 0.0
            }
        except Exception as e:
            return {
                "error": str(e),
                "subject": "unknown",
                "category": "unknown",
                "caption": f"Processing failed: {str(e)}",
                "tags": ["error"],
                "confidence": 0.0
            }
    
    def process_image(self, image: Image, db) -> Optional[ImageMetadata]:
        # Process a single image: analyze and save metadata
        try:
            print(f'Processing image {image.id}: {image.filename}')
            image.processing_status = "processing"
            db.commit()
            
            result = self.analyze_image(image.file_path)
            
            if "error" in result:
                image.processing_status = "failed"
                image.processing_error = result["error"]
                db.commit()
                print(f'Failed to process image {image.id}: {result["error"]}')
                return None
            
            metadata = ImageMetadata(
                image_id=image.id,
                subject=result["subject"],
                category=result["category"],
                caption=result["caption"],
                tags=result["tags"],
                confidence=result["confidence"],
                raw_response=result
            )
            
            db.add(metadata)
            image.processing_status = "completed"
            db.commit()
            
            print(f'Successfully processed image {image.id}: {result["subject"]} ({result["confidence"]:.2f})')
            return metadata
            
        except Exception as e:
            print(f'Error processing image {image.id}: {e}')
            import traceback
            traceback.print_exc()
            image.processing_status = "failed"
            image.processing_error = str(e)
            db.commit()
            return None


# Create singleton instance
try:
    vision_service = GeminiVisionService()
except Exception as e:
    print(f'Error initializing Gemini service: {e}')
    vision_service = None
