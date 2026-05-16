import os
import httpx
import json
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import google.generativeai as genai
from pathlib import Path

load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("GithubCardGenerator")

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash") # Using 1.5 Flash as 2.5 is not yet standard in SDK

@mcp.tool()
async def scrape_github(username: str) -> dict:
    """Fetch profile and repo data from GitHub REST API."""
    github_token = os.getenv("GITHUB_TOKEN")
    headers = {"Authorization": f"token {github_token}"} if github_token else {}
    
    async with httpx.AsyncClient() as client:
        # Fetch user profile
        user_res = await client.get(f"https://api.github.com/users/{username}", headers=headers)
        if user_res.status_code != 200:
            return {"error": "User not found"}
        user_data = user_res.json()

        # Fetch repos
        repos_res = await client.get(f"https://api.github.com/users/{username}/repos?sort=stars&per_page=30", headers=headers)
        repos_data = repos_res.json() if repos_res.status_code == 200 else []

    # Process repos
    top_repos = []
    languages = {}
    for r in sorted(repos_data, key=lambda x: x.get("stargazers_count", 0), reverse=True)[:6]:
        top_repos.append({
            "name": r.get("name"),
            "stars": r.get("stargazers_count"),
            "language": r.get("language"),
            "description": r.get("description")
        })
        lang = r.get("language")
        if lang:
            languages[lang] = languages.get(lang, 0) + 1

    return {
        "name": user_data.get("name") or username,
        "bio": user_data.get("bio"),
        "location": user_data.get("location"),
        "public_repos": user_data.get("public_repos"),
        "followers": user_data.get("followers"),
        "avatar_url": user_data.get("avatar_url"),
        "top_repos": top_repos,
        "most_used_languages": sorted(languages.keys(), key=lambda l: languages[l], reverse=True)
    }

@mcp.tool()
async def analyze_profile(github_data: dict) -> dict:
    """Analyze GitHub data using Gemini to determine vibe and theme."""
    prompt = f"""
    Analyze this GitHub profile data and return a JSON object.
    Data: {json.dumps(github_data)}

    Return exactly this JSON structure:
    {{
        "developer_vibe": "one sentence personality description",
        "top_skills": ["skill1", "skill2", "skill3"],
        "fun_fact": "something clever inferred from their repos",
        "card_theme": "one of: hacker, builder, researcher, designer, open-source-hero"
    }}
    """
    response = model.generate_content(prompt)
    try:
        # Basic JSON extraction from response
        text = response.text
        start = text.find("{")
        end = text.rfind("}") + 1
        return json.loads(text[start:end])
    except Exception as e:
        return {
            "developer_vibe": "A dedicated code craftsman.",
            "top_skills": github_data.get("most_used_languages", ["Coding"])[:3],
            "fun_fact": "Has a prolific GitHub presence.",
            "card_theme": "builder"
        }

@mcp.tool()
async def generate_card_html(username: str, github_data: dict, analysis: dict) -> str:
    """Generate a self-contained, beautiful HTML dev card."""
    theme_colors = {
        "hacker": {"bg": "#0f172a", "text": "#38bdf8", "accent": "#1e293b"},
        "builder": {"bg": "#f8fafc", "text": "#1e293b", "accent": "#e2e8f0"},
        "researcher": {"bg": "#1e1b4b", "text": "#e0e7ff", "accent": "#312e81"},
        "designer": {"bg": "#fff1f2", "text": "#9f1239", "accent": "#ffe4e6"},
        "open-source-hero": {"bg": "#f0fdf4", "text": "#166534", "accent": "#dcfce7"}
    }
    theme = theme_colors.get(analysis.get("card_theme"), theme_colors["builder"])
    
    skills_html = "".join([f"<span style='background:{theme['accent']}; padding:2px 8px; border-radius:12px; margin-right:5px;'>{s}</span>" for s in analysis.get("top_skills", [])])
    repos_html = "".join([f"<div style='margin-top:10px;'><strong>{r['name']}</strong> - ⭐ {r['stars']}<br/><small>{r['description'] or ''}</small></div>" for r in github_data.get("top_repos", [])[:3]])

    html = f"""
    <div style="font-family: sans-serif; background: {theme['bg']}; color: {theme['text']}; padding: 20px; border-radius: 15px; width: 400px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);">
        <div style="display: flex; align-items: center; gap: 15px;">
            <img src="{github_data.get('avatar_url')}" style="width: 80px; height: 80px; border-radius: 50%; border: 3px solid {theme['text']}"/>
            <div>
                <h2 style="margin:0;">{github_data.get('name')}</h2>
                <p style="margin:5px 0; font-style: italic; opacity: 0.8;">{analysis.get('developer_vibe')}</p>
            </div>
        </div>
        <div style="margin-top: 15px;">
            {skills_html}
        </div>
        <div style="margin-top: 20px; display: flex; gap: 20px; font-weight: bold;">
            <div>📦 {github_data.get('public_repos')} Repos</div>
            <div>👥 {github_data.get('followers')} Followers</div>
        </div>
        <div style="margin-top: 20px; border-top: 1px solid {theme['text']}; padding-top: 10px;">
            <strong>Top Repositories</strong>
            {repos_html}
        </div>
        <div style="margin-top: 15px; font-size: 0.8em; opacity: 0.7;">
            💡 {analysis.get('fun_fact')}
        </div>
    </div>
    """
    return html

@mcp.tool()
async def save_card(username: str, html: str) -> str:
    """Save HTML to static/cards/ and return path."""
    path = Path(f"static/cards")
    path.mkdir(parents=True, exist_ok=True)
    file_path = path / f"{username}.html"
    file_path.write_text(html, encoding="utf-8")
    return f"/static/cards/{username}.html"

if __name__ == "__main__":
    mcp.run()
