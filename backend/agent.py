import json
import os
from pathlib import Path
from typing import AsyncGenerator, Optional, Dict, Any, List

from claude_agent_sdk import ClaudeAgentOptions, query, SandboxSettings
from claude_agent_sdk.types import AssistantMessage, TextBlock, ToolUseBlock
from backend.logging_config import get_logger
from backend.content_filter import StreamingContentFilter

logger = get_logger()


def generate_tool_description(tool_name: str, tool_input: Dict[str, Any]) -> str:
    """
    Generate a human-readable description of what a tool is doing based on its name and input.
    """
    input_str = json.dumps(tool_input) if tool_input else "{}"
    
    # WebSearch
    if tool_name == "WebSearch":
        query = tool_input.get("query", tool_input.get("search_term", ""))
        if query:
            return f"Searching the web for: {query[:80]}{'...' if len(query) > 80 else ''}"
        return "Searching the web for information..."
    
    # WebFetch
    if tool_name == "WebFetch":
        url = tool_input.get("url", "")
        if url:
            # Extract domain for cleaner display
            domain = url.split("//")[-1].split("/")[0] if "//" in url else url.split("/")[0]
            return f"Fetching content from {domain}"
        return "Fetching content from a URL..."
    
    # Read
    if tool_name == "Read":
        path = tool_input.get("path", tool_input.get("file_path", ""))
        if path:
            filename = path.split("/")[-1] if "/" in path else path
            return f"Reading file: {filename}"
        return "Reading a file..."
    
    # Write
    if tool_name == "Write":
        path = tool_input.get("path", tool_input.get("file_path", ""))
        if path:
            filename = path.split("/")[-1] if "/" in path else path
            return f"Writing to file: {filename}"
        return "Writing to a file..."
    
    # Bash
    if tool_name == "Bash" or tool_name == "bash":
        description = tool_input.get("description", "")
        if description:
            return f"Running: {description[:70]}{'...' if len(description) > 70 else ''}"
        
        command = tool_input.get("command", "")
        if command:
            cmd_preview = command[:60] + "..." if len(command) > 60 else command
            return f"Running command: {cmd_preview}"
        return "Executing a shell command..."
    
    # Task
    if tool_name == "Task":
        description = tool_input.get("description", tool_input.get("task", ""))
        if description:
            return f"Running task: {description[:60]}{'...' if len(description) > 60 else ''}"
        return "Running a background task..."
    
    # Skill
    if tool_name == "Skill":
        skill_name = tool_input.get("skill", tool_input.get("skill_name", tool_input.get("name", "")))
        args = tool_input.get("args", tool_input.get("arguments", tool_input.get("query", "")))
        
        if skill_name and args:
            args_str = str(args)[:50]
            return f"Using '{skill_name}' skill for: {args_str}{'...' if len(str(args)) > 50 else ''}"
        elif skill_name:
            return f"Using skill: {skill_name}"
        elif args:
            args_str = str(args)[:60]
            return f"Using skill for: {args_str}{'...' if len(str(args)) > 60 else ''}"
        
        return "Using a specialized skill..."
    
    # Generic fallback with smarter formatting
    tool_display = tool_name.replace("_", " ").title()
    
    # Try to extract a meaningful parameter
    for key in ["query", "search", "topic", "name", "path", "url", "command", "description"]:
        if key in tool_input:
            value = str(tool_input[key])[:50]
            if value:
                return f"{tool_display}: {value}{'...' if len(str(tool_input[key])) > 50 else ''}"
    
    return f"Running: {tool_display}"


