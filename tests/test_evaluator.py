import pytest
from services.evaluator import AnswerEvaluator

SAMPLE_QUESTION = {
    "id": "PY-BEG-01",
    "subject": "Python Programming",
    "topic": "Data Structures",
    "difficulty": "Beginner",
    "question": "What is the difference between a list and a tuple in Python? When would you use one over the other?",
    "expected_concepts": [
        "mutable",
        "immutable",
        "syntax bracket",
        "hashable",
        "dictionary key",
        "performance memory"
    ],
    "reference_answer": "In Python, lists are mutable and defined using square brackets []. Tuples are immutable and defined using parentheses (). Because tuples are immutable, they are hashable and can be used as dictionary keys, whereas lists cannot. Tuples also have a smaller memory footprint and faster iteration.",
    "evaluation_criteria": "Full marks require explaining mutability, syntax, hashability/dict keys, and memory footprint.",
    "follow_up_question": "Can a tuple contain mutable elements?"
}


def test_evaluator_correct_answer():
    """Verify that a comprehensive, concept-rich answer receives a high score."""
    evaluator = AnswerEvaluator()
    student_answer = (
        "In Python, the fundamental difference is that lists are mutable while tuples are immutable. "
        "Lists use square brackets [] whereas tuples use parentheses (). Because tuples cannot be mutated, "
        "they are hashable and can be used as dictionary keys or in sets, which lists cannot. "
        "Furthermore, tuples have lower memory overhead and offer better performance for fixed collections."
    )
    result = evaluator.evaluate_rule_based(SAMPLE_QUESTION, student_answer)

    assert result.score >= 7.0
    assert "mutable" in result.concepts_covered
    assert "immutable" in result.concepts_covered
    assert "dictionary key" in result.concepts_covered or "hashable" in result.concepts_covered
    assert result.evaluation_mode == "Rule-Based Engine"
    assert len(result.feedback) > 10


def test_evaluator_partially_correct_answer():
    """Verify that a partially correct answer gets a moderate score and pinpoints missing concepts."""
    evaluator = AnswerEvaluator()
    student_answer = "Lists can be changed after creation because they are mutable, but tuples are immutable."
    result = evaluator.evaluate_rule_based(SAMPLE_QUESTION, student_answer)

    assert 3.0 <= result.score <= 7.0
    assert "mutable" in result.concepts_covered
    assert "immutable" in result.concepts_covered
    # Missing dictionary key / hashability should be flagged
    assert any("hashable" in m or "dictionary key" in m for m in result.concepts_missing)


def test_evaluator_irrelevant_or_empty_answer():
    """Verify that empty, gibberish, or irrelevant answers receive negligible scores."""
    evaluator = AnswerEvaluator()

    # Empty
    res_empty = evaluator.evaluate_rule_based(SAMPLE_QUESTION, "")
    assert res_empty.score <= 1.0
    assert len(res_empty.concepts_missing) == len(SAMPLE_QUESTION["expected_concepts"])

    # Placeholder / IDK
    res_idk = evaluator.evaluate_rule_based(SAMPLE_QUESTION, "I don't know")
    assert res_idk.score <= 1.0

    # Off-topic gibberish
    res_gibberish = evaluator.evaluate_rule_based(SAMPLE_QUESTION, "asdfasdfasdfasdf zzzzz")
    assert res_gibberish.score <= 1.5


def test_evaluator_does_not_score_on_length_alone():
    """Ensure that verbose text with no relevant technical concepts does not score high."""
    evaluator = AnswerEvaluator()
    long_nonsense = (
        "This is an interesting topic and I really think it has a lot to do with computer science in general. "
        "Many people believe different things about this subject. It depends on the environment and how you "
        "configure your computer systems. Generally speaking, things can be very different when programming."
    )
    result = evaluator.evaluate_rule_based(SAMPLE_QUESTION, long_nonsense)

    assert result.score < 4.0
    assert len(result.concepts_covered) == 0
