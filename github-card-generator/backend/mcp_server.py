import os
import json
import httpx
from pathlib import Path
from dotenv import load_dotenv

from mcp.server.fastmcp import FastMCP

from google import genai
from google.genai import types

load_dotenv()

# =========================
# ENV (SAFE)
# =========================
raw_key = os.getenv("GEMINI_API_KEY")

if not raw_key:
    raise RuntimeError("❌ GEMINI_API_KEY missing")

api_key = raw_key.strip()

print("🚀 MCP Server Starting...")
print("Key Loaded:", api_key[:6] + "..." + api_key[-4:])

# =========================
# GEMINI CLIENT
# =========================
client = genai.Client(api_key=api_key)

# =========================
# MCP INIT
# =========================
mcp = FastMCP("GithubCardGenerator")


# =========================
# GITHUB SCRAPER
# =========================
@mcp.tool()
async def scrape_github(username: str) -> dict:
    headers = {
        "User-Agent": "github-card-generator"
    }

    async with httpx.AsyncClient(headers=headers, timeout=20) as http:

        user = await http.get(f"https://api.github.com/users/{username}")
        if user.status_code != 200:
            return {"error": "User not found"}

        repos = await http.get(
            f"https://api.github.com/users/{username}/repos?per_page=30&sort=stars"
        )

    user_data = user.json()
    repos_data = repos.json() if repos.status_code == 200 else []

    top_repos = sorted(
        repos_data,
        key=lambda r: r.get("stargazers_count", 0),
        reverse=True
    )[:6]

    return {
        "name": user_data.get("name") or username,
        "avatar_url": user_data.get("avatar_url"),
        "bio": user_data.get("bio"),
        "followers": user_data.get("followers"),
        "public_repos": user_data.get("public_repos"),
        "top_repos": [
            {
                "name": r.get("name"),
                "stars": r.get("stargazers_count"),
                "language": r.get("language")
            }
            for r in top_repos
        ]
    }


# =========================
# GEMINI ANALYSIS (ROBUST)
# =========================
@mcp.tool()
async def analyze_profile(github_data: dict) -> dict:

    prompt = f"""
Return ONLY valid JSON.

GitHub Profile:
{json.dumps(github_data)}
"""

    try:
        res = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=
                    "Return ONLY JSON with keys: developer_vibe, top_skills, fun_fact, card_theme.",
                response_mime_type="application/json"
            )
        )

        text = (res.text or "").strip()

        return json.loads(text)

    except Exception as e:
        print("⚠️ Gemini error:", e)

        return {
            "developer_vibe": "Passionate Developer",
            "top_skills": ["Code", "Git"],
            "fun_fact": "Loves building projects",
            "card_theme": "dark"
        }


# =========================
# HTML GENERATOR
# =========================
@mcp.tool()
async def generate_card_html(username: str, github_data: dict, analysis: dict) -> str:

    return f"""
<div style="
    background:#0d1117;
    color:white;
    padding:20px;
    border-radius:12px;
    font-family:Arial;
">
    <h2>{github_data.get("name", username)}</h2>
    <p>{analysis.get("developer_vibe", "")}</p>
    <p>Skills: {', '.join(analysis.get("top_skills", []))}</p>
</div>
"""


# =========================
# SAVE FILE
# =========================
@mcp.tool()
async def save_card(username: str, html: str) -> str:

    path = Path("static/cards")
    path.mkdir(parents=True, exist_ok=True)

    file_path = path / f"{username}.html"
    file_path.write_text(html, encoding="utf-8")

    return f"/static/cards/{username}.html"


# =========================
# RUN
# =========================
if __name__ == "__main__":
    mcp.run()