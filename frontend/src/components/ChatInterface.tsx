import { useEffect, useRef, useCallback, useState, forwardRef, useImperativeHandle, memo, useMemo } from 'react'
import { useChat, type UIMessage } from '@ai-sdk/react'
import { DefaultChatTransport } from 'ai'
import { useNavigate } from 'react-router-dom'
import { ArrowUp, FileText, Copy, Check, Loader2, Square, SquareCheck, StickyNote, Menu, Maximize2, Minimize2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math'
import remarkGfm from 'remark-gfm'
import rehypeKatex from 'rehype-katex'
import clsx from 'clsx'
import { ChatSidebar } from './ChatSidebar'

interface ChatInterfaceProps {
  onPaperAction?: () => void;
  onLibrarySearch?: (query: string) => void;
  isExpanded?: boolean;
  onToggleExpand?: () => void;
}



interface ResearchTask {
  id?: string;
  label: string;
  status: 'pending' | 'running' | 'completed';
}

const DEFAULT_SUGGESTIONS = [
  "Find papers on LLM alignment",
  "Summarize recent NeurIPS papers",
  "Explain attention mechanisms",
  "Search for chain of thought"
];

// ... (CopyButton, ResearchPlan, ThinkingProcess components - UNCHANGED) ...
const CopyButton = memo(function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button
      onClick={handleCopy}
      className="p-1 text-warmstone-400 hover:text-warmstone-600 transition-colors"
      title="Copy"
    >
      {copied ? <Check size={12} /> : <Copy size={12} />}
    </button>
  );
});

