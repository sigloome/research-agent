"""Content filter for separating internal reasoning from user-facing content.

This module provides streaming-compatible filtering that:
1. Removes hidden tags: <thinking>, <private>, <debug>
2. Transforms display tags: <citation>, <summary>, <source>
3. Removes sensitive file paths (e.g., /Users/...)
4. Cleans up resulting whitespace

Supported XML Tags:
- <thinking>: Internal reasoning, process narration (HIDDEN)
- <private>: Sensitive data like file paths, credentials (HIDDEN)
- <debug>: Development/debug info (HIDDEN)
- <citation>: Source citations with optional url attribute (TRANSFORMED)
- <summary>: Summary sections (TRANSFORMED)
- <source>: Source metadata (TRANSFORMED)

The filter is designed to work with streaming responses, buffering
content at tag boundaries to ensure proper parsing.
"""

import re
from typing import Optional


class ContentFilter:
    """
    Filters agent output by:
    - Removing hidden tags: <thinking>, <private>, <debug>
    - Transforming display tags: <citation>, <summary>, <source>
    - Removing sensitive local file paths (fallback safety)
    
    Thread-safe for single-stream use. Create a new instance per stream.
    """
    
    # === HIDDEN TAGS (content removed entirely) ===
    
    # Match <thinking>...</thinking> including multiline content
    THINKING_TAG = re.compile(
        r'<thinking>.*?</thinking>',
        re.DOTALL | re.IGNORECASE
    )
    
    # Match <private>...</private> for sensitive data
    PRIVATE_TAG = re.compile(
        r'<private>.*?</private>',
        re.DOTALL | re.IGNORECASE
    )
    
    # Match <debug>...</debug> for dev/debug info
    DEBUG_TAG = re.compile(
        r'<debug>.*?</debug>',
        re.DOTALL | re.IGNORECASE
    )
    
    # === DISPLAY TAGS (transformed for rendering) ===
    
    # Match <citation url="...">...</citation> or <citation>...</citation>
    # Captures: url (optional), content
    CITATION_TAG = re.compile(
        r'<citation(?:\s+url=["\']([^"\']+)["\'])?\s*>(.*?)</citation>',
        re.DOTALL | re.IGNORECASE
    )
    
    # Match <summary>...</summary>
    SUMMARY_TAG = re.compile(
        r'<summary>(.*?)</summary>',
        re.DOTALL | re.IGNORECASE
    )
    
    # Match <source url="...">...</source> or <source>...</source>
    SOURCE_TAG = re.compile(
        r'<source(?:\s+url=["\']([^"\']+)["\'])?\s*>(.*?)</source>',
        re.DOTALL | re.IGNORECASE
    )
    
    # === FALLBACK PATTERNS ===
    
    # Remove absolute paths that might slip through
    ABSOLUTE_PATH_PATTERNS = [
        re.compile(r'^Stored locally:\s*\n?', re.MULTILINE),
        re.compile(r'^/(?:Users|home|var|tmp)/[^\s\n]+\s*$', re.MULTILINE),
        re.compile(r'`/(?:Users|home|var|tmp)/[^`]+`'),  # Paths in backticks
    ]
    
    # Clean up multiple newlines
    MULTIPLE_NEWLINES = re.compile(r'\n{3,}')
    LEADING_PROCESS_LINES = [
        re.compile(
            r'^\s*(?:I(?: am|\'m|’m| will|\'ll|’ll| have|\'ve|’ve)|Let me|Next I(?:\'ll|’ll| will)|Now I(?:\'ll|’ll| will))\b[^\n]*\n?',
            re.IGNORECASE,
        ),
        re.compile(
            r'^\s*(?:Searching|Reading|Fetching|Loading|Checking|Using|Running|Switching)\b[^\n]*\n?',
            re.IGNORECASE,
        ),
    ]
    LEADING_PROCESS_SENTENCE_CUES = [
        re.compile(r'^(?:I(?: am|\'m|’m| will|\'ll|’ll| have|\'ve|’ve)\b|Let me\b|Next I\b|Now I\b)', re.IGNORECASE),
        re.compile(r'^(?:Searching|Reading|Fetching|Loading|Checking|Using|Running|Switching|Retrying|Querying|Inspecting|Executing)\b', re.IGNORECASE),
    ]
    PROCESS_SENTENCE_KEYWORDS = (
        "checking",
        "retrying",
        "executing",
        "switching",
        "querying",
        "loading",
        "using the",
        "using built-in",
        "module path",
        "runtime",
        "cli search",
        "local-paper search",
        "knowledge database",
        "now i'm",
        "now i’m",
        "next i'll",
        "next i’ll",
        "i tried using",
        "i used",
        "repo's",
        "tool,",
        "tool ",
        "blocked in this environment",
        "access is blocked",
    )
    
    def _transform_citation(self, match: re.Match) -> str:
        """Transform <citation> tag to markdown format."""
        url = match.group(1)
        content = match.group(2).strip()
        
        if url:
            # Format as markdown link with citation styling
            return f"[{content}]({url})"
        else:
            # Just return the content with emphasis
            return f"*{content}*"
    
    def _transform_summary(self, match: re.Match) -> str:
        """Transform <summary> tag to markdown blockquote."""
        content = match.group(1).strip()
        # Format as blockquote for visual distinction
        lines = content.split('\n')
        quoted = '\n'.join(f"> {line}" for line in lines)
        return f"\n{quoted}\n"
    
    def _transform_source(self, match: re.Match) -> str:
        """Transform <source> tag to markdown format."""
        url = match.group(1)
        content = match.group(2).strip()
        
        if url:
            # Format as a source reference with link
            return f"\n📄 **Source**: [{content}]({url})\n"
        else:
            # Just format as source reference
            return f"\n📄 **Source**: {content}\n"
    
    def filter_text(self, text: str) -> str:
        """
        Remove hidden blocks and transform display blocks.
        
        Args:
            text: Raw text from the LLM response
            
        Returns:
            Filtered and transformed text ready for display
        """
        if not text:
            return text
        
        result = text
        
        # 1. Remove hidden tags (order matters - remove first)
        result = self.THINKING_TAG.sub('', result)
        result = self.PRIVATE_TAG.sub('', result)
        result = self.DEBUG_TAG.sub('', result)
        
        # 2. Transform display tags to markdown
        result = self.CITATION_TAG.sub(self._transform_citation, result)
        result = self.SUMMARY_TAG.sub(self._transform_summary, result)
        result = self.SOURCE_TAG.sub(self._transform_source, result)
        
        # 3. Fallback: Remove any absolute file paths
        for pattern in self.ABSOLUTE_PATH_PATTERNS:
            result = pattern.sub('', result)
        
        # 4. Clean up extra whitespace
        result = self.MULTIPLE_NEWLINES.sub('\n\n', result)
        result = self._strip_leading_process_narration(result)
        result = self._strip_process_paragraphs(result)
        result = self.MULTIPLE_NEWLINES.sub('\n\n', result)
        result = result.strip()
        
        return result

    def _strip_leading_process_narration(self, text: str) -> str:
        result = text or ""
        changed = True
        while changed and result:
            changed = False
            stripped = result.lstrip()
            leading_offset = len(result) - len(stripped)
            result = stripped if leading_offset else result
            for pattern in self.LEADING_PROCESS_LINES:
                match = pattern.match(result)
                if match:
                    result = result[match.end():]
                    changed = True
                    break
            if changed:
                continue

            sentence_end = self._find_sentence_end(result)
            if sentence_end is None:
                break
            candidate = result[:sentence_end].strip()
            if self._looks_like_process_sentence(candidate):
                result = result[sentence_end:].lstrip()
                changed = True
        return result

    def _find_sentence_end(self, text: str) -> Optional[int]:
        for idx, char in enumerate(text):
            if char == "\n" and idx + 1 < len(text) and text[idx + 1] == "\n":
                return idx
            if char in ".!?":
                next_idx = idx + 1
                if next_idx >= len(text) or text[next_idx].isspace():
                    return next_idx
        return None

    def _looks_like_process_sentence(self, sentence: str) -> bool:
        if not sentence:
            return False
        normalized = sentence.strip()
        for pattern in self.LEADING_PROCESS_SENTENCE_CUES:
            if pattern.match(normalized):
                lowered = normalized.lower()
                return any(keyword in lowered for keyword in self.PROCESS_SENTENCE_KEYWORDS)
        lowered = normalized.lower()
        return any(keyword in lowered for keyword in self.PROCESS_SENTENCE_KEYWORDS[:8])

    def _strip_process_paragraphs(self, text: str) -> str:
        if not text:
            return text

        kept: list[str] = []
        paragraphs = re.split(r"\n\s*\n", text)
        for paragraph in paragraphs:
            stripped = paragraph.strip()
            if not stripped:
                continue
            if self._is_process_paragraph(stripped):
                continue
            kept.append(stripped)
        return "\n\n".join(kept)

    def _is_process_paragraph(self, paragraph: str) -> bool:
        lowered = paragraph.lower()
        if (
            "tool" in lowered
            or "environment" in lowered
            or "repo" in lowered
            or "access is blocked" in lowered
        ) and any(
            cue in lowered
            for cue in ("i tried", "i'm", "i’m", "i used", "i checked", "i found", "i ran")
        ):
            return True

        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", paragraph)
            if sentence.strip()
        ]
        if sentences and all(self._looks_like_process_sentence(sentence) for sentence in sentences):
            return True
        return False


