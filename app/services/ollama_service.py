import json
import base64
import requests
from typing import Dict, Any, Optional
from PIL import Image as PILImage
import io

from app.core.config import settings
from app.models.image import Image, ImageMetadata


class OllamaVisionService:
    # Service for interacting with Ollama Vision API
    
    def __init__(self):
        self.base_url = settings.OLLAMA_URL or "http://host.docker.internal:11434"
        self.model = settings.VISION_MODEL or "llava:7b"
        print(f'Ollama service initialized with model: {self.model}')
        print(f'Ollama URL: {self.base_url}')
        
        # Test connection
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json()
                print(f'Connected to Ollama. Available models: {[m["name"] for m in models.get("models", [])]}')
            else:
                print(f'Ollama connection warning: {response.status_code}')
        except Exception as e:
            print(f'Warning: Could not connect to Ollama: {e}')
        
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        # Analyze an image using Ollama
        try:
            print(f'Opening image: {image_path}')
            img = PILImage.open(image_path)
            print(f'Image opened: {img.size}')
            
            # Convert image to base64
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
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
            
            print(f'Sending to Ollama with model: {self.model}...')
            
            # Call Ollama API
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "images": [img_base64],
                    "stream": False,
                    "format": "json"
                },
                timeout=120
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
            
            result = response.json()
            
            # Extract the response text
            if "response" in result:
                return self._parse_response(result["response"])
            else:
                return {
                    "error": "No response from Ollama",
                    "subject": "unknown",
                    "category": "unknown",
                    "caption": "Analysis failed: No response",
                    "tags": ["error"],
                    "confidence": 0.0
                }
            
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
        # Parse Ollama response and validate schema
        try:
            text = response_text.strip()
            
            # Remove markdown code blocks if present
            if text.startswith("`json"):
                text = text[7:]
            if text.startswith("`"):
                text = text[3:]
            if text.endswith("`"):
                text = text[:-3]
            text = text.strip()
            
            data = json.loads(text)
            
            # Validate required fields
            required_fields = ["subject", "category", "caption", "tags", "confidence"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Ensure confidence is between 0 and 1
            if not 0 <= data["confidence"] <= 1:
                data["confidence"] = 0.5
            
            # Ensure tags is a list
            if not isinstance(data["tags"], list):
                data["tags"] = [str(data["tags"])]
            
            # Limit tags to 5
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
    vision_service = OllamaVisionService()
except Exception as e:
    print(f'Error initializing Ollama service: {e}')
    vision_service = None
