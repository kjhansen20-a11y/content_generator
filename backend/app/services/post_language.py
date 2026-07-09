"""Resolve output language for post generation."""

from langdetect import LangDetectException, detect_langs

LANGUAGE_NAMES: dict[str, str] = {
    "da": "Danish",
    "en": "English",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "sv": "Swedish",
    "no": "Norwegian",
    "nb": "Norwegian",
    "nn": "Norwegian",
    "nl": "Dutch",
    "it": "Italian",
    "pt": "Portuguese",
    "pl": "Polish",
    "fi": "Finnish",
}

POST_LANGUAGE_CODES: dict[str, str] = {
    "auto": "Auto-detect",
    "da": "Danish",
    "en": "English",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "sv": "Swedish",
    "no": "Norwegian",
    "nl": "Dutch",
    "it": "Italian",
    "pt": "Portuguese",
    "pl": "Polish",
    "fi": "Finnish",
}

_DANISH_WORDS = frozenset(
    {
        "og",
        "at",
        "med",
        "har",
        "også",
        "deres",
        "vi",
        "så",
        "ikke",
        "det",
        "den",
        "for",
        "på",
        "til",
        "en",
        "er",
        "som",
        "af",
        "de",
        "nu",
        "her",
        "ved",
        "andre",
        "problemer",
        "løsningen",
        "løsning",
        "vores",
        "din",
        "dit",
        "mine",
        "mine",
        "hvor",
        "hvad",
        "når",
    }
)


def user_language_source(*parts: str | None) -> str:
    return " ".join(p.strip() for p in parts if p and p.strip())


def _danish_word_score(text: str) -> int:
    tokens = {token.strip(".,!?;:\"'()") for token in text.lower().split()}
    return sum(1 for word in _DANISH_WORDS if word in tokens)


def detect_output_language(language_source: str) -> str:
    cleaned = language_source.strip()
    if len(cleaned) < 4:
        return "English"
    if any(char in cleaned for char in "æøåÆØÅ"):
        return "Danish"
    if _danish_word_score(cleaned) >= 2:
        return "Danish"
    try:
        candidates = detect_langs(cleaned)
    except LangDetectException:
        return "English"
    if not candidates:
        return "English"
    best = candidates[0]
    if best.prob < 0.55:
        return "English"
    return LANGUAGE_NAMES.get(best.lang, best.lang.upper())


def resolve_output_language(explicit_code: str | None, language_source: str) -> str:
    code = (explicit_code or "auto").strip().lower()
    if code != "auto":
        if code not in POST_LANGUAGE_CODES or code == "auto":
            return detect_output_language(language_source)
        return POST_LANGUAGE_CODES[code]
    return detect_output_language(language_source)


def build_post_language_instruction(output_language: str, language_source: str = "") -> str:
    if output_language == "English" and not language_source:
        return "CRITICAL: Write hook, body, hashtags, and alt_text in English only."
    lines = [
        f"CRITICAL OUTPUT LANGUAGE: {output_language}",
        f"You MUST write hook, body, hashtags, and alt_text entirely in {output_language}.",
        "Never translate to English. English words in the user direction are topic context only.",
    ]
    if language_source:
        lines.append(f'User direction: """{language_source}"""')
    return "\n".join(lines)


def build_language_preservation_instruction(output_language: str) -> str:
    return (
        f"Preserve output language: {output_language}. "
        f"Keep hook, body, hashtags, and alt_text in {output_language}. "
        "Do not translate to English."
    )
