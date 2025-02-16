from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import json
import datetime
from utils.prompt_handler import PromptHandler
import aiohttp

# Load environment variables
load_dotenv()

app = FastAPI()
prompt_handler = PromptHandler()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    content: str

@app.post("/api/generate/{domain}")
async def generate_insight(domain: str, request: GenerateRequest):
    try:
        prompt_data = prompt_handler.format_prompt(domain, request.content)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'http://localhost:3001/api/generate',
                json=prompt_data
            ) as response:
                if not response.ok:
                    data = await response.json()
                    return {"error": data.get('error', 'Failed to generate insight')}, response.status_code
                    
                data = await response.json()
                return {
                    "content": data.content,
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
    except ValueError as e:
        return {"error": str(e)}, 400
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)