
import json

from claude_agent_sdk import ClaudeAgentOptions, query


class RagCritic:
    """
    Evaluates the relevance of a retrieved chunk to a specific query.
    Acts as a binary classifier or scorer to filter out 'distractors'.
    """
    def __init__(self, model: str = "claude-sonnet-4-5-20250929"):
        self.model = model
        # Simplified options for internal LLM calls
        self.options = ClaudeAgentOptions(
             cwd=".",
             model=model,
             allowed_tools=[]
        )

    async def evaluate_chunk(self, query_text: str, chunk_text: str) -> dict:
        """
        Returns a dict with 'score' (0.0-1.0) and 'reasoning'.
        """
        prompt = f"""
        You are a strict Judge of Information Relevance.
        
        User Query: "{query_text}"
        Retrieved Text Chunk:
        \"\"\"{chunk_text}\"\"\"
        
        Your Goal: Determine if this chunk *actually contains the answer* or relevant evidence to the query.
        
        Rules:
        1. If the chunk mentions keywords but in a "Related Work" or "Background" context (i.e., describing *other* people's work), and the user is asking about *this* paper's method, the score should be LOW (0.0 - 0.3).
        2. If the chunk describes the proposed method, experimental results, or direct answer, score HIGH (0.7 - 1.0).
        
        Output JSON only:
        {{
            "score": 0.1,
            "reasoning": "This text is about ConvS2S, a different model mentioned in Related Work."
        }}
        """
        
        response_text = ""
        try:
            async for message in query(prompt=prompt, options=self.options):
                 if hasattr(message, 'content') and message.content:
                   for block in message.content:
                       if hasattr(block, 'text'):
                           response_text += block.text
            
            # Simple cleanup to ensure valid JSON
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end != -1:
                return json.loads(response_text[start:end])
            else:
                return {"score": 0.0, "reasoning": "Failed to parse LLM response"}
        except Exception as e:
            print(f"Critic Error: {e}")
            return {"score": 0.5, "reasoning": "Error in evaluation"}

