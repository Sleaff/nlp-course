from fastapi import FastAPI
from pydantic import BaseModel
import requests
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI()

class TextInput(BaseModel):
    text: str

@app.post("/v1/extract-persons")
def send_message(text: TextInput):
        logger.info(f"v1/extract-persons called with text: {text.text[:50]}...")
        api_url = f"https://chat.campusai.compute.dtu.dk/api/chat/completions"

        api_key = os.getenv("CAMPUSAI_API_KEY")
        logger.info(f"API key status: {'set' if api_key else 'NOT SET'}")

        if not api_key:
            return {"error": "CAMPUSAI_API_KEY environment variable not set"}

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "Gemma3",
            "messages": [
                {"role": "user", "content": 
                 f"""Extract all person names from the following text. Return only a list of names, one per line.
                 Text: "{text.text}"
                 Names:"""}
            ],
            "temperature": 0.5,
            "stream": False
        }

        response = requests.post(api_url, json=payload, headers=headers)
        logger.info(f"API response status: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"API request failed: {response.text}")
            return {"error": f"API request failed with status {response.status_code}", "detail": response.text}
        
        result = response.json()
        names_text = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        logger.info(f"Received names text: {names_text}")
        
        persons = []
        if names_text:
            lines = names_text.split('\n')
            for line in lines:
                name = line.strip().lstrip('-*•').strip()
                import re
                name = re.sub(r'^\d+[\.\)]\s*', '', name)
                if name and len(name) > 1:  # Basic validation
                    persons.append(name)
        
        logger.info(f"Extracted persons: {persons}")
        return {"persons": persons}
