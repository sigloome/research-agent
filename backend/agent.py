import json
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

import httpx
from backend.logging_config import get_logger
from backend.codex_sdk_runtime import stream_codex_sdk
from backend.multi_agent_runtime import MultiAgentRuntime, RuntimeProfile

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
    Main AI Agent using local Codex SDK adapter runtime.
    
    This is the single unified agent that handles all tasks including research.
    Uses built-in SDK tools (WebSearch, WebFetch, Read, Write, Bash) directly.
    """
    
    def __init__(self):
        # Single-provider runtime: local Codex SDK adapter.
        self.provider = "codex_sdk"
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
        self.max_tool_turns = 6
        self.max_http_retries = int(os.environ.get("BRIDGE_MAX_HTTP_RETRIES", "1"))
        self.http_timeout_seconds = float(os.environ.get("BRIDGE_HTTP_TIMEOUT_SECONDS", "120"))
        self.multi_agent_runtime = MultiAgentRuntime()

    def _is_skill_routed_query(self, query: str) -> bool:
        """Detect whether a query should prioritize local skill runtime."""
        lower_query = (query or "").lower()
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
        return any(term in lower_query for term in skill_routing_terms)

    def _should_enforce_skill_routing(self, query: str) -> bool:
        """
        Determine whether strict skill/tool enforcement is required.

        Default mode is on-demand tools. Strict mode is enabled only when:
        1) explicit env flag is on, or
        2) user prompt explicitly demands skill-first/tool use.
        """
        env_force = os.environ.get("RESEARCH_STRICT_SKILL_ROUTING", "").strip().lower()
        if env_force in {"1", "true", "yes", "on"}:
            return True

        lower_query = (query or "").lower()
        explicit_phrases = [
            "use skill tool",
            "list available skills first",
            "must use knowledge",
            "must use preference",
            "knowledge and preference",
            "strict skill routing",
        ]
        return any(phrase in lower_query for phrase in explicit_phrases)

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
        """Initialize single-provider runtime."""
        logger.info(
            "agent_provider_initialized",
            provider=self.provider,
            model=self.codex_model,
            model_source="server_startup_env",
            endpoint="local://codex-sdk-adapter",
        )

    async def chat_generator(
        self, 
        query: str, 
        session_id: str = "default", 
        user_preferences: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        runtime_profile: Optional[RuntimeProfile] = None,
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
            async for msg in self.run(
                query, 
                chat_id=session_id, 
                user_preferences=user_preferences,
                conversation_history=conversation_history,
                runtime_profile=runtime_profile,
            ):
                yield msg
        except Exception as e:
            logger.error(f"Chat generator error: {e}")
            yield self._format_chunk({"type": "error", "errorText": str(e)})
            yield self._format_chunk({"type": "finish", "finishReason": "error"})

    def _format_chunk(self, chunk: Dict[str, Any]) -> str:
        """Encode a UI message chunk as SSE data event."""
        return f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

    def _format_trace_event(
        self,
        trace_id: str,
        role: str,
        stage: str,
        status: str,
        latency_ms: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> str:
        payload: Dict[str, Any] = {
            "type": "agent-trace",
            "traceId": trace_id,
            "role": role,
            "stage": stage,
            "status": status,
        }
        if latency_ms is not None:
            payload["latencyMs"] = latency_ms
        if details:
            payload["details"] = details
        return self._format_chunk(payload)

    async def run(
        self, 
        query: str, 
        chat_id: str, 
        user_preferences: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        runtime_profile: Optional[RuntimeProfile] = None,
    ):
        """
        Internal async generator to run the agent and yield formatted messages.
        
        conversation_history: List of prior messages to include as context.
                             This is used when resuming a historical chat session
                             that the SDK doesn't have in memory.
        """
        async for chunk in self._run_codex_sdk(
            query=query,
            user_preferences=user_preferences,
            conversation_history=conversation_history,
            runtime_profile=runtime_profile,
        ):
            yield chunk

    async def _run_codex_sdk(
        self,
        query: str,
        user_preferences: Optional[str],
        conversation_history: Optional[List[Dict[str, str]]],
        runtime_profile: Optional[RuntimeProfile],
    ):
        full_query = self._build_full_query(
            query=query,
            user_preferences=user_preferences,
            conversation_history=conversation_history,
        )
        _ = runtime_profile
        async for chunk in stream_codex_sdk(
            format_chunk=self._format_chunk,
            query=full_query,
            cwd=self.cwd,
            codex_model=self.codex_model,
        ):
            yield chunk

    def _codex_responses_url(self) -> str:
        base = (self.codex_base_url or "").rstrip("/")
        if not base:
            return ""
        if base.endswith("/responses"):
            return base
        return f"{base}/responses"

    def _build_bridge_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if self.codex_auth_header_name and self.codex_auth_header_value:
            headers[self.codex_auth_header_name] = self.codex_auth_header_value
        elif os.getenv("OPENAI_API_KEY"):
            headers["Authorization"] = f"Bearer {os.getenv('OPENAI_API_KEY')}"
        return headers

    def _bridge_auth_preflight_error(self, headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
        responses_url = self._codex_responses_url()
        if not responses_url:
            return {"type": "error", "errorText": "Missing OPENAI_BASE_URL for codex_bridge provider"}
        if not any(k.lower() in ("authorization", "byted-authorization") for k in headers):
            return {
                "type": "error",
                "errorText": "Missing bridge authentication: set OPENAI_AUTH_HEADER_* or OPENAI_API_KEY",
            }
        return None

    def _build_bridge_payload(
        self,
        input_data: Any,
        user_preferences: Optional[str],
        active_tools: List[Dict[str, Any]],
        enforce_skill_routing: bool,
        first_turn: bool,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": self.codex_model,
            "input": input_data,
            "stream": True,
            "instructions": self.get_system_prompt(user_preferences),
        }
        if active_tools:
            payload["tools"] = active_tools
        if enforce_skill_routing and first_turn and active_tools:
            payload["tool_choice"] = "required"
        return payload

    def _build_full_query(
        self,
        query: str,
        user_preferences: Optional[str],
        conversation_history: Optional[List[Dict[str, str]]],
    ) -> str:
        full_query = query

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

    def _build_bridge_tools(self) -> List[Dict[str, Any]]:
        """Declare function tools for the bridge runtime."""
        return [
            {
                "type": "function",
                "name": "Skill",
                "description": (
                    "Invoke project skills. Use action=list to enumerate skills. "
                    "Use skill=knowledge or skill=preference for local project context."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["list", "read", "run"],
                            "description": "list skills, read a skill, or run a named skill",
                        },
                        "skill": {
                            "type": "string",
                            "description": "Skill name such as knowledge or preference",
                        },
                        "query": {
                            "type": "string",
                            "description": "Query payload for the skill",
                        },
                        "args": {
                            "type": "object",
                            "description": "Optional structured arguments for skill execution",
                        },
                        "skill_path": {
                            "type": "string",
                            "description": "Path/name used by read action",
                        },
                    },
                    "required": ["action"],
                    "additionalProperties": True,
                },
            }
        ]

    def _extract_tool_calls(self, response_obj: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract function calls from a completed response object."""
        output = response_obj.get("output", [])
        if not isinstance(output, list):
            return []

        calls: List[Dict[str, Any]] = []
        for item in output:
            if not isinstance(item, dict):
                continue
            item_type = item.get("type")
            if item_type not in ("function_call", "tool_call"):
                continue
            name = item.get("name")
            if not isinstance(name, str) or not name:
                continue
            call_id = item.get("call_id") or item.get("id") or f"tool-{len(calls) + 1}"
            raw_args = item.get("arguments", {})
            args: Dict[str, Any] = {}
            if isinstance(raw_args, str):
                try:
                    parsed = json.loads(raw_args)
                    if isinstance(parsed, dict):
                        args = parsed
                except Exception:
                    args = {"raw": raw_args}
            elif isinstance(raw_args, dict):
                args = raw_args
            calls.append(
                {
                    "tool_call_id": str(call_id),
                    "tool_name": name,
                    "input": args,
                }
            )
        return calls

    def _run_skill_tool(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the Skill tool via project runtime modules.
        No manual SKILL.md content injection is used.
        """
        import importlib

        skill_mgmt = importlib.import_module("skills.skill-management.core")
        action = str(tool_input.get("action", "run")).strip().lower()
        skill_name = str(
            tool_input.get("skill")
            or tool_input.get("skill_name")
            or tool_input.get("name")
            or ""
        ).strip()

        if action == "list":
            skills = skill_mgmt.list_skills()
            return {"action": "list", "skills": skills}

        if action == "read":
            target = str(tool_input.get("skill_path") or skill_name or "").strip()
            if not target:
                return {"error": "read action requires skill_path or skill"}
            content = skill_mgmt.read_skill(target)
            return {"action": "read", "target": target, "content": content}

        args = tool_input.get("args")
        if not isinstance(args, dict):
            args = {}
        query = str(
            tool_input.get("query")
            or args.get("query")
            or args.get("prompt")
            or args.get("topic")
            or ""
        ).strip()

        if skill_name == "knowledge":
            from skills.knowledge.db import manager
            from skills.knowledge.paper import core as paper_core

            op = str(args.get("op") or args.get("action") or "").strip().lower()
            source = str(args.get("source") or query or "").strip()
            if op in {"paper_ingest", "ingest"}:
                ingest = paper_core.paper_ingest(
                    source=source,
                    force_update=bool(args.get("force_update", False)),
                )
                return {
                    "skill": "knowledge",
                    "op": "paper_ingest",
                    "source": source,
                    "result": ingest,
                }

            if query:
                papers = manager.search_local_papers(query)
            else:
                papers = manager.list_papers(sort_by="created_at_desc")
            compact = []
            for row in (papers or [])[:8]:
                if not isinstance(row, dict):
                    continue
                compact.append(
                    {
                        "id": row.get("id"),
                        "title": row.get("title"),
                        "summary": row.get("summary_main_ideas"),
                        "url": row.get("url"),
                    }
                )
            return {
                "skill": "knowledge",
                "query": query,
                "result_count": len(compact),
                "results": compact,
            }

        if skill_name == "preference":
            from skills.knowledge.db import manager
            from skills.preference.implementation import get_user_history, get_user_profile

            summary = manager.get_preference_summary()
            profile = get_user_profile()
            history = get_user_history()
            return {
                "skill": "preference",
                "summary": summary,
                "profile": profile,
                "history": history,
            }

        if skill_name:
            return {
                "error": f"Unsupported skill: {skill_name}",
                "supported_skills": ["knowledge", "preference"],
            }
        return {"error": "run action requires skill name"}

    async def _run_codex_bridge(
        self,
        query: str,
        user_preferences: Optional[str],
        conversation_history: Optional[List[Dict[str, str]]],
        runtime_profile: Optional[RuntimeProfile],
    ):
        full_query = self._build_full_query(query, user_preferences, conversation_history)
        trace_id = f"trace-{int(time.time() * 1000)}"
        if runtime_profile is not None:
            runtime_result = await self.multi_agent_runtime.run(
                query=query,
                profile=runtime_profile,
                user_preferences=user_preferences,
            )
            full_query = (
                f"{full_query}\n\n"
                f"{runtime_result.answer_context}\n\n"
                f"Verifier summary: {runtime_result.verifier_summary}"
            )
        else:
            runtime_result = None
        text_part_id = "text-1"
        started = False
        usage_info: Dict[str, Any] = {}
        observed_skill_tool = False
        skill_routed_query = self._is_skill_routed_query(query)
        enforce_skill_routing = self._should_enforce_skill_routing(query)

        headers = self._build_bridge_headers()
        preflight_error = self._bridge_auth_preflight_error(headers)
        responses_url = self._codex_responses_url()
        if preflight_error is not None:
            yield self._format_chunk(
                preflight_error
            )
            yield self._format_chunk({"type": "finish", "finishReason": "error"})
            return

        def emit_start():
            nonlocal started
            if started:
                return []
            chunks = [
                self._format_chunk({"type": "start"}),
                self._format_chunk({"type": "start-step"}),
                self._format_chunk({"type": "text-start", "id": text_part_id}),
            ]
            if runtime_result is not None:
                for envelope in runtime_result.handoffs:
                    chunks.append(
                        self._format_trace_event(
                            trace_id=trace_id,
                            role=envelope.role.value,
                            stage="handoff",
                            status="ok" if envelope.ok else "error",
                            latency_ms=envelope.latency_ms,
                            details={
                                "fallback_used": envelope.fallback_used,
                                "error_code": envelope.error.code if envelope.error else None,
                            },
                        )
                    )
            started = True
            return chunks

        tool_outputs_for_next_turn: Any = full_query
        bridge_tools = self._build_bridge_tools()
        exhausted_tool_turns = True
        final_context_prompt: Optional[str] = None
        first_turn = True

        async with httpx.AsyncClient(timeout=self.http_timeout_seconds) as client:
            try:
                for _ in range(self.max_tool_turns):
                    active_tools = bridge_tools if final_context_prompt is None else []
                    payload = self._build_bridge_payload(
                        input_data=tool_outputs_for_next_turn,
                        user_preferences=user_preferences,
                        active_tools=active_tools,
                        enforce_skill_routing=enforce_skill_routing,
                        first_turn=first_turn,
                    )

                    completed_response: Optional[Dict[str, Any]] = None
                    current_event: Optional[str] = None
                    data_lines: List[str] = []

                    attempt = 0
                    while True:
                        try:
                            async with client.stream(
                                "POST",
                                responses_url,
                                headers=headers,
                                json=payload,
                            ) as response:
                                if response.status_code >= 500 and attempt < self.max_http_retries:
                                    attempt += 1
                                    continue
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
                                                completed_response = response_obj
                                                usage = response_obj.get("usage")
                                                if isinstance(usage, dict):
                                                    usage_info = usage
                                        current_event = None
                                        continue

                                    if line.startswith("event:"):
                                        current_event = line[6:].strip()
                                    elif line.startswith("data:"):
                                        data_lines.append(line[5:].strip())
                            break
                        except (httpx.ReadTimeout, httpx.ConnectTimeout):
                            if attempt < self.max_http_retries:
                                attempt += 1
                                continue
                            yield self._format_chunk(
                                {
                                    "type": "error",
                                    "errorText": "Codex bridge timeout after retry; returning error envelope",
                                }
                            )
                            yield self._format_chunk({"type": "finish", "finishReason": "error"})
                            return

                    if not completed_response:
                        break

                    tool_calls = self._extract_tool_calls(completed_response)
                    if not tool_calls:
                        exhausted_tool_turns = False
                        break

                    if enforce_skill_routing:
                        has_knowledge = False
                        has_preference = False
                        for call in tool_calls:
                            if call.get("tool_name") != "Skill":
                                continue
                            tool_input = call.get("input", {})
                            if not isinstance(tool_input, dict):
                                continue
                            if str(tool_input.get("action", "")).strip().lower() != "run":
                                continue
                            skill_name = str(tool_input.get("skill", "")).strip().lower()
                            if skill_name == "knowledge":
                                has_knowledge = True
                            if skill_name == "preference":
                                has_preference = True

                        if not has_knowledge:
                            tool_calls.append(
                                {
                                    "tool_call_id": "policy-knowledge",
                                    "tool_name": "Skill",
                                    "input": {
                                        "action": "run",
                                        "skill": "knowledge",
                                        "query": "Summarize what is known about the user's profile/history from local project knowledge.",
                                    },
                                }
                            )
                        if not has_preference:
                            tool_calls.append(
                                {
                                    "tool_call_id": "policy-preference",
                                    "tool_name": "Skill",
                                    "input": {
                                        "action": "run",
                                        "skill": "preference",
                                        "query": "Summarize known user profile/history and preferences.",
                                    },
                                }
                            )

                    executed_tools: List[Dict[str, Any]] = []
                    for call in tool_calls:
                        tool_name = call["tool_name"]
                        call_id = call["tool_call_id"]
                        tool_input = call["input"]

                        if tool_name == "Skill":
                            observed_skill_tool = True
                        yield self._format_chunk(
                            {
                                "type": "tool-input-start",
                                "toolCallId": call_id,
                                "toolName": tool_name,
                            }
                        )
                        yield self._format_chunk(
                            {
                                "type": "tool-input-available",
                                "toolCallId": call_id,
                                "toolName": tool_name,
                                "input": tool_input,
                            }
                        )

                        try:
                            if tool_name == "Skill":
                                tool_output_obj = self._run_skill_tool(tool_input)
                            else:
                                tool_output_obj = {"error": f"Unsupported tool: {tool_name}"}
                        except Exception as tool_error:
                            tool_output_obj = {"error": f"Tool execution failed: {tool_error}"}

                        yield self._format_chunk(
                            {
                                "type": "tool-output-available",
                                "toolCallId": call_id,
                                "output": tool_output_obj,
                            }
                        )
                        executed_tools.append(
                            {
                                "tool_name": tool_name,
                                "tool_call_id": call_id,
                                "input": tool_input,
                                "output": tool_output_obj,
                            }
                        )

                    final_context_prompt = (
                        "Use the following tool outputs to answer the original user request. "
                        "Do not call tools again; provide the final response directly.\n\n"
                        f"Original request:\n{query}\n\n"
                        "Tool outputs (JSON):\n"
                        f"{json.dumps(executed_tools, ensure_ascii=False)}"
                    )
                    tool_outputs_for_next_turn = final_context_prompt
                    first_turn = False

            except Exception as e:
                logger.error(f"Codex bridge execution error: {e}")
                for chunk in emit_start():
                    yield chunk
                yield self._format_chunk({"type": "error", "errorText": str(e)})
                yield self._format_chunk({"type": "text-end", "id": text_part_id})
                yield self._format_chunk({"type": "finish-step"})
                yield self._format_chunk({"type": "finish", "finishReason": "error"})
                return

        if exhausted_tool_turns:
            for chunk in emit_start():
                yield chunk
            yield self._format_chunk(
                {
                    "type": "error",
                    "errorText": (
                        f"Codex bridge exceeded max tool turns ({self.max_tool_turns}) "
                        "without reaching a completion turn."
                    ),
                }
            )
            yield self._format_chunk({"type": "text-end", "id": text_part_id})
            yield self._format_chunk({"type": "finish-step"})
            yield self._format_chunk({"type": "finish", "finishReason": "error"})
            return

        if enforce_skill_routing and not observed_skill_tool:
            for chunk in emit_start():
                yield chunk
            yield self._format_chunk(
                {
                    "type": "error",
                    "errorText": (
                        "Skill-routed request completed without Skill tool invocation; "
                        "bridge tool-routing requirement not satisfied."
                    ),
                }
            )
            yield self._format_chunk({"type": "text-end", "id": text_part_id})
            yield self._format_chunk({"type": "finish-step"})
            yield self._format_chunk(
                {
                    "type": "finish",
                    "finishReason": "error",
                    "messageMetadata": usage_info or {},
                }
            )
            return

        for chunk in emit_start():
            yield chunk
        yield self._format_chunk({"type": "text-end", "id": text_part_id})
        yield self._format_chunk({"type": "finish-step"})
        if usage_info:
            yield self._format_chunk({"type": "data-metrics", "data": usage_info})
        yield self._format_chunk(
            {
                "type": "finish",
                "finishReason": "stop",
                "messageMetadata": usage_info or {},
            }
        )
