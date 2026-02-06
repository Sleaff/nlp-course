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

@app.post("/v0/sentiment")
def analyze_sentiment(text: TextInput):
    logger.info(f"v0/sentiment called with text: {text.text[:50]}...")
    lowered_text = text.text.lower()

    if 'god' in lowered_text or 'good' in lowered_text:
        return {"score": 3}
    elif 'dårlig' in lowered_text or 'bad' in lowered_text:
        return {"score": -3}
    else:
        return {"score": 0}
    

@app.post("/v1/sentiment")
def send_message(text: TextInput):
        logger.info(f"v1/sentiment called with text: {text.text[:50]}...")
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
                 f"""Classify the sentiment of the following text as positive, negative, or neutral within the range of (-5, 5). 5 being very positive, 3 being good, -5 very negative, -3 being negative, and 0 being neutral. 
                 Return only the number with no formatting
                 Text: "{text.text}"
                 Sentiment:"""}
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
        sentiment_text = result.get("choices", [{}])[0].get("message", {}).get("content", "0").strip()
        logger.info(f"Received sentiment text: {sentiment_text}")
        
        try:
            score = int(sentiment_text)
        except ValueError:
            score = 0
        
        return {"score": score}