class MainAgent:
    """
    Main AI Agent using claude_agent_sdk.client.ClaudeSDKClient.
    
    This is the single unified agent that handles all tasks including research.
    Uses built-in SDK tools (WebSearch, WebFetch, Read, Write, Bash) directly.
    """
    
    def __init__(self):
        # Get API credentials from environment
        self.api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
        self.base_url = os.environ.get("ANTHROPIC_BASE_URL")
        self.model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")
        # Project root is parent of backend/
        self.cwd = Path(__file__).parent.parent
        
        self.base_system_prompt = """
        You are an expert AI Assistant with research and coding capabilities.
        
        ## Your Capabilities
        
        You have access to powerful tools:
        - **WebSearch**: Search the web for current information, papers, articles
        - **WebFetch**: Read content from specific URLs
        - **Read/Write**: File operations
        - **Bash**: Execute shell commands
        - **Skill**: Use specialized skills
        
        ## Research Tasks
        
        When users ask about research topics, papers, surveys, or technical comparisons:
        1. Use **WebSearch** immediately to find relevant information
        2. Use **WebFetch** to read detailed content from promising URLs
        3. Synthesize findings into a clear, comprehensive response
        4. Include sources with URLs when available
        
        ## Important Guidelines
        
        - **Execute, don't describe**: Don't say "I'll search for..." - just search and report findings
        - **Be direct**: Provide the answer, not a plan to find it
        - **Cite sources**: Include URLs for web sources
        - **Handle limitations gracefully**: If tools fail, explain what happened and what you can still provide
        
        ## Response Style
        
        - Clear and well-organized
        - Use markdown formatting for readability
        - Be concise but comprehensive
        
        ## Output Formatting (IMPORTANT)
        
        Use XML tags to structure your output. Different tags have different behaviors:
        
        ### Hidden Tags (content will be removed before showing to user)
        
        **<thinking>**: Internal reasoning, process descriptions, planning
        - "Let me search...", "I'll read...", "Now I need to..."
        - Tool usage narration: "Searching for...", "Reading file..."
        - Any self-referential commentary about what you're doing
        
        **<private>**: Sensitive information that should never be shown
        - File paths: /Users/.../file.txt, /home/.../data.pdf
        - Internal IDs, credentials, system paths
        - Storage locations and local file references
        
        **<debug>**: Development/debugging information
        - Technical details only useful for debugging
        - Verbose tool outputs not needed by user
        
        ### Display Tags (content will be formatted nicely for user)
        
        **<citation url="...">**: Source citations (will become clickable links)
        - IMPORTANT: For papers in the library, use local URLs: /paper/{paper_id}
        - The paper_id is the arxiv ID (e.g., "2401.12345") or local ID from the database
        - Example: <citation url="/paper/1706.03762">Vaswani et al., 2017</citation>
        - For external sources not in library, use full URLs
        
        **<summary>**: Summary sections (will be formatted as blockquote)
        - Use to highlight key takeaways
        - Example: <summary>The main finding is that attention mechanisms...</summary>
        
        **<source url="...">**: Source metadata (will be formatted with icon)
        - IMPORTANT: For papers in the library, use local URLs: /paper/{paper_id}
        - Example: <source url="/paper/1706.03762">Attention Is All You Need</source>
        - For external sources, use full URLs
        
        ### Example Usage
        
        <thinking>Let me search for papers on transformers.</thinking>
        <private>/Users/john/papers/attention.pdf</private>
        
        Here are the key findings:
        
        <source url="/paper/1706.03762">Attention Is All You Need (Vaswani et al., 2017)</source>
        
        <summary>
        The Transformer architecture replaces recurrence with self-attention,
        enabling parallel computation and better long-range dependency modeling.
        </summary>
        
        The paper introduces several innovations:
        1. Multi-head attention allows the model to jointly attend to information...
        2. Positional encodings provide sequence order information...
        
        <citation url="/paper/1706.03762">Vaswani et al., 2017</citation>
        """
        
        self.client = None

    def get_system_prompt(self, user_preferences: Optional[str] = None) -> str:
        """Build the system prompt with user preferences included."""
        prompt = self.base_system_prompt
        
        if user_preferences:
            prompt += f"""
        
        ## Learned User Preferences (Automated)
        
        {user_preferences}
        """

        # Inject User Profile (Markdown Config)
        try:
            from skills.preference.implementation import get_user_profile, get_user_history
            profile_md = get_user_profile()
            if profile_md and "No preferences set yet" not in profile_md:
                prompt += f"""

        ## User Profile & Configuration
        {profile_md}
        """
            
            # Inject User History
            history_md = get_user_history()
            if history_md and "No history yet" not in history_md:
                 prompt += f"""

        ## User Interaction History
        {history_md}
        """

        except Exception as e:
            print(f"Error loading user profile/history: {e}")
            
        prompt += """
        
        Use this information to personalize your responses and recommendations.
        """
        
        return prompt

    async def initialize(self):
        """Initialize and connect the SDK client."""
        if not self.client:
            from claude_agent_sdk.client import ClaudeSDKClient
            
            sandbox_settings: SandboxSettings = {
                "enabled": True,
                "autoAllowBashIfSandboxed": True,
                "network": {
                    "allowLocalBinding": True
                }
            }

            options = ClaudeAgentOptions(
                cwd=str(self.cwd),
                setting_sources=["project"],
                model=self.model,
                env=(
                    {
                        "ANTHROPIC_API_KEY": self.api_key or os.getenv("ANTHROPIC_API_KEY", ""),
                        "ANTHROPIC_AUTH_TOKEN": os.getenv("ANTHROPIC_AUTH_TOKEN", ""),
                        "ANTHROPIC_BASE_URL": self.base_url or "",
                    }
                ),
                system_prompt=self.base_system_prompt,
                allowed_tools=["WebSearch", "WebFetch", "Task", "Read", "Write", "Bash", "Skill"],
                permission_mode="bypassPermissions",
                sandbox=sandbox_settings
            )
            
            self.client = ClaudeSDKClient(options=options)
            print("Connecting to Claude SDK Client...")
            await self.client.connect()
            print("Claude SDK Client Connected.")

    async def chat_generator(
        self, 
        query: str, 
        session_id: str = "default", 
        user_preferences: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ):
        """
        Async generator that yields text chunks from Claude Agent SDK Client.
        
        query: The new user message
        session_id: Session ID for stateful context
        user_preferences: Optional string summarizing user preferences
        conversation_history: Optional list of prior messages [{"role": "user"/"assistant", "content": "..."}]
        
        OUTPUT FORMAT: Vercel AI SDK Data Stream Protocol
        0:"<text>"\n  -> Text parts
        d:<json>\n    -> Data parts (Tool usage)
        """
        try:
            logger.error(f"DEBUG: chat_generator started for query: {query[:20]} session: {session_id}")
            async for msg in self.run(
                query, 
                chat_id=session_id, 
                user_preferences=user_preferences,
                conversation_history=conversation_history
            ):
                # self.run yields strings from _format_text or _format_data
                logger.error(f"DEBUG: chat_generator yielding chunk: {msg[:50]}...")
                yield msg
        except Exception as e:
            logger.error(f"Chat generator error: {e}")
            yield self._format_data({"type": "error", "content": str(e)})

    def _format_text(self, text: str) -> str:
        """encodes text for Vercel protocol: 0:"quoted string"\n"""
        return f'0:{json.dumps(text)}\n'

    def _format_data(self, data: Dict[str, Any]) -> str:
        """encodes data for Vercel protocol: d:{...}\n"""
        # Note: standard Vercel 'd:' takes JSON directly, but frontend parsing might vary.
        # Historically this codebase uses d:{"type":...}\n
        return f'd:{json.dumps(data)}\n'

    async def run(
        self, 
        query: str, 
        chat_id: str, 
        user_preferences: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ):
        """
        Internal async generator to run the agent and yield formatted messages.
        
        conversation_history: List of prior messages to include as context.
                             This is used when resuming a historical chat session
                             that the SDK doesn't have in memory.
        """
        if not self.client:
            await self.initialize()

        # Build the full query with context
        full_query = query
        
        # If we have conversation history, prepend it as context
        # This allows the agent to continue historical conversations properly
        if conversation_history and len(conversation_history) > 0:
            history_context = "\n\n[Prior Conversation History - Please continue this conversation]\n"
            for msg in conversation_history:
                role_label = "User" if msg.get("role") == "user" else "Assistant"
                content = msg.get("content", "")
                # Truncate very long messages to keep context manageable
                if len(content) > 2000:
                    content = content[:2000] + "... [truncated]"
                history_context += f"\n{role_label}: {content}\n"
            history_context += "\n[End of History - Now responding to new message]\n\n"
            full_query = history_context + f"User: {query}"
        
        # Augment prompt with preferences if provided
        if user_preferences:
            full_query += f"\n\n[User Context Preferences]\n{user_preferences}"

        # Send query to SDK
        await self.client.query(full_query, session_id=chat_id)

        # Create content filter to remove <thinking> blocks and file paths
        content_filter = StreamingContentFilter()

        try:
            # Stream response until ResultMessage (end of turn)
            async for msg in self.client.receive_response():
                # Handle different message types
                logger.error(f"DEBUG: Agent yielded message type: {type(msg).__name__}")
                if isinstance(msg, AssistantMessage):
                    logger.error(f"DEBUG: AssistantMessage blocks: {len(msg.content)}")
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            logger.error(f"DEBUG: TextBlock content: {block.text[:50]}...")
                            # Filter out <thinking> blocks and file paths
                            filtered_text = content_filter.filter_chunk(block.text)
                            if filtered_text:
                                yield self._format_text(filtered_text)
                        if isinstance(block, ToolUseBlock):
                            tool_name = block.name
                            logger.error(f"DEBUG: ToolUseBlock: {tool_name}")
                            tool_input = getattr(block, 'input', {}) or {}
                            description = generate_tool_description(tool_name, tool_input)
                            yield self._format_data({"type": "tool_usage", "tool": tool_name, "description": description})
                            
                elif type(msg).__name__ == "ResultMessage":
                    # Flush any remaining buffered content
                    remaining = content_filter.flush()
                    if remaining:
                        yield self._format_text(remaining)
                    # Final result - already yielded via AssistantMessage
                    cost_info = {"duration_ms": msg.duration_ms, "cost": msg.total_cost_usd}
                    logger.error(f"DEBUG: ResultMessage: {cost_info}")
                    yield self._format_data({"type": "meta", "info": cost_info})
                    print(f"Agent finished. Duration: {msg.duration_ms}ms, Cost: ${msg.total_cost_usd:.4f}")
        except Exception as e:
            logger.error(f"Agent execution error: {e}")
            yield self._format_text(f"Error: {str(e)}")
