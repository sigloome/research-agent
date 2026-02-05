
import asyncio
import os
from claude_agent_sdk.client import ClaudeSDKClient
from claude_agent_sdk.types import ClaudeAgentOptions, AssistantMessage, TextBlock

# Mock credentials if needed, but the SDK subprocess usually uses local auth
# We assume the environment is already set up

async def test_persistence():
    print("Initializing client...")
    client = ClaudeSDKClient()
    
    # Connect
    print("Connecting...")
    await client.connect()
    print("Connected.")
    
    try:
        session_id = "test_interaction_1"
        
        # Turn 1
        print(f"\n--- Turn 1 (Session {session_id}) ---")
        prompt1 = "My name is Antigravity. Remember this."
        print(f"User: {prompt1}")
        await client.query(prompt1, session_id=session_id)
        
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")
                        
        # Turn 2
        print(f"\n--- Turn 2 (Session {session_id}) ---")
        prompt2 = "What is my name?"
        print(f"User: {prompt2}")
        await client.query(prompt2, session_id=session_id)
        
        name_found = False
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")
                        if "Antigravity" in block.text:
                            name_found = True
                            
        if name_found:
            print("\nSUCCESS: Context preserved.")
        else:
            print("\nFAILURE: Context lost.")
            
    finally:
        await client.disconnect()
        print("\nDisconnected.")

if __name__ == "__main__":
    try:
        asyncio.run(test_persistence())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}")