class StreamingContentFilter:
    """
    Streaming-aware filter that buffers content at tag boundaries.
    
    This filter handles the case where XML tags may be split
    across multiple streaming chunks.
    
    Supported tags:
    - Hidden: <thinking>, <private>, <debug>
    - Display: <citation>, <summary>, <source>
    
    Usage:
        filter = StreamingContentFilter()
        for chunk in stream:
            filtered = filter.filter_chunk(chunk)
            if filtered:
                yield filtered
        # Don't forget to flush at the end
        remaining = filter.flush()
        if remaining:
            yield remaining
    """
    
    # All supported tag names
    SUPPORTED_TAGS = ['thinking', 'private', 'debug', 'citation', 'summary', 'source']
    
    def __init__(self):
        self._buffer = ""
        self._base_filter = ContentFilter()
    
    def _has_unclosed_tag(self) -> tuple[bool, str, int]:
        """
        Check if buffer has any unclosed tags.
        
        Returns:
            (has_unclosed, tag_name, position) - position of last unclosed tag
        """
        for tag in self.SUPPORTED_TAGS:
            open_pattern = re.compile(f'<{tag}(?:\\s[^>]*)?>',  re.IGNORECASE)
            close_pattern = re.compile(f'</{tag}>', re.IGNORECASE)
            
            open_count = len(open_pattern.findall(self._buffer))
            close_count = len(close_pattern.findall(self._buffer))
            
            if open_count > close_count:
                # Find position of last unclosed opening tag
                matches = list(open_pattern.finditer(self._buffer))
                if matches:
                    # Get the position after the last close tag
                    close_matches = list(close_pattern.finditer(self._buffer))
                    last_close_end = close_matches[-1].end() if close_matches else 0
                    
                    # Find first open tag after last close
                    for m in matches:
                        if m.start() >= last_close_end:
                            return True, tag, m.start()
                    
                    return True, tag, matches[-1].start()
        
        return False, "", -1
    
    def filter_chunk(self, chunk: str) -> str:
        """
        Filter a streaming chunk, buffering at potential tag boundaries.
        
        Args:
            chunk: A chunk of text from the streaming response
            
        Returns:
            Filtered text that is safe to output, or empty string if buffering
        """
        if not chunk:
            return ""
        
        self._buffer += chunk
        
        # Check for incomplete tag at end (e.g., "<think" or "<priv")
        incomplete_match = re.search(r'</?[a-z]*$', self._buffer, re.IGNORECASE)
        
        # Check for unclosed tags
        has_unclosed, tag_name, unclosed_pos = self._has_unclosed_tag()
        
        if has_unclosed and unclosed_pos >= 0:
            # We have an unclosed tag - output everything before it
            if unclosed_pos > 0:
                safe_content = self._buffer[:unclosed_pos]
                self._buffer = self._buffer[unclosed_pos:]
                return self._base_filter.filter_text(safe_content)
            return ""
        
        if incomplete_match:
            # Buffer ends with partial tag like "<think"
            safe_end = incomplete_match.start()
            if safe_end > 0:
                safe_content = self._buffer[:safe_end]
                self._buffer = self._buffer[safe_end:]
                return self._base_filter.filter_text(safe_content)
            return ""
        
        # No incomplete tags, process everything
        result = self._base_filter.filter_text(self._buffer)
        self._buffer = ""
        return result
    
    def flush(self) -> str:
        """
        Flush remaining buffer at end of stream.
        
        Handles unclosed tags gracefully by removing them.
        
        Returns:
            Any remaining filtered content
        """
        if not self._buffer:
            return ""
        
        # Remove any unclosed hidden tags
        result = self._buffer
        for tag in ['thinking', 'private', 'debug']:
            result = re.sub(f'<{tag}[^>]*>.*$', '', result, flags=re.DOTALL | re.IGNORECASE)
        
        result = self._base_filter.filter_text(result)
        self._buffer = ""
        return result
