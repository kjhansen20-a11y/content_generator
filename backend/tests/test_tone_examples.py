from app.services.knowledge import PREVIOUS_POST_SOURCE, tone_examples_context_block


def test_previous_post_source_constant():
    assert PREVIOUS_POST_SOURCE == "previous_post"
