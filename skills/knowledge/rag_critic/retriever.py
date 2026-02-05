
from typing import List

from .critic import RagCritic


class HierarchicalRetriever:
    """
    Retrieves information using a Critic to filter out irrelevant chunks.
    """
    def __init__(self, model: str = "claude-sonnet-4-5-20250929"):
        self.critic = RagCritic(model)

    async def retrieve_and_filter(self, query: str, chunks: List[str]) -> List[str]:
        """
        Takes raw chunks (from a search or naive retrieval),
        Scores them using the Critic,
        Returns only the high-quality chunks.
        """
        print(f"[Retriever] Scoring {len(chunks)} chunks for query: '{query}'")
        
        filtered_chunks = []
        
        # In production, we'd run this in parallel. unique concurrent task for each chunk.
        for chunk in chunks:
            # Call the Critic (REAL LLM Call)
            eval_result = await self.critic.evaluate_chunk(query, chunk)
            
            score = eval_result.get("score", 0.0)
            reasoning = eval_result.get("reasoning", "No reasoning provided")
            
            print(f"  - Chunk Preview: {chunk.strip()[:50]}...")
            print(f"    -> Score: {score} | Reason: {reasoning}")
            
            # Threshold: 0.5 (Strict filter)
            if score >= 0.5:
                filtered_chunks.append(chunk)
            else:
                print("    -> REJECTED (Distractor/Irrelevant)")
                
        return filtered_chunks
