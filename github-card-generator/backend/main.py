from fastapi import FastAPI, Depends
from agent import GithubCardAgent, get_agent
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="GitHub Dev Card Generator API")

class GenerateRequest(BaseModel):
    username: str

@app.get("/")
async def root():
    return {"message": "GitHub Dev Card Generator API is running"}

@app.post("/generate")
async def generate_card(request: GenerateRequest, agent: GithubCardAgent = Depends(get_agent)):
    prompt = f"Generate a GitHub dev card for user: {request.username}"
    result = await agent.run(prompt)
    return {"result": result}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
