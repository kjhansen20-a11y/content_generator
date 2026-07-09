from app.services.post_language import (
    build_post_language_instruction,
    detect_output_language,
    resolve_output_language,
    user_language_source,
)


def test_user_language_source_joins_non_empty_parts():
    assert user_language_source("Hej verden", None, "  bæredygtighed  ") == "Hej verden bæredygtighed"


def test_detect_output_language_danish_with_special_chars():
    text = (
        "Har andre også problemer med at være consistant på linkedin, "
        "nu har jeg løsningen!"
    )
    assert detect_output_language(text) == "Danish"


def test_detect_output_language_danish_without_special_chars():
    text = "Har andre også problemer med deres SoME så har vi løsningen her ved KJSolution"
    assert detect_output_language(text) == "Danish"


def test_resolve_output_language_hard_danish():
    assert resolve_output_language("da", "write in english please") == "Danish"


def test_resolve_output_language_auto():
    text = "Har andre også problemer med deres SoME så har vi løsningen her ved KJSolution"
    assert resolve_output_language("auto", text) == "Danish"


def test_build_post_language_instruction_for_danish():
    instruction = build_post_language_instruction("Danish", "Skriv om bæredygtighed")
    assert "CRITICAL OUTPUT LANGUAGE: Danish" in instruction
    assert "Never translate to English" in instruction