// Research Plan Component
const ResearchPlan = memo(function ResearchPlan({ tasks }: { tasks: ResearchTask[] }) {
  if (!tasks || tasks.length === 0) return null;

  const hasActive = tasks.some(t => t.status === 'running');
  const completedCount = tasks.filter(t => t.status === 'completed').length;
  const isDone = completedCount === tasks.length && tasks.length > 0;

  // Auto-collapse when done
  const [isExpanded, setIsExpanded] = useState(true);

  useEffect(() => {
    // Auto-expand when a task starts running
    if (hasActive) {
      setIsExpanded(true);
    }
    if (isDone) {
      // Delay collapse slightly for UX
      const timer = setTimeout(() => setIsExpanded(false), 2000);
      return () => clearTimeout(timer);
    }
  }, [isDone, hasActive, tasks.length]); // Re-expand if new tasks added or task starts

  return (
    <div className={clsx(
      "bg-white border border-warmstone-200 rounded-xl shadow-card overflow-hidden mb-4 transition-all duration-300",
      // Only float when active/expanded
      isExpanded ? "sticky top-0 z-20" : ""
    )}>
      <div
        className="flex items-center gap-2 px-4 py-3 bg-cream-50 border-b border-warmstone-100 cursor-pointer hover:bg-cream-100 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {hasActive ? (
          <Loader2 size={14} className="text-warmstone-600 animate-spin" />
        ) : isDone ? (
          <SquareCheck size={14} className="text-green-600" />
        ) : (
          <FileText size={14} className="text-warmstone-600" />
        )}
        <span className="text-sm font-semibold text-warmstone-800 flex-1">
          {isDone ? "Research Completed" : "Research Plan"}
        </span>
        <span className="text-xs text-warmstone-600 bg-warmstone-100 px-2 py-0.5 rounded-full">
          {completedCount}/{tasks.length}
        </span>
        {/* Chevron indicator could represent state, but clicking header works too */}
      </div>

      {/* Collapsible Content */}
      <div className={clsx(
        "px-4 bg-cream-50/50 transition-all duration-300 ease-in-out",
        isExpanded ? "max-h-[300px] overflow-y-auto py-2 opacity-100" : "max-h-0 overflow-hidden py-0 opacity-0"
      )}>
        <div className="space-y-1 py-1">
          {tasks.map((task, idx) => (
            <div key={idx} className={clsx(
              "flex items-center gap-3 px-2 py-1.5 rounded transition-all duration-300",
              task.status === 'running'
                ? "bg-gradient-to-r from-blue-50 to-white shadow-sm border border-blue-200 animate-pulse"
                : ""
            )}>
              {task.status === 'completed' ? (
                <SquareCheck size={14} className="text-green-600 shrink-0" />
              ) : task.status === 'running' ? (
                <Loader2 size={14} className="text-blue-600 animate-spin shrink-0" />
              ) : (
                <Square size={14} className="text-warmstone-300 shrink-0" />
              )}

              <span className={clsx(
                "text-sm font-mono truncate transition-all duration-300",
                task.status === 'completed' ? "text-warmstone-500 line-through decoration-warmstone-300" :
                  task.status === 'running' ? "text-blue-700 font-medium" : "text-warmstone-600"
              )}>
                {task.label}
              </span>

              {task.status === 'running' && (
                <span className="text-xs text-blue-500 font-medium animate-pulse ml-auto bg-blue-50 px-1.5 rounded">
                  IN PROGRESS
                </span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}, (prev, next) => {
  // Custom loose comparison to prevent jitter
  if (prev.tasks.length !== next.tasks.length) return false;
  // Check if any status changed
  return prev.tasks.every((t, i) => t.status === next.tasks[i].status && t.label === next.tasks[i].label && t.id === next.tasks[i].id);
});

/*
// Thinking Process Component (Collapsible)
const ThinkingProcess = memo(function ThinkingProcess({ steps }: { steps: string[] }) {
    const [isExpanded, setIsExpanded] = useState(false);

    if (!steps || steps.length === 0) return null;

    return (
        <div className="mb-2">
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="flex items-center gap-2 text-xs text-warmstone-500 hover:text-warmstone-700 hover:bg-warmstone-100 px-2 py-1.5 rounded-lg transition-colors w-full"
            >
                <div className={clsx("transition-transform", isExpanded ? "rotate-90" : "")}>
                    <ArrowUp size={12} className="rotate-90" />
                </div>
                <span className="font-medium">Thinking Process</span>
                <span className="bg-warmstone-100 px-1.5 rounded-full text-[10px]">{steps.length} steps</span>
            </button>

            {isExpanded && (
                <div className="mt-1 pl-4 space-y-1">
                    {steps.map((step, idx) => (
                        <div key={idx} className="flex items-center gap-2 text-xs text-warmstone-500 py-0.5 border-l border-warmstone-200 pl-2">
                            <Loader2 size={10} className="shrink-0" />
                            <span className="truncate">{step}</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}, (prev, next) => {
    // Only re-render if steps length changes or the last step changes
    if (prev.steps.length !== next.steps.length) return false;
    if (prev.steps.length > 0 && prev.steps[prev.steps.length - 1] !== next.steps[next.steps.length - 1]) return false;
    return true;
});
*/


// Helper to parse content with Stream Protocol - UNCHANGED
function parseContent(fullText: string) {
  // 1. Parse Research Plan

  const planValues: ResearchTask[] = [];
  const seenTasks = new Set<string>();

  const planInitRegex = /<<<PlanInit:\s*([\s\S]*?)>>>/g;

  for (const m of fullText.matchAll(planInitRegex)) {
    console.log("Found PlanInit marker");
    try {
      const parsed = JSON.parse(m[1].trim());
      // Handle both legacy [strings] and new [{id, description, status}] format
      parsed.forEach((t: any) => {
        const label = typeof t === 'string' ? t : t.description;
        const id = typeof t === 'string' ? undefined : t.id;
        // De-duplicate by ID if available, else by label
        const key = id || label;

        if (!seenTasks.has(key)) {
          planValues.push({
            id,
            label,
            status: typeof t === 'string' ? 'pending' : (t.status || 'pending')
          });
          seenTasks.add(key);
        }
      });
    } catch (e) {
      console.error("Failed to parse PlanInit", e);
    }
  }

  // 1b. Parse Plan Updates (Additions)
  const planUpdateRegex = /<<<PlanUpdate:\s*([\s\S]*?)>>>/g;
  for (const m of fullText.matchAll(planUpdateRegex)) {
    try {
      const parsed = JSON.parse(m[1].trim());
      parsed.forEach((t: any) => {
        const label = typeof t === 'string' ? t : t.description;
        const id = typeof t === 'string' ? undefined : t.id;
        const key = id || label;

        if (!seenTasks.has(key)) {
          planValues.push({
            id,
            label,
            status: typeof t === 'string' ? 'pending' : (t.status || 'pending')
          });
          seenTasks.add(key);
        }
      });
    } catch (e) {
      console.error("Failed to parse PlanUpdate", e);
    }
  }

  // Step Start/End logic...
  const stepStartRegex = /<<<StepStart:\s*([\s\S]*?)>>>/g;
  const runningIds = new Set<string>();
  const runningLabels = new Set<string>(); // Legacy fallback

  for (const m of fullText.matchAll(stepStartRegex)) {
    try {
      // Try parsing as JSON object first (New Protocol)
      if (m[1].trim().startsWith('{')) {
        const data = JSON.parse(m[1].trim());
        console.log("Parsed StepStart JSON:", data);
        if (data.id) runningIds.add(data.id);
        if (data.description) runningLabels.add(data.description);
      } else {
        console.log("Parsed StepStart String:", m[1].trim());
        // Fallback to raw string
        runningLabels.add(m[1].trim());
      }
    } catch (e) {
      console.error("StepStart parsing error:", e);
      runningLabels.add(m[1].trim());
    }
  }

  const stepEndRegex = /<<<StepEnd:\s*([\s\S]*?)>>>/g;
  const completedIds = new Set<string>();
  const completedLabels = new Set<string>();

  for (const m of fullText.matchAll(stepEndRegex)) {
    try {
      if (m[1].trim().startsWith('{')) {
        const data = JSON.parse(m[1].trim());
        console.log("Parsed StepEnd JSON:", data);
        if (data.id) completedIds.add(data.id);
      } else {
        console.log("Parsed StepEnd String:", m[1].trim());
        completedLabels.add(m[1].trim());
      }
    } catch {
      completedLabels.add(m[1].trim());
    }
  }

  // Update statuses based on IDs first, then labels
  planValues.forEach(t => {
    if (t.id) {
      if (completedIds.has(t.id)) t.status = 'completed';
      else if (runningIds.has(t.id)) t.status = 'running';
    } else {
      if (completedLabels.has(t.label)) t.status = 'completed';
      else if (runningLabels.has(t.label)) t.status = 'running';
    }
  });

  // 2. Parse Tool Logs (Extraction)
  // Extract "*Running tool: ...*" to separate list
  // Use robust regex that doesn't depend on surrounding newlines
  const toolRegex = /\*Running tool: ([\s\S]*?)\*/g;
  const toolSteps: string[] = [];
  const toolMatches = [...fullText.matchAll(toolRegex)];
  for (const m of toolMatches) {
    toolSteps.push(m[1].trim());
  }

  // 3. Clean Content
  // NOTE: Primary filtering now happens in backend (content_filter.py)
  // The backend handles XML tags (<thinking>, <private>, <debug>, <citation>, <summary>, <source>)
  // and file paths before streaming. These frontend filters are kept as fallbacks.
  let cleanContent = fullText
    .replace(planInitRegex, "")
    .replace(planUpdateRegex, "")
    .replace(stepStartRegex, "")
    .replace(stepEndRegex, "")
    .replace(toolRegex, "") // Remove tools from main text
    .replace(/\(no content\)/g, "")
    // Fallback: Remove hidden tags that slip through
    .replace(/<thinking>[\s\S]*?<\/thinking>/gi, "")
    .replace(/<private>[\s\S]*?<\/private>/gi, "")
    .replace(/<debug>[\s\S]*?<\/debug>/gi, "")
    // Fallback: Transform display tags (in case backend misses them)
    .replace(/<citation\s+url=["']([^"']+)["']\s*>([\s\S]*?)<\/citation>/gi, '[$2]($1)')
    .replace(/<citation>([\s\S]*?)<\/citation>/gi, '*$1*')
    .replace(/<summary>([\s\S]*?)<\/summary>/gi, '\n> $1\n')
    .replace(/<source\s+url=["']([^"']+)["']\s*>([\s\S]*?)<\/source>/gi, '\n📄 **Source**: [$2]($1)\n')
    .replace(/<source>([\s\S]*?)<\/source>/gi, '\n📄 **Source**: $1\n')
    // Fallback: Remove file paths
    .replace(/^\/(?:Users|home|var|tmp)\/[^\n]+$/gm, "")
    .replace(/`\/(?:Users|home|var|tmp)\/[^`]+`/g, "")
    // Clean up whitespace
    .replace(/\n{3,}/g, "\n\n")
    .trim();

  return { cleanContent, researchTasks: planValues, toolSteps };
}

// Markdown components definition moved outside to prevent re-creation
// We need to pass navigate and simple handlers, but components prop in ReactMarkdown
// accepts a dictionary. For specialized handlers that depend on scope (like navigate),
// we can keep them inside but memoized. However, moving static parts out is better.
// Markdown components definition moved outside to prevent re-creation
// We need to pass navigate and simple handlers, but components prop in ReactMarkdown
// accepts a dictionary. For specialized handlers that depend on scope (like navigate),
// we can keep them inside but memoized. However, moving static parts out is better.
const createMarkdownComponents = (navigate: any, onLibrarySearch: any) => ({
  h1: ({ children }: any) => <h1 className="text-xl font-bold text-stone-900 mb-3">{children}</h1>,
  h2: ({ children }: any) => <h2 className="text-lg font-semibold text-stone-900 mt-4 mb-2">{children}</h2>,
  h3: ({ children }: any) => <h3 className="text-base font-semibold text-stone-800 mt-3 mb-2">{children}</h3>,
  p: ({ children }: any) => {
    const text = Array.isArray(children) ? children.join('') : String(children);
    if (text.startsWith('Searching for:') || text.includes('Searching for:')) {
      return (
        <div className="flex items-center gap-2 text-xs text-stone-500 my-1 bg-stone-50 px-2 py-1 rounded w-fit border border-stone-100">
          <Loader2 size={10} className="stroke-stone-400 shrink-0" />
          {children}
        </div>
      )
    }
    return <p className="text-stone-700 leading-relaxed mb-3">{children}</p>
  },
  li: ({ children }: any) => <li className="text-stone-700 mb-1">{children}</li>,
  strong: ({ children }: any) => <strong className="font-semibold text-stone-900">{children}</strong>,
  a: ({ href, children }: any) => {
    const isLibraryLink = href?.startsWith('/library/');
    const isPaperLink = href?.startsWith('/paper/');

    // Check for ArXiv links to intercept
    let arxivId = null;
    if (href && (href.includes('arxiv.org/abs/') || href.includes('arxiv.org/pdf/'))) {
      const match = href.match(/arxiv\.org\/(?:abs|pdf)\/([^/?#]+)/);
      if (match) {
        arxivId = match[1];
      }
    }

    const handleClick = (e: React.MouseEvent) => {
      if (isLibraryLink && onLibrarySearch) {
        e.preventDefault();
        // Extract title from children if possible, or use ID
        const text = String(children);
        onLibrarySearch(text);
      } else if (isPaperLink && href) {
        e.preventDefault();
        navigate(href);
      } else if (arxivId) {
        e.preventDefault();
        navigate(`/paper/${arxivId}`);
      }
    };

    return (
      <a
        href={href}
        onClick={handleClick}
        className="text-blue-600 underline hover:text-blue-800 cursor-pointer"
        target={isLibraryLink || isPaperLink || arxivId ? undefined : "_blank"}
        rel={isLibraryLink || isPaperLink || arxivId ? undefined : "noreferrer"}
      >
        {children}
      </a>
    );
  },
  code({ node, inline, className, children, ...props }: any) {
    const isBlock = !inline || className?.includes('language-');
    if (isBlock) {
      return (
        <div className="relative group my-4">
          <pre className="bg-stone-100/50 text-stone-800 p-4 rounded-lg overflow-x-auto">
            <code className="text-sm font-mono" {...props}>{children}</code>
          </pre>
        </div>
      );
    }
    return <code className="bg-stone-100 px-1.5 py-0.5 rounded text-xs font-mono text-stone-800" {...props}>{children}</code>
  },
  table: ({ children }: any) => <div className="overflow-x-auto my-4 border border-stone-200 rounded-lg"><table className="min-w-full divide-y divide-stone-200 text-sm text-stone-700">{children}</table></div>,
});




const UserMessage = memo(function UserMessage({
  content,
  onEdit,
}: {
  content: string;
  onEdit?: () => void;
}) {
  return (
    <div className="group">
      <div className="bg-cream-200 rounded-xl px-4 py-3 text-warmstone-800 text-sm shadow-sm">{content}</div>
      {onEdit && (
        <div className="mt-1 flex justify-end">
          <button
            onClick={onEdit}
            className="text-xs text-warmstone-500 hover:text-warmstone-700 underline"
            title="Edit and resend this message"
          >
            Edit
          </button>
        </div>
      )}
    </div>
  );
});

interface PaperContext {
  paperId: string;
  paperTitle: string;
  suggestions: string[];
}

interface ToolTimelineItem {
  id: string;
  name: string;
  state: string;
  description: string;
  isRunning: boolean;
  isError: boolean;
}

function extractMessageText(message: UIMessage): string {
  return message.parts
    .filter((part): part is { type: 'text'; text: string } => part.type === 'text')
    .map(part => part.text)
    .join('');
}

function stringifyPartValue(value: unknown): string {
  if (typeof value === 'string') {
    return value;
  }
  if (value == null) {
    return '';
  }
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

function extractToolTimeline(message: UIMessage): ToolTimelineItem[] {
  const runningStates = new Set(['input-streaming', 'input-available', 'approval-requested', 'approval-responded']);
  const errorStates = new Set(['output-error', 'output-denied']);

  const items: ToolTimelineItem[] = [];
  for (let i = 0; i < message.parts.length; i += 1) {
    const part = message.parts[i];
    if (part.type !== 'dynamic-tool' && !part.type.startsWith('tool-')) {
      continue;
    }

    const asRecord = part as Record<string, unknown>;
    const toolName = part.type === 'dynamic-tool' ? String(asRecord.toolName ?? 'tool') : part.type.slice(5);
    const state = typeof asRecord.state === 'string' ? asRecord.state : 'unknown';
    const title = typeof asRecord.title === 'string' ? asRecord.title : '';
    const outputText = stringifyPartValue(asRecord.output);
    const inputText = stringifyPartValue(asRecord.input);
    const description = title || outputText || inputText || 'No detail';

    items.push({
      id: String(asRecord.toolCallId ?? `${toolName}-${i}`),
      name: toolName,
      state,
      description: description.length > 140 ? `${description.slice(0, 140)}...` : description,
      isRunning: runningStates.has(state),
      isError: errorStates.has(state),
    });
  }
  return items;
}

function getLastUserText(messages: UIMessage[]): string {
  for (let i = messages.length - 1; i >= 0; i -= 1) {
    if (messages[i].role === 'user') {
      return extractMessageText(messages[i]);
    }
  }
  return '';
}

const ToolTimeline = memo(function ToolTimeline({ items }: { items: ToolTimelineItem[] }) {
  if (items.length === 0) return null;

  return (
    <div className="mb-3 rounded-lg border border-blue-100 bg-blue-50/60 px-3 py-2">
      <p className="mb-2 text-xs font-semibold text-blue-800">Tool Progress</p>
      <div className="space-y-1.5">
        {items.map(item => (
          <div key={item.id} className="flex items-start gap-2 rounded-md bg-white/70 px-2 py-1.5">
            {item.isRunning ? (
              <Loader2 size={13} className="mt-0.5 shrink-0 animate-spin text-blue-600" />
            ) : item.isError ? (
              <Square size={13} className="mt-0.5 shrink-0 text-red-500" />
            ) : (
              <SquareCheck size={13} className="mt-0.5 shrink-0 text-green-600" />
            )}
            <div className="min-w-0">
              <p className="truncate text-xs font-medium text-blue-900">{item.name}</p>
              <p className="truncate text-xs text-blue-700">{item.description}</p>
              <p className="text-[10px] uppercase tracking-wide text-blue-500">{item.state}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
});

// Export handle type for parent components to use
export interface ChatInterfaceHandle {
  sendMessage: (content: string) => Promise<void>;
  prepareQuestionAboutPaper: (paperId: string, paperTitle: string) => void;
}


const AssistantMessage = memo(function AssistantMessage({
  content,
  toolTimeline,
  onRetry,
  onLibrarySearch,
}: {
  content: string;
  toolTimeline: ToolTimelineItem[];
  onRetry?: () => void;
  onLibrarySearch?: (query: string) => void;
}) {
  // Memoize the parsing logic effectively
  const { cleanContent, researchTasks } = useMemo(() => parseContent(content), [content]);

  const navigate = useNavigate();
  const [isSaving, setIsSaving] = useState(false);

  // Stabilize markdown components
  const markdownComponents = useMemo(() =>
    createMarkdownComponents(navigate, onLibrarySearch),
    [navigate, onLibrarySearch]
  );

  const handleSaveNote = useCallback(async () => {
    setIsSaving(true);
    try {
      await fetch('/api/notes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: cleanContent })
      });
    } catch (e) {
      console.error("Failed to save note", e);
    } finally {
      setIsSaving(false);
    }
  }, [cleanContent]);


  // Memoize split content
  const { chatter, reportContent } = useMemo(() => {
    // Split Report and Chatter (Intro/Outro)
    const reportIndex = cleanContent.indexOf('# Research Report');
    let chatter = cleanContent;
    let reportContent = "";

    if (reportIndex !== -1) {
      const pre = cleanContent.substring(0, reportIndex).trim();
      const post = cleanContent.substring(reportIndex).trim();
      reportContent = post;
      chatter = pre;
    }
    return { chatter, reportContent };
  }, [cleanContent]);


  // Extract title
  // const titleMatch = cleanContent.match(/^#\s+(.+)$/m) || cleanContent.match(/^(.{1,50})/);
  // const title = titleMatch ? titleMatch[1].replace(/[#*]/g, '').trim() : 'Response';
  const hasContent = cleanContent.trim().length > 0;

  const renderMarkdown = (text: string) => (
    <div className="prose prose-stone prose-sm max-w-none">
      <ReactMarkdown
        remarkPlugins={[remarkMath, remarkGfm]}
        rehypePlugins={[rehypeKatex]}
        components={markdownComponents}
      >
        {text}
      </ReactMarkdown>
    </div>
  );

  return (
    <div className="flex flex-col gap-2">
      <ToolTimeline items={toolTimeline} />
      {researchTasks.length > 0 && <ResearchPlan tasks={researchTasks} />}

      {hasContent && (
        <div className="bg-white rounded-xl shadow-sm overflow-hidden group">
          <div className="px-4 py-4 text-stone-800">
            {chatter && reportContent ? (
              <>
                {chatter.trim() && <div className="mb-4 border-b border-stone-100 pb-2">{renderMarkdown(chatter)}</div>}
                <div>{renderMarkdown(reportContent)}</div>
              </>
            ) : (
              renderMarkdown(cleanContent)
            )}
          </div>
          {/* Action Bar */}
          <div className="px-4 py-2 bg-stone-50 border-t border-warmstone-100 flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <div className="flex items-center gap-2">
              <CopyButton text={cleanContent} />
              {onRetry && (
                <button
                  onClick={onRetry}
                  className="p-1 text-warmstone-400 hover:text-warmstone-600 transition-colors text-xs"
                  title="Regenerate this response"
                >
                  Retry
                </button>
              )}
              <button
                onClick={handleSaveNote}
                disabled={isSaving}
                className="p-1 text-warmstone-400 hover:text-warmstone-600 transition-colors flex items-center gap-1 text-xs"
                title="Save to Notes"
              >
                <StickyNote size={12} />
                {isSaving ? "Saving..." : "Save Note"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
});

const ChatInterface = forwardRef<ChatInterfaceHandle, ChatInterfaceProps>(({ onPaperAction, onLibrarySearch, isExpanded, onToggleExpand }, ref) => {
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [inputValue, setInputValue] = useState('');
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const [isFetchingHistory, setIsFetchingHistory] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>(DEFAULT_SUGGESTIONS);
  const [paperContext, setPaperContext] = useState<PaperContext | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [uiError, setUiError] = useState<string | null>(null);

  const {
    messages,
    setMessages,
    sendMessage: sendChatMessage,
    regenerate,
    stop,
    status,
    error,
    clearError,
  } = useChat({
    experimental_throttle: 40,
    transport: new DefaultChatTransport({
      api: '/api/chat',
      prepareSendMessagesRequest: ({ messages: currentMessages, body }) => {
        const requestBody = (body ?? {}) as Record<string, unknown>;
        const apiMessage =
          typeof requestBody.api_message === 'string'
            ? requestBody.api_message
            : getLastUserText(currentMessages);
        const sessionId =
          typeof requestBody.session_id === 'string'
            ? requestBody.session_id
            : 'default';

        return {
          body: {
            message: apiMessage,
            session_id: sessionId,
          },
        };
      },
    }),
    onError: chatError => {
      console.error("Chat error:", chatError);
    },
  });

  const isStreaming = status === 'submitted' || status === 'streaming';
  const isLoading = isStreaming || isFetchingHistory;

  // Generate suggestions for a specific paper
  const generatePaperSuggestions = useCallback((paperTitle: string): string[] => {
    const shortTitle = paperTitle.length > 40 ? paperTitle.substring(0, 40) + '...' : paperTitle;
    return [
      `What are the main contributions of "${shortTitle}"?`,
      `Summarize the key findings and methodology`,
      `What are the limitations and future work?`,
      `How does this paper relate to other recent research?`,
      `Explain the technical approach in simple terms`,
    ];
  }, []);

  // Prepare a question about a specific paper (called from parent)
  const prepareQuestionAboutPaper = useCallback((paperId: string, paperTitle: string) => {
    const suggestions = generatePaperSuggestions(paperTitle);
    setPaperContext({
      paperId,
      paperTitle,
      suggestions
    });
    // Set a template in the input that user can edit
    setInputValue(`Tell me about "${paperTitle}"`);
  }, [generatePaperSuggestions]);

  // Clear paper context
  const clearPaperContext = useCallback(() => {
    setPaperContext(null);
  }, []);

  // Fetch personalized suggestions on mount and after each message
  const fetchSuggestions = useCallback(async () => {
    try {
      const response = await fetch('/api/preferences');
      if (response.ok) {
        const data = await response.json();
        if (data.suggestions && data.suggestions.length > 0) {
          setSuggestions(data.suggestions);
        }
      }
    } catch (error) {
      console.error('Failed to fetch suggestions:', error);
    }
  }, []);

  useEffect(() => {
    fetchSuggestions();
  }, [fetchSuggestions]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    if (uiError) setUiError(null);
    setInputValue(e.target.value);
  };

  // Chat Management actions
  const handleNewChat = () => {
    setCurrentChatId(null);
    setMessages([]);
    setEditingMessageId(null);
    clearError();
    setUiError(null);
    if (window.innerWidth < 768) setIsSidebarOpen(false);
  };

  const handleSelectChat = async (chatId: string) => {
    setCurrentChatId(chatId);
    setMessages([]); // clear current
    setEditingMessageId(null);
    clearError();
    setUiError(null);
    setIsFetchingHistory(true);
    if (window.innerWidth < 768) setIsSidebarOpen(false);
    try {
      const res = await fetch(`/api/chats/${chatId}`);
      if (res.ok) {
        const data = await res.json();
        const uiMessages: UIMessage[] = data.map((m: any) => ({
          id: String(m.id),
          role: m.role === 'assistant' ? 'assistant' : 'user',
          parts: [{ type: 'text', text: String(m.content ?? ''), state: 'done' }],
        }));
        setMessages(uiMessages);
      } else {
        setUiError("Could not load chat history. Please retry.");
      }
    } catch (e) {
      console.error("Failed to load chat history", e);
      setUiError("Could not load chat history. Please check your connection and retry.");
    } finally {
      setIsFetchingHistory(false);
    }
  };


  const sendMessage = useCallback(async (content: string, options?: { messageId?: string }) => {
    if (!content.trim() || isStreaming) return false;

    let activeChatId = currentChatId;

    // If no active chat, create one now
    if (!activeChatId) {
      try {
        // Generate a title from the first details
        const title = content.length > 30 ? content.substring(0, 30) + '...' : content;
        const res = await fetch('/api/chats', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title })
        });
        if (res.ok) {
          const data = await res.json();
          activeChatId = data.id;
          setCurrentChatId(data.id);
        } else {
          throw new Error("Failed to create chat");
        }
      } catch (e) {
        console.error("Error creating chat", e);
        setUiError("Could not create a new chat. Please check your connection and retry.");
        return false;
      }
    }

    // If we have paper context, enhance the message with paper ID for the agent
    const displayContent = content.trim();
    let finalContent = displayContent;
    if (paperContext) {
      // Prepend context for the agent to use local DB
      finalContent = `[Context: Paper ID "${paperContext.paperId}" - "${paperContext.paperTitle}"]\n\n${finalContent}\n\nPlease use the read_paper tool to get details from the local database first.`;
      // Clear paper context after sending
      clearPaperContext();
    }

    try {
      clearError();
      setUiError(null);
      await sendChatMessage(
        options?.messageId
          ? { text: displayContent, messageId: options.messageId }
          : { text: displayContent },
        {
          body: {
            session_id: activeChatId,
            api_message: finalContent,
          },
        },
      );
      onPaperAction?.();
      fetchSuggestions();
      return true;
    } catch (e) {
      console.error("Chat request failed:", e);
      setUiError("Could not send message. Please retry.");
      return false;
    }
  }, [isStreaming, currentChatId, paperContext, clearPaperContext, clearError, sendChatMessage, onPaperAction, fetchSuggestions, setUiError]);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputValue.trim() || isStreaming) return;

    const text = inputValue.trim();
    const messageId = editingMessageId ?? undefined;
    const sent = await sendMessage(text, messageId ? { messageId } : undefined);
    if (sent) {
      setInputValue('');
      setEditingMessageId(null);
    }
  };

  const append = async (msg: { role: string; content: string }) => {
    await sendMessage(msg.content);
  };

  const handleEditMessage = useCallback((messageId: string, text: string) => {
    setEditingMessageId(messageId);
    setInputValue(text);
    requestAnimationFrame(() => {
      textareaRef.current?.focus();
    });
  }, []);

  const handleRetry = useCallback(async (messageId?: string) => {
    if (!currentChatId) return;
    clearError();
    setUiError(null);
    try {
      await regenerate({
        messageId,
        body: { session_id: currentChatId },
      });
      fetchSuggestions();
    } catch (retryError) {
      console.error("Retry failed:", retryError);
      setUiError("Could not retry the response. Please try again.");
    }
  }, [currentChatId, clearError, regenerate, fetchSuggestions]);

  // Expose methods to parent via ref
  useImperativeHandle(ref, () => ({
    sendMessage: async (content: string) => {
      await sendMessage(content);
    },
    prepareQuestionAboutPaper
  }), [sendMessage, prepareQuestionAboutPaper]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading, scrollToBottom]);

  // Resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px';
    }
  }, [inputValue]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(e); }
  };

  return (
    <div className="flex h-full bg-cream overflow-hidden relative">
      <ChatSidebar
        currentChatId={currentChatId || ""}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
        isOpen={isSidebarOpen}
        setIsOpen={setIsSidebarOpen}
      />

      <div className="flex-1 flex flex-col h-full min-w-0">
        {/* Header for Mobile/Collapsed Sidebar */}
        <div className="h-14 border-b border-warmstone-200 bg-cream flex items-center justify-between px-4 shrink-0 transition-all">
          <div className="flex items-center">
            {!isSidebarOpen && (
              <button
                onClick={() => setIsSidebarOpen(true)}
                className="p-2 -ml-2 text-warmstone-500 hover:bg-warmstone-100 rounded-lg transition-colors mr-2"
                title="Open History"
              >
                <Menu size={20} />
              </button>
            )}
            <span className="font-medium text-warmstone-700">
              {currentChatId ? "Chat Session" : "Research Assistant"}
            </span>
          </div>
          {onToggleExpand && (
            <button
              onClick={onToggleExpand}
              className="p-1.5 text-warmstone-400 hover:text-warmstone-800 hover:bg-warmstone-100 rounded-lg transition-colors"
              title={isExpanded ? "Collapse chat" : "Expand chat"}
            >
              {isExpanded ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
            </button>
          )}
        </div>

        <div className="flex-1 overflow-y-auto relative">
          {/* Mobile Header for Sidebar Trigger - optional if handled by sidebar absolute button */}
          {/* Sidebar has a fixed button for mobile. */}

          {messages.length === 0 && !isFetchingHistory ? (
            <div className="flex flex-col items-center justify-center h-full px-4 py-12">
              {/* Suggestions */}
              <div className="text-center max-w-md">
                <h1 className="text-2xl font-semibold text-warmstone-800 mb-2">Research Assistant</h1>
                <p className="text-warmstone-500 text-sm mb-8">Find papers, get summaries, and explore research topics.</p>
                <div className="space-y-2">
                  {suggestions.map((text, index) => (
                    <button
                      key={`${text}-${index}`}
                      onClick={() => {
                        void sendMessage(text);
                      }}
                      className="w-full text-left px-4 py-3 bg-white border border-warmstone-200 rounded-xl text-sm text-warmstone-700 hover:border-warmstone-300 hover:shadow-card transition-all"
                    >
                      {text}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div
              className="max-w-3xl mx-auto px-4 py-6 space-y-4"
              role="log"
              aria-live="polite"
              aria-relevant="additions text"
              aria-label="Live chat transcript"
            >
              {isFetchingHistory && messages.length === 0 && (
                <div className="flex items-center gap-2 text-warmstone-400 p-4">
                  <Loader2 size={16} className="animate-spin" />
                  <span className="text-sm">Loading chat history...</span>
                </div>
              )}
              {messages.map((m) => (
                <div key={m.id}>
                  {m.role === 'user' ? (
                    <UserMessage
                      content={extractMessageText(m)}
                      onEdit={() => handleEditMessage(m.id, extractMessageText(m))}
                    />
                  ) : (
                    <AssistantMessage
                      content={extractMessageText(m)}
                      toolTimeline={extractToolTimeline(m)}
                      onRetry={() => handleRetry(m.id)}
                      onLibrarySearch={onLibrarySearch}
                    />
                  )}
                </div>
              ))}
              {isLoading && messages[messages.length - 1]?.role === 'user' && (
                <div className="flex items-center gap-2 text-warmstone-400 p-4">
                  <Loader2 size={16} className="animate-spin" />
                  <span className="text-sm">{isFetchingHistory ? "Loading history..." : "Streaming..."}</span>
                </div>
              )}
              <div ref={messagesEndRef} className="h-4" />
            </div>
          )}
        </div>

        {/* Input */}
        <div className="border-t border-warmstone-200 bg-cream-50 p-4 z-10 relative">
          <div className="max-w-3xl mx-auto">
            {/* Paper Context Banner & Suggestions */}
            {paperContext && (
              <div className="mb-3 bg-blue-50 border border-blue-200 rounded-xl p-3">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <FileText size={14} className="text-blue-600" />
                    <span className="text-sm font-medium text-blue-800">
                      Asking about: {paperContext.paperTitle.length > 50
                        ? paperContext.paperTitle.substring(0, 50) + '...'
                        : paperContext.paperTitle}
                    </span>
                  </div>
                  <button
                    onClick={clearPaperContext}
                    className="text-xs text-blue-600 hover:text-blue-800 px-2 py-1 hover:bg-blue-100 rounded"
                  >
                    Clear
                  </button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {paperContext.suggestions.map((suggestion, idx) => (
                    <button
                      key={idx}
                      onClick={() => setInputValue(suggestion)}
                      className="text-xs px-3 py-1.5 bg-white border border-blue-200 text-blue-700 rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-all"
                    >
                      {suggestion.length > 45 ? suggestion.substring(0, 45) + '...' : suggestion}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {editingMessageId && (
              <div className="mb-2 flex items-center justify-between rounded-lg border border-amber-200 bg-amber-50 px-3 py-2">
                <span className="text-xs text-amber-800">Editing previous message. Sending will replace later turns.</span>
                <button
                  type="button"
                  onClick={() => {
                    setEditingMessageId(null);
                    setInputValue('');
                  }}
                  className="text-xs text-amber-700 underline"
                >
                  Cancel edit
                </button>
              </div>
            )}

            {(status === 'error' && error) || uiError ? (
              <div className="mb-2 flex flex-wrap items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2" role="status" aria-live="polite">
                <span className="text-xs text-red-700">
                  {status === 'error' && error ? `Stream error: ${error.message}` : uiError}
                </span>
                <button
                  type="button"
                  className="text-xs text-red-700 underline"
                  onClick={() => {
                    if (status === 'error' && error) {
                      void handleRetry();
                      return;
                    }
                    void handleSubmit();
                  }}
                >
                  Retry
                </button>
                <button
                  type="button"
                  className="text-xs text-red-700 underline"
                  onClick={() => {
                    clearError();
                    setUiError(null);
                  }}
                >
                  Dismiss
                </button>
              </div>
            ) : null}

            <form onSubmit={handleSubmit}>
              <div className="flex items-end gap-2 bg-white border border-warmstone-200 rounded-xl shadow-card focus-within:border-warmstone-300 transition-all">
                <textarea
                  ref={textareaRef}
                  className="flex-1 bg-transparent border-none px-4 py-3 text-sm text-warmstone-800 focus:outline-none resize-none min-h-[48px] max-h-[200px]"
                  value={inputValue}
                  onChange={handleInputChange}
                  onKeyDown={handleKeyDown}
                  placeholder={paperContext ? "Edit your question or pick a suggestion above..." : "Ask about research papers..."}
                  rows={1}
                />
                <div className="p-2">
                  <div className="flex items-center gap-2">
                    {isStreaming && (
                      <button
                        type="button"
                        aria-label="Stop streaming response"
                        onClick={stop}
                        className="p-2 bg-red-600 hover:bg-red-500 text-white rounded-lg transition-all"
                        title="Stop"
                      >
                        <Square size={14} />
                      </button>
                    )}
                    <button
                      type="submit"
                      aria-label={editingMessageId ? "Resend edited message" : "Send message"}
                      disabled={isStreaming || !inputValue.trim()}
                      className="p-2 bg-warmstone-800 hover:bg-warmstone-700 disabled:bg-warmstone-300 text-white rounded-lg transition-all"
                    >
                      <ArrowUp size={16} />
                    </button>
                  </div>
                </div>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
});

ChatInterface.displayName = 'ChatInterface';

export default ChatInterface;
