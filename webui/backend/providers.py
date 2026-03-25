"""Static provider / model data mirrored from cli/utils.py."""

PROVIDERS = [
    {"value": "openai",     "label": "OpenAI",      "url": "https://api.openai.com/v1"},
    {"value": "google",     "label": "Google",      "url": "https://generativelanguage.googleapis.com/v1"},
    {"value": "anthropic",  "label": "Anthropic",   "url": "https://api.anthropic.com/"},
    {"value": "xai",        "label": "xAI",         "url": "https://api.x.ai/v1"},
    {"value": "openrouter", "label": "Openrouter",  "url": "https://openrouter.ai/api/v1"},
    {"value": "ollama",     "label": "Ollama",      "url": "http://localhost:11434/v1"},
]

DEPTH_OPTIONS = [
    {"value": 1, "label": "Shallow", "description": "Quick research, few debate rounds"},
    {"value": 3, "label": "Medium",  "description": "Moderate debate rounds and strategy discussion"},
    {"value": 5, "label": "Deep",    "description": "Comprehensive research, in-depth debate"},
]

ANALYSTS = [
    {"value": "market",       "label": "Market Analyst"},
    {"value": "social",       "label": "Social Media Analyst"},
    {"value": "news",         "label": "News Analyst"},
    {"value": "fundamentals", "label": "Fundamentals Analyst"},
]

SHALLOW_MODELS: dict[str, list[dict]] = {
    "openai": [
        {"value": "gpt-5-mini",  "label": "GPT-5 Mini – Balanced speed, cost, and capability"},
        {"value": "gpt-5-nano",  "label": "GPT-5 Nano – High-throughput, simple tasks"},
        {"value": "gpt-5.4",     "label": "GPT-5.4 – Latest frontier, 1M context"},
        {"value": "gpt-4.1",     "label": "GPT-4.1 – Smartest non-reasoning model"},
    ],
    "anthropic": [
        {"value": "claude-sonnet-4-6", "label": "Claude Sonnet 4.6 – Best speed/intelligence balance"},
        {"value": "claude-haiku-4-5",  "label": "Claude Haiku 4.5 – Fast, near-instant responses"},
        {"value": "claude-sonnet-4-5", "label": "Claude Sonnet 4.5 – Agents and coding"},
    ],
    "google": [
        {"value": "gemini-3-flash-preview",       "label": "Gemini 3 Flash – Next-gen fast"},
        {"value": "gemini-2.5-flash",             "label": "Gemini 2.5 Flash – Balanced, stable"},
        {"value": "gemini-3.1-flash-lite-preview", "label": "Gemini 3.1 Flash Lite – Most cost-efficient"},
        {"value": "gemini-2.5-flash-lite",        "label": "Gemini 2.5 Flash Lite – Fast, low-cost"},
    ],
    "xai": [
        {"value": "grok-4-1-fast-non-reasoning", "label": "Grok 4.1 Fast (Non-Reasoning) – Speed optimized, 2M ctx"},
        {"value": "grok-4-fast-non-reasoning",   "label": "Grok 4 Fast (Non-Reasoning) – Speed optimized"},
        {"value": "grok-4-1-fast-reasoning",     "label": "Grok 4.1 Fast (Reasoning) – High-performance, 2M ctx"},
    ],
    "openrouter": [
        {"value": "nvidia/nemotron-3-nano-30b-a3b:free", "label": "NVIDIA Nemotron 3 Nano 30B (free)"},
        {"value": "z-ai/glm-4.5-air:free",               "label": "Z.AI GLM 4.5 Air (free)"},
    ],
    "ollama": [
        {"value": "qwen3:latest",        "label": "Qwen3:latest (8B, local)"},
        {"value": "gpt-oss:latest",      "label": "GPT-OSS:latest (20B, local)"},
        {"value": "glm-4.7-flash:latest","label": "GLM-4.7-Flash:latest (30B, local)"},
    ],
}

DEEP_MODELS: dict[str, list[dict]] = {
    "openai": [
        {"value": "gpt-5.4",     "label": "GPT-5.4 – Latest frontier, 1M context"},
        {"value": "gpt-5.2",     "label": "GPT-5.2 – Strong reasoning, cost-effective"},
        {"value": "gpt-5-mini",  "label": "GPT-5 Mini – Balanced speed, cost, and capability"},
        {"value": "gpt-5.4-pro", "label": "GPT-5.4 Pro – Most capable ($30/$180 per 1M tokens)"},
    ],
    "anthropic": [
        {"value": "claude-opus-4-6",   "label": "Claude Opus 4.6 – Most intelligent, agents and coding"},
        {"value": "claude-opus-4-5",   "label": "Claude Opus 4.5 – Premium, max intelligence"},
        {"value": "claude-sonnet-4-6", "label": "Claude Sonnet 4.6 – Best speed/intelligence balance"},
        {"value": "claude-sonnet-4-5", "label": "Claude Sonnet 4.5 – Agents and coding"},
    ],
    "google": [
        {"value": "gemini-3.1-pro-preview", "label": "Gemini 3.1 Pro – Reasoning-first, complex workflows"},
        {"value": "gemini-3-flash-preview",  "label": "Gemini 3 Flash – Next-gen fast"},
        {"value": "gemini-2.5-pro",          "label": "Gemini 2.5 Pro – Stable pro model"},
        {"value": "gemini-2.5-flash",        "label": "Gemini 2.5 Flash – Balanced, stable"},
    ],
    "xai": [
        {"value": "grok-4-0709",             "label": "Grok 4 – Flagship model"},
        {"value": "grok-4-1-fast-reasoning", "label": "Grok 4.1 Fast (Reasoning) – High-performance, 2M ctx"},
        {"value": "grok-4-fast-reasoning",   "label": "Grok 4 Fast (Reasoning) – High-performance"},
        {"value": "grok-4-1-fast-non-reasoning", "label": "Grok 4.1 Fast (Non-Reasoning) – Speed optimized, 2M ctx"},
    ],
    "openrouter": [
        {"value": "z-ai/glm-4.5-air:free",               "label": "Z.AI GLM 4.5 Air (free)"},
        {"value": "nvidia/nemotron-3-nano-30b-a3b:free", "label": "NVIDIA Nemotron 3 Nano 30B (free)"},
    ],
    "ollama": [
        {"value": "glm-4.7-flash:latest", "label": "GLM-4.7-Flash:latest (30B, local)"},
        {"value": "gpt-oss:latest",       "label": "GPT-OSS:latest (20B, local)"},
        {"value": "qwen3:latest",         "label": "Qwen3:latest (8B, local)"},
    ],
}

THINKING_CONFIG: dict[str, list[dict]] = {
    "openai": [
        {"value": "medium", "label": "Medium – Default"},
        {"value": "high",   "label": "High – More thorough"},
        {"value": "low",    "label": "Low – Faster"},
    ],
    "anthropic": [
        {"value": "high",   "label": "High – Recommended"},
        {"value": "medium", "label": "Medium – Balanced"},
        {"value": "low",    "label": "Low – Faster, cheaper"},
    ],
    "google": [
        {"value": "high",    "label": "Enable Thinking – Recommended"},
        {"value": "minimal", "label": "Minimal Thinking – Faster"},
    ],
}
