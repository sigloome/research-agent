import json
import os

from anthropic import Anthropic


def generate_summary(text: str, title: str = "") -> dict:
    """
    Generates a structured summary for the given text using Claude.
    """
    api_key = os.environ.get("ANTHROPIC_AUTH_TOKEN")
    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    
    if not api_key:
        # Fallback or error
        print("Warning: ANTHROPIC_AUTH_TOKEN not found.")
        return {}

    client = Anthropic(api_key=api_key, base_url=base_url)
    
    prompt = f"""
    You are an expert AI researcher. Analyze the following paper (Title: {title}) and provide a structured summary.
    
    Content:
    {text[:50000]}  # Limit context window just in case
    
    Return ONLY a JSON object with the following keys:
    - "tags": list of strings (e.g. ["LLM", "RLHF", "Vision"])
    - "summary_main_ideas": string
    - "summary_methods": string
    - "summary_results": string
    - "summary_limitations": string
    
    Do not output any markdown formatting like ```json, just the raw JSON string.
    """
    
    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            temperature=0,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        content = message.content[0].text
        # cleanup if model returns markdown
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "")
        
        return json.loads(content)
        
    except Exception as e:
        print(f"Error generating summary: {e}")
        return {
            "tags": ["Error"],
            "summary_main_ideas": "Failed to generate summary.",
            "summary_methods": "",
            "summary_results": "",
            "summary_limitations": ""
        }
