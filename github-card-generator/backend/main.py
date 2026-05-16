import os
from dotenv import load_dotenv

# 1. ABSOLUTE TOP: SYNC KEYS
load_dotenv()
raw_key = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
api_key = raw_key.strip().replace('"', '').replace("'", "")

# Force standard variable only
os.environ["GOOGLE_API_KEY"] = api_key
if "GEMINI_API_KEY" in os.environ: del os.environ["GEMINI_API_KEY"]
os.environ["GOOGLE_GENAI_API_VERSION"] = "v1alpha"

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.genai import types
from agent import github_card_agent
from pathlib import Path

app = FastAPI(title="GitHub Dev Card Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path("static/cards")
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

session_service = InMemorySessionService()
memory_service = InMemoryMemoryService()

class GenerateRequest(BaseModel):
    username: str

@app.get("/health")
async def health():
    return {"status": "ok", "key_set": bool(os.environ.get("GOOGLE_API_KEY"))}

@app.post("/generate")
async def generate_card(request: GenerateRequest):
    username = request.username
    session_id = f"session_{username}"
    
    runner = Runner(
        app_name="github_dev_card_app",
        agent=github_card_agent,
        session_service=session_service,
        memory_service=memory_service,
        auto_create_session=True
    )
    
    try:
        prompt = f"Generate a dev card for {username}."
        new_message = types.Content(parts=[types.Part(text=prompt)])
        
        async for event in runner.run_async(
            user_id="user_1",
            session_id=session_id,
            new_message=new_message
        ):
            print(f"AGENT -> {type(event).__name__}")
        
        # Check success
        card_file = STATIC_DIR / f"{username}.html"
        if card_file.exists():
            return {"status": "success", "card_url": f"/static/cards/{username}.html"}
        else:
            return {"status": "error", "detail": "Agent finished but card not found."}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "detail": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
