import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List

import httpx
from claude_agent_sdk import ClaudeAgentOptions, SandboxSettings
from claude_agent_sdk.types import AssistantMessage, TextBlock, ToolUseBlock
from backend.logging_config import get_logger
from backend.content_filter import StreamingContentFilter

logger = get_logger()


def generate_tool_description(tool_name: str, tool_input: Dict[str, Any]) -> str:
    """
    Generate a human-readable description of what a tool is doing based on its name and input.
    """
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
        self.provider = os.environ.get("AGENT_PROVIDER", "claude").strip().lower()
        self.anthropic_api_key = (os.environ.get("ANTHROPIC_API_KEY") or "").strip()
        self.anthropic_auth_token = (os.environ.get("ANTHROPIC_AUTH_TOKEN") or "").strip()
        self.base_url = os.environ.get("ANTHROPIC_BASE_URL")
        self.model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")
        self.codex_base_url = os.environ.get("OPENAI_BASE_URL", "").strip()
        self.codex_model = os.environ.get("OPENAI_MODEL", "gpt-5.3-codex")
        self.codex_auth_header_name = os.environ.get(
            "OPENAI_AUTH_HEADER_NAME", "Byted-Authorization"
        )
        self.codex_auth_header_value = os.environ.get("OPENAI_AUTH_HEADER_VALUE", "")
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

        ## Skill Routing Policy (MANDATORY)

        Prefer project-local skills before generic web tools when the task matches them.

        - Use **Skill: knowledge** for:
          - paper/library lookup, local retrieval, paper analysis/summaries
          - RAG/graph retrieval over local knowledge
          - local research workflows that can be answered from project data
        - Use **Skill: preference** for:
          - user preference signals, topic tendencies, preference-aware recommendations
          - tasks that require reading or applying learned user profile/history context

        If the user asks what skills/capabilities are available, use the Skill tool to enumerate skills first,
        then answer with what is actually available.

        Only fall back to WebSearch/WebFetch first when local/project skills cannot satisfy the request.
        
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

    def _validate_claude_auth_preflight(self) -> Optional[str]:
        """
        Deterministic preflight validation for Claude auth configuration.
        Fails fast before issuing any model request so auth blockers are explicit.
        """
        api_key = self.anthropic_api_key
        auth_token = self.anthropic_auth_token

        if api_key and not api_key.startswith("sk-ant-"):
            return (
                "Invalid ANTHROPIC_API_KEY format. Expected an Anthropic API key "
                "starting with 'sk-ant-'. If you are using OAuth, unset ANTHROPIC_API_KEY "
                "and use ANTHROPIC_AUTH_TOKEN instead."
            )
        if not api_key and not auth_token:
            return (
                "Missing Claude authentication. Set ANTHROPIC_API_KEY (sk-ant-*) "
                "or ANTHROPIC_AUTH_TOKEN before using provider=claude."
            )
        return None

    def _build_claude_sdk_env(self) -> Dict[str, str]:
        """
        Build an explicit env payload for the Claude SDK subprocess.
        Empty values intentionally mask inherited malformed credentials.
        """
        sdk_env: Dict[str, str] = {
            "ANTHROPIC_BASE_URL": self.base_url or "",
            "ANTHROPIC_API_KEY": "",
            "ANTHROPIC_AUTH_TOKEN": "",
        }
        if self.anthropic_api_key.startswith("sk-ant-"):
            sdk_env["ANTHROPIC_API_KEY"] = self.anthropic_api_key
        if self.anthropic_auth_token:
            sdk_env["ANTHROPIC_AUTH_TOKEN"] = self.anthropic_auth_token
        return sdk_env

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
        if self.provider == "codex_bridge":
            logger.info(
                "agent_provider_initialized",
                provider="codex_bridge",
                model=self.codex_model,
                model_source="server_startup_env",
                endpoint=self._codex_responses_url(),
            )
            return

        if not self.client:
            preflight_error = self._validate_claude_auth_preflight()
            if preflight_error:
                logger.error("claude_auth_preflight_failed", reason=preflight_error)
                raise RuntimeError(preflight_error)

            from claude_agent_sdk.client import ClaudeSDKClient
            
            sandbox_settings: SandboxSettings = {
                "enabled": True,
                "autoAllowBashIfSandboxed": True,
                "network": {
                    "allowLocalBinding": True
                }
            }

            # Only forward ANTHROPIC_API_KEY if it looks like a real API key.
            # If the env uses an OAuth-style token (e.g. "user.password"), omit
            # the API key so the bundled CLI falls back to its stored OAuth
            # credentials while still routing through ANTHROPIC_BASE_URL.
            sdk_env = self._build_claude_sdk_env()

            options = ClaudeAgentOptions(
                cwd=str(self.cwd),
                # Enable automatic SDK-native skill loading from both user and project scopes.
                setting_sources=["user", "project"],
                model=self.model,
                env=sdk_env,
                # Use composed prompt so profile/history wiring is active in runtime.
                system_prompt=self.get_system_prompt(),
                allowed_tools=["WebSearch", "WebFetch", "Task", "Read", "Write", "Bash", "Skill"],
                permission_mode="bypassPermissions",
                sandbox=sandbox_settings
            )
            
            self.client = ClaudeSDKClient(options=options)
            logger.info(
                "agent_provider_initialized",
                provider="claude_agent_sdk",
                model=self.model,
                model_source="server_startup_env",
            )
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
        
        OUTPUT FORMAT: SSE UI message chunks:
        data: {"type":"start"|...}\n\n
        """
        try:
            logger.error(f"DEBUG: chat_generator started for query: {query[:20]} session: {session_id}")
            async for msg in self.run(
                query, 
                chat_id=session_id, 
                user_preferences=user_preferences,
                conversation_history=conversation_history
            ):
                # self.run yields SSE-formatted data events.
                logger.error(f"DEBUG: chat_generator yielding chunk: {msg[:50]}...")
                yield msg
        except Exception as e:
            logger.error(f"Chat generator error: {e}")
            yield self._format_chunk({"type": "error", "errorText": str(e)})
            yield self._format_chunk({"type": "finish", "finishReason": "error"})

    def _format_chunk(self, chunk: Dict[str, Any]) -> str:
        """Encode a UI message chunk as SSE data event."""
        return f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

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
        if self.provider == "codex_bridge":
            async for chunk in self._run_codex_bridge(
                query=query,
                user_preferences=user_preferences,
                conversation_history=conversation_history,
            ):
                yield chunk
            return

        async for chunk in self._run_claude(
            query=query,
            chat_id=chat_id,
            user_preferences=user_preferences,
            conversation_history=conversation_history,
        ):
            yield chunk

    def _codex_responses_url(self) -> str:
        base = (self.codex_base_url or "").rstrip("/")
        if not base:
            return ""
        if base.endswith("/responses"):
            return base
        return f"{base}/responses"

    def _build_full_query(
        self,
        query: str,
        user_preferences: Optional[str],
        conversation_history: Optional[List[Dict[str, str]]],
    ) -> str:
        full_query = query
        lower_query = (query or "").lower()

        # Enforce local-skill-first routing for research-relevant asks.
        skill_routing_terms = [
            "skill",
            "paper",
            "library",
            "knowledge",
            "rag",
            "preference",
            "profile",
            "history",
            "recommend",
        ]
        if any(term in lower_query for term in skill_routing_terms):
            full_query = (
                "[MANDATORY TOOL ROUTING]\n"
                "1) Call Skill tool to enumerate available skills before final answer.\n"
                "2) Prefer knowledge/preference skills for local/project queries.\n"
                "3) If those skills are unavailable, explicitly state that in output.\n\n"
                f"User request: {query}"
            )

        if conversation_history and len(conversation_history) > 0:
            history_context = "\n\n[Prior Conversation History - Please continue this conversation]\n"
            for msg in conversation_history:
                role_label = "User" if msg.get("role") == "user" else "Assistant"
                content = msg.get("content", "")
                if len(content) > 2000:
                    content = content[:2000] + "... [truncated]"
                history_context += f"\n{role_label}: {content}\n"
            history_context += "\n[End of History - Now responding to new message]\n\n"
            full_query = history_context + f"User: {query}"
        if user_preferences:
            full_query += f"\n\n[User Context Preferences]\n{user_preferences}"
        return full_query

    async def _run_claude(
        self,
        query: str,
        chat_id: str,
        user_preferences: Optional[str],
        conversation_history: Optional[List[Dict[str, str]]],
    ):
        if not self.client:
            await self.initialize()

        full_query = self._build_full_query(query, user_preferences, conversation_history)

        # Send query to SDK
        await self.client.query(full_query, session_id=chat_id)

        content_filter = StreamingContentFilter()
        text_part_id = "text-1"
        tool_counter = 0

        try:
            yield self._format_chunk({"type": "start"})
            yield self._format_chunk({"type": "start-step"})
            yield self._format_chunk({"type": "text-start", "id": text_part_id})

            async for msg in self.client.receive_response():
                logger.error(f"DEBUG: Agent yielded message type: {type(msg).__name__}")
                if isinstance(msg, AssistantMessage):
                    logger.error(f"DEBUG: AssistantMessage blocks: {len(msg.content)}")
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            logger.error(f"DEBUG: TextBlock content: {block.text[:50]}...")
                            filtered_text = content_filter.filter_chunk(block.text)
                            if filtered_text:
                                yield self._format_chunk(
                                    {
                                        "type": "text-delta",
                                        "id": text_part_id,
                                        "delta": filtered_text,
                                    }
                                )
                        if isinstance(block, ToolUseBlock):
                            tool_name = block.name
                            logger.error(f"DEBUG: ToolUseBlock: {tool_name}")
                            tool_input = getattr(block, "input", {}) or {}
                            description = generate_tool_description(tool_name, tool_input)
                            tool_counter += 1
                            tool_call_id = getattr(block, "id", None) or f"tool-{tool_counter}"
                            yield self._format_chunk(
                                {
                                    "type": "tool-input-start",
                                    "toolCallId": tool_call_id,
                                    "toolName": tool_name,
                                    "title": description,
                                }
                            )
                            yield self._format_chunk(
                                {
                                    "type": "tool-input-available",
                                    "toolCallId": tool_call_id,
                                    "toolName": tool_name,
                                    "input": tool_input,
                                    "title": description,
                                }
                            )
                            yield self._format_chunk(
                                {
                                    "type": "tool-output-available",
                                    "toolCallId": tool_call_id,
                                    "output": {"description": description},
                                }
                            )

                elif type(msg).__name__ == "ResultMessage":
                    remaining = content_filter.flush()
                    if remaining:
                        yield self._format_chunk(
                            {
                                "type": "text-delta",
                                "id": text_part_id,
                                "delta": remaining,
                            }
                        )
                    cost_info = {"duration_ms": msg.duration_ms, "cost": msg.total_cost_usd}
                    logger.error(f"DEBUG: ResultMessage: {cost_info}")
                    yield self._format_chunk({"type": "text-end", "id": text_part_id})
                    yield self._format_chunk({"type": "finish-step"})
                    yield self._format_chunk({"type": "data-metrics", "data": cost_info})
                    yield self._format_chunk(
                        {
                            "type": "finish",
                            "finishReason": "stop",
                            "messageMetadata": cost_info,
                        }
                    )
                    print(f"Agent finished. Duration: {msg.duration_ms}ms, Cost: ${msg.total_cost_usd:.4f}")
        except Exception as e:
            logger.error(f"Agent execution error: {e}")
            yield self._format_chunk({"type": "error", "errorText": str(e)})
            yield self._format_chunk({"type": "text-end", "id": text_part_id})
            yield self._format_chunk({"type": "finish-step"})
            yield self._format_chunk({"type": "finish", "finishReason": "error"})

    async def _run_codex_bridge(
        self,
        query: str,
        user_preferences: Optional[str],
        conversation_history: Optional[List[Dict[str, str]]],
    ):
        full_query = self._build_full_query(query, user_preferences, conversation_history)
        text_part_id = "text-1"
        started = False
        finished = False
        usage_info: Dict[str, Any] = {}

        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if self.codex_auth_header_name and self.codex_auth_header_value:
            headers[self.codex_auth_header_name] = self.codex_auth_header_value
        elif os.getenv("OPENAI_API_KEY"):
            headers["Authorization"] = f"Bearer {os.getenv('OPENAI_API_KEY')}"

        payload: Dict[str, Any] = {
            "model": self.codex_model,
            "input": full_query,
            "stream": True,
        }

        responses_url = self._codex_responses_url()
        if not responses_url:
            yield self._format_chunk(
                {
                    "type": "error",
                    "errorText": "Missing OPENAI_BASE_URL for codex_bridge provider",
                }
            )
            yield self._format_chunk({"type": "finish", "finishReason": "error"})
            return

        if not any(k.lower() in ("authorization", "byted-authorization") for k in headers):
            yield self._format_chunk(
                {
                    "type": "error",
                    "errorText": "Missing bridge authentication: set OPENAI_AUTH_HEADER_* or OPENAI_API_KEY",
                }
            )
            yield self._format_chunk({"type": "finish", "finishReason": "error"})
            return

        def emit_start():
            nonlocal started
            if started:
                return []
            started = True
            return [
                self._format_chunk({"type": "start"}),
                self._format_chunk({"type": "start-step"}),
                self._format_chunk({"type": "text-start", "id": text_part_id}),
            ]

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                async with client.stream(
                    "POST",
                    responses_url,
                    headers=headers,
                    json=payload,
                ) as response:
                    if response.status_code >= 400:
                        body = (await response.aread()).decode("utf-8", errors="replace")
                        yield self._format_chunk(
                            {
                                "type": "error",
                                "errorText": f"Codex bridge error {response.status_code}: {body[:300]}",
                            }
                        )
                        yield self._format_chunk({"type": "finish", "finishReason": "error"})
                        return

                    current_event: Optional[str] = None
                    data_lines: List[str] = []

                    async for raw_line in response.aiter_lines():
                        line = raw_line.strip()
                        if not line:
                            if not data_lines:
                                current_event = None
                                continue
                            data_blob = "\n".join(data_lines)
                            data_lines = []
                            if not data_blob:
                                current_event = None
                                continue
                            try:
                                event_payload = json.loads(data_blob)
                            except Exception:
                                current_event = None
                                continue

                            event_type = current_event or event_payload.get("type")
                            if event_type == "response.created":
                                for chunk in emit_start():
                                    yield chunk
                            elif event_type == "response.output_text.delta":
                                for chunk in emit_start():
                                    yield chunk
                                delta = event_payload.get("delta", "")
                                if isinstance(delta, str) and delta:
                                    yield self._format_chunk(
                                        {
                                            "type": "text-delta",
                                            "id": text_part_id,
                                            "delta": delta,
                                        }
                                    )
                            elif event_type == "response.completed":
                                response_obj = event_payload.get("response", {})
                                if isinstance(response_obj, dict):
                                    usage = response_obj.get("usage")
                                    if isinstance(usage, dict):
                                        usage_info = usage
                                for chunk in emit_start():
                                    yield chunk
                                yield self._format_chunk({"type": "text-end", "id": text_part_id})
                                yield self._format_chunk({"type": "finish-step"})
                                if usage_info:
                                    yield self._format_chunk(
                                        {"type": "data-metrics", "data": usage_info}
                                    )
                                yield self._format_chunk(
                                    {
                                        "type": "finish",
                                        "finishReason": "stop",
                                        "messageMetadata": usage_info or {},
                                    }
                                )
                                finished = True
                            current_event = None
                            continue

                        if line.startswith("event:"):
                            current_event = line[6:].strip()
                        elif line.startswith("data:"):
                            data_lines.append(line[5:].strip())

            except Exception as e:
                logger.error(f"Codex bridge execution error: {e}")
                for chunk in emit_start():
                    yield chunk
                yield self._format_chunk({"type": "error", "errorText": str(e)})
                yield self._format_chunk({"type": "text-end", "id": text_part_id})
                yield self._format_chunk({"type": "finish-step"})
                yield self._format_chunk({"type": "finish", "finishReason": "error"})
                return

        if not finished:
            for chunk in emit_start():
                yield chunk
            yield self._format_chunk({"type": "text-end", "id": text_part_id})
            yield self._format_chunk({"type": "finish-step"})
            yield self._format_chunk(
                {
                    "type": "finish",
                    "finishReason": "stop",
                    "messageMetadata": usage_info or {},
                }
            )
