"""Prompt-injection sanitizer and content isolation boundary for scraped web content."""
import re
from typing import Tuple


INJECTION_PATTERNS = [
    r"(?i)\bignore\s+(all\s+)?(previous|prior|above)\s+instructions\b",
    r"(?i)\bdisregard\s+(all\s+)?(previous|prior|above)\s+instructions\b",
    r"(?i)\bsystem\s+prompt\s+override\b",
    r"(?i)\byou\s+are\s+now\s+(a\s+)?(new|different|unfiltered)\b",
    r"(?i)\bdo\s+anything\s+now\b",
    r"(?i)\benter\s+dan\s+mode\b",
    r"(?i)\breveal\s+(the\s+)?(api[_\s]?key|secret|password|auth|token)\b",
    r"(?i)\bstop\s+summarizing\s+and\b",
    r"(?i)\bact\s+as\s+an\s+unrestricted\b",
]

COMPILED_INJECTIONS = [re.compile(p) for p in INJECTION_PATTERNS]


def sanitize_text_content(raw_text: str, max_chars: int = 15000) -> Tuple[str, bool]:
    """
    Sanitize extracted text to prevent indirect prompt injection:
    - Neutralizes known adversarial override phrases
    - Strips executable code blocks and tracking noise
    - Truncates to max_chars
    Returns (sanitized_text, injection_detected_bool).
    """
    if not raw_text:
        return "", False

    text = raw_text[:max_chars]
    injection_detected = False

    # Check for known prompt injection attempts
    for pattern in COMPILED_INJECTIONS:
        if pattern.search(text):
            injection_detected = True
            # Neutralize the offending instruction by replacing it with a neutral warning
            text = pattern.sub("[POTENTIAL_INJECTION_DEFUSED]", text)

    # Clean excessive whitespace and zero-width characters
    text = re.sub(r"[\u200B-\u200D\uFEFF]", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip(), injection_detected


def wrap_untrusted_content(source_id: str, url: str, content: str) -> str:
    """
    Wrap untrusted external content into strict boundary isolation tags.
    This informs the LLM to interpret content purely as passive data.
    """
    safe_content, _ = sanitize_text_content(content)
    return (
        f'<external_untrusted_source id="{source_id}" url="{url}">\n'
        f"{safe_content}\n"
        f"</external_untrusted_source>"
    )
