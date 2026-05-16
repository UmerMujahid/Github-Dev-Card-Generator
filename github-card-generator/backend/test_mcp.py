import asyncio
import json
import os
from mcp_server import mcp

async def test_end_to_end():
    username = "torvalds"
    print(f"--- Testing for user: {username} ---")
    
    try:
        # 1. Scrape GitHub
        print("1. Scraping GitHub...")
        github_data = await mcp.get_tool("scrape_github")(username)
        if "error" in github_data:
            print(f"Scrape failed: {github_data['error']}")
            return

        # 2. Analyze Profile
        print("2. Analyzing Profile...")
        analysis = await mcp.get_tool("analyze_profile")(github_data)
        
        # 3. Generate Card HTML
        print("3. Generating Card HTML...")
        html = await mcp.get_tool("generate_card_html")(username, github_data, analysis)
        
        # 4. Results
        print("\n--- Results ---")
        print(f"Card Theme: {analysis.get('card_theme')}")
        print(f"Developer Vibe: {analysis.get('developer_vibe')}")
        print(f"HTML Length: {len(html)} chars")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_end_to_end())
