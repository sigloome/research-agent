
from typing import Optional, Dict, Any, Tuple, List
import re
from pydantic import BaseModel
from datetime import datetime

# Define models in core (shared by API and Agent adapters)
class FeedbackEvent(BaseModel):
    event_type: str # "click", "rating", "copy", "time_spent"
    target_id: str # doc_id or "summary"
    target_content: Optional[str] = None
    value: Optional[float] = 1.0 # 1.0 = positive, -1.0 = negative
    metadata: Dict[str, Any] = {}
    timestamp: datetime = datetime.now()

def analyze_event(event: FeedbackEvent) -> Tuple[str, bool, Optional[str]]:
    """
    Pure logic to analyze a feedback event.
    Returns:
        update_text (str): Text for the Markdown profile.
        should_boost_sql (bool): Whether SQL weights should be boosted.
        paper_id_to_boost (str): ID of paper to boost, if any.
    """
    update_text = ""
    should_boost_sql = False
    paper_id_to_boost = None
    
    if event.event_type == "rating":
        if event.value > 0:
            update_text = f"- User Liked Content: {event.target_content[:100]}...\n  - Reason: Explicit positive rating."
        else:
            update_text = f"- User Disliked Content: {event.target_content[:100]}...\n  - Reason: Explicit negative rating."

    elif event.event_type == "click":
        # Implicit signal
        update_text = f"- User Interested In: {event.target_content or event.target_id}\n  - Reason: Clicked citation."
        should_boost_sql = True
        paper_id_to_boost = event.target_id

    elif event.event_type == "copy":
        # Strong positive signal
        update_text = f"- User Found Useful (Copied): {event.target_content[:200]}..."

    return update_text, should_boost_sql, paper_id_to_boost


# ==========================================
# Query Analysis Logic (Migrated from analyzer.py)
# ==========================================

# Common AI/ML research topics for detection
AI_TOPICS = {
    # Core ML
    'machine learning': ['machine learning', 'ml', 'supervised learning', 'unsupervised'],
    'deep learning': ['deep learning', 'neural network', 'neural net', 'dnn'],
    'reinforcement learning': ['reinforcement learning', 'rl', 'reward', 'policy gradient', 'q-learning'],
    
    # NLP & Language
    'large language models': ['llm', 'large language model', 'language model', 'gpt', 'claude', 'gemini'],
    'natural language processing': ['nlp', 'natural language', 'text processing', 'sentiment'],
    'transformers': ['transformer', 'attention mechanism', 'self-attention', 'bert', 'encoder-decoder'],
    'prompt engineering': ['prompt', 'prompting', 'chain of thought', 'cot', 'few-shot', 'zero-shot'],
    
    # Vision
    'computer vision': ['computer vision', 'image recognition', 'object detection', 'cv'],
    'image generation': ['image generation', 'diffusion', 'stable diffusion', 'dall-e', 'midjourney'],
    'multimodal': ['multimodal', 'vision-language', 'vlm', 'image-text'],
    
    # AI Safety & Alignment
    'alignment': ['alignment', 'aligned', 'human values', 'value alignment'],
    'safety': ['ai safety', 'safe ai', 'robustness', 'adversarial'],
    'interpretability': ['interpretability', 'explainability', 'xai', 'explainable'],
    
    # Agents & Systems
    'agents': ['agent', 'agentic', 'autonomous', 'tool use', 'function calling'],
    'reasoning': ['reasoning', 'chain of thought', 'step by step', 'logic'],
    'retrieval': ['retrieval', 'rag', 'retrieval augmented', 'vector search', 'embedding'],
    
    # Training & Optimization
    'fine-tuning': ['fine-tuning', 'fine tune', 'finetuning', 'lora', 'adapter'],
    'training': ['training', 'pre-training', 'pretraining', 'optimization'],
    'efficiency': ['efficient', 'efficiency', 'compression', 'quantization', 'pruning'],
    
    # Applications
    'code generation': ['code generation', 'coding', 'programming', 'copilot'],
    'summarization': ['summarization', 'summary', 'summarize'],
    'question answering': ['question answering', 'qa', 'reading comprehension'],
}

# Query type patterns
QUERY_TYPES = {
    'find_papers': [
        r'find\s+papers?',
        r'search\s+(?:for\s+)?papers?',
        r'look\s+(?:for|up)\s+papers?',
        r'papers?\s+(?:on|about)',
        r'recent\s+(?:papers?|research)',
    ],
    'explain_concept': [
        r'explain\s+',
        r'what\s+is\s+',
        r'what\s+are\s+',
        r'how\s+does\s+',
        r'how\s+do\s+',
        r'tell\s+me\s+about',
        r'describe\s+',
    ],
    'summarize': [
        r'summarize',
        r'summary\s+of',
        r'key\s+(?:points|findings|ideas)',
        r'main\s+(?:contributions?|ideas?)',
    ],
    'compare': [
        r'compare',
        r'difference\s+between',
        r'vs\.?',
        r'versus',
        r'better\s+than',
    ],
    'recommend': [
        r'recommend',
        r'suggest',
        r'best\s+papers?',
        r'top\s+papers?',
        r'should\s+(?:I|we)\s+read',
    ],
    'paper_lookup': [
        r'paper\s+(?:with\s+)?id',
        r'look\s+up\s+.*\s+from\s+.*library',
        r'read_paper',
        r'details\s+(?:of|about|on)\s+',
    ],
}


def extract_topics(query: str) -> List[str]:
    """
    Extract AI/ML topics from a user query.
    Returns a list of detected topic names.
    """
    query_lower = query.lower()
    detected_topics = []
    
    for topic_name, keywords in AI_TOPICS.items():
        for keyword in keywords:
            if keyword.lower() in query_lower:
                if topic_name not in detected_topics:
                    detected_topics.append(topic_name)
                break
    
    return detected_topics


def detect_query_type(query: str) -> str:
    """
    Detect the type of query the user is making.
    """
    query_lower = query.lower()
    
    for query_type, patterns in QUERY_TYPES.items():
        for pattern in patterns:
            if re.search(pattern, query_lower):
                return query_type
    
    return 'general'


def extract_interests(query: str) -> List[str]:
    """
    Extract specific interests or entities from the query.
    These are more specific than general topics.
    """
    interests = []
    query_lower = query.lower()
    
    # Look for specific model names
    model_patterns = [
        r'\bgpt[-\s]?[34]?\b',
        r'\bclaude\b',
        r'\bgemini\b',
        r'\bllama\b',
        r'\bmistral\b',
        r'\bbert\b',
        r'\bt5\b',
        r'\bstable\s*diffusion\b',
    ]
    for pattern in model_patterns:
        match = re.search(pattern, query_lower)
        if match:
            interests.append(match.group().strip())
    
    # Look for specific techniques
    technique_patterns = [
        r'\bchain\s+of\s+thought\b',
        r'\bfew[-\s]?shot\b',
        r'\bzero[-\s]?shot\b',
        r'\bin[-\s]?context\s+learning\b',
        r'\blora\b',
        r'\bqlora\b',
        r'\brag\b',
        r'\brlhf\b',
        r'\bdpo\b',
    ]
    for pattern in technique_patterns:
        match = re.search(pattern, query_lower)
        if match:
            interests.append(match.group().strip())
    
    return interests


def analyze_query(query: str) -> Dict[str, Any]:
    """
    Full analysis of a user query.
    Returns topics, query type, and specific interests.
    """
    return {
        'topics': extract_topics(query),
        'query_type': detect_query_type(query),
        'interests': extract_interests(query),
    }
