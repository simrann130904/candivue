import os
import re
import json
import urllib.request
import urllib.error
from typing import Dict, List, Any, Tuple, Optional


COMMON_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "because", "as", "what",
    "which", "this", "that", "these", "those", "then", "just", "so", "than",
    "such", "both", "through", "about", "for", "is", "of", "while", "during",
    "to", "from", "in", "out", "on", "off", "again", "further", "then", "once",
    "here", "there", "when", "where", "why", "how", "all", "any", "both",
    "each", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "can", "will",
    "don", "should", "now", "are", "was", "were", "been", "being", "have",
    "has", "had", "do", "does", "did", "doing", "would", "could", "be", "with"
}

IRRELEVANT_PATTERNS = [
    r"^(idk|i don't know|dont know|i have no idea|no idea|skip|pass|dunno|na|n/a|\.)$",
    r"^(nothing|hello|test|testing|hi|bye|foo|bar|asdf|qwerty|zzz)$",
    r"^(i am not sure|not sure|dont remember|cant remember)$"
]


class EvaluationResult:
    """Encapsulates the structured output of an answer evaluation."""

    def __init__(
        self,
        score: float,
        concepts_covered: List[str],
        concepts_missing: List[str],
        feedback: str,
        reference_answer: str,
        evaluation_mode: str,
        follow_up_question: Optional[str] = None,
        technical_depth: str = "Standard"
    ):
        self.score = round(max(0.0, min(10.0, score)), 1)
        self.concepts_covered = concepts_covered
        self.concepts_missing = concepts_missing
        self.feedback = feedback
        self.reference_answer = reference_answer
        self.evaluation_mode = evaluation_mode
        self.follow_up_question = follow_up_question
        self.technical_depth = technical_depth

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "concepts_covered": self.concepts_covered,
            "concepts_missing": self.concepts_missing,
            "feedback": self.feedback,
            "reference_answer": self.reference_answer,
            "evaluation_mode": self.evaluation_mode,
            "follow_up_question": self.follow_up_question,
            "technical_depth": self.technical_depth,
        }


class AnswerEvaluator:
    """Evaluates student technical interview responses using rule-based algorithms with optional LLM augmentation."""

    def __init__(self, api_key: Optional[str] = None):
        # API key can be passed or read from env
        self.api_key = (
            api_key
            or os.environ.get("GEMINI_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
            or ""
        ).strip()

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Convert text to normalized lowercase word tokens without punctuation."""
        return re.findall(r"\b[a-zA-Z0-9_-]+\b", text.lower())

    @staticmethod
    def _is_irrelevant_or_empty(answer: str) -> bool:
        """Detect empty, placeholder, or clearly irrelevant answers."""
        cleaned = answer.strip().lower()
        if len(cleaned) < 4:
            return True
        for pattern in IRRELEVANT_PATTERNS:
            if re.match(pattern, cleaned):
                return True
        # Check repeated character gibberish like 'aaaaaa' or 'sdkfjhsdf'
        tokens = AnswerEvaluator._tokenize(cleaned)
        if len(tokens) <= 2 and all(len(t) > 10 and len(set(t)) < 4 for t in tokens):
            return True
        return False

    def evaluate_rule_based(self, question_data: Dict[str, Any], user_answer: str) -> EvaluationResult:
        """Transparent, deterministic rule-based evaluation of technical answers."""
        ref_answer = question_data.get("reference_answer", "")
        expected_concepts = question_data.get("expected_concepts", [])
        follow_up = question_data.get("follow_up_question")

        if self._is_irrelevant_or_empty(user_answer):
            return EvaluationResult(
                score=0.5 if len(user_answer.strip()) > 0 else 0.0,
                concepts_covered=[],
                concepts_missing=expected_concepts,
                feedback="The answer provided does not address the question or contains placeholder content. In technical placement interviews, even an educated attempt at key definitions scores partial credit.",
                reference_answer=ref_answer,
                evaluation_mode="Rule-Based Engine",
                follow_up_question=follow_up,
                technical_depth="Insufficient"
            )

        user_lower = user_answer.lower()
        user_tokens = set(self._tokenize(user_lower))

        covered: List[str] = []
        missing: List[str] = []

        # Check concept coverage
        for concept in expected_concepts:
            concept_words = self._tokenize(concept)
            # Concept is considered covered if either:
            # 1. The exact multi-word phrase is in the answer, OR
            # 2. A significant subset (e.g. 60%+) of the concept's key terms are present
            exact_match = concept.lower() in user_lower
            meaningful_words = [w for w in concept_words if w not in COMMON_STOPWORDS and len(w) > 2]
            
            if exact_match:
                covered.append(concept)
            elif meaningful_words:
                matches = sum(1 for w in meaningful_words if w in user_tokens or any(w in t for t in user_tokens))
                coverage_ratio = matches / len(meaningful_words)
                if coverage_ratio >= 0.5:
                    covered.append(concept)
                else:
                    missing.append(concept)
            else:
                missing.append(concept)

        total_concepts = len(expected_concepts) if expected_concepts else 1
        concept_ratio = len(covered) / total_concepts

        # Keyword overlap with reference answer (excluding stopwords)
        ref_tokens = [w for w in self._tokenize(ref_answer) if w not in COMMON_STOPWORDS and len(w) > 2]
        ref_token_set = set(ref_tokens)
        shared_tokens = user_tokens.intersection(ref_token_set)
        ref_overlap_ratio = len(shared_tokens) / max(1, len(ref_token_set))

        # Check technical term richness (code snippets, keywords, numbers)
        has_code_markers = any(m in user_answer for m in ["`", "def ", "SELECT", "WHERE", "class ", "()", "->", "O("])
        
        # Calculate score (out of 10)
        # Weighting: Concept coverage 65%, Vocabulary overlap 25%, Formatting/Code bonus 10%
        base_score = (concept_ratio * 6.5) + (min(1.0, ref_overlap_ratio * 2.5) * 2.5)
        if has_code_markers:
            base_score += 1.0

        # Penalize if answer is very brief (< 15 words) and missing most concepts
        word_count = len(self._tokenize(user_answer))
        if word_count < 15 and concept_ratio < 0.4:
            base_score = min(base_score, 3.0)

        final_score = round(min(10.0, max(0.5, base_score)), 1)

        # Construct actionable feedback
        feedback_lines = []
        if final_score >= 8.5:
            feedback_lines.append("🌟 **Excellent explanation!** You demonstrated a strong grasp of the fundamental mechanics and key terminology.")
            technical_depth = "Advanced"
        elif final_score >= 6.5:
            feedback_lines.append("👍 **Solid technical answer.** You hit major architectural and conceptual points accurately.")
            technical_depth = "Proficient"
        elif final_score >= 4.0:
            feedback_lines.append("⚠️ **Partially correct.** You have the right directional intuition, but left out crucial underlying details or specific trade-offs.")
            technical_depth = "Developing"
        else:
            feedback_lines.append("📉 **Needs improvement.** Key technical mechanisms were omitted or explained vaguely.")
            technical_depth = "Novice"

        if covered:
            feedback_lines.append(f"**Strengths identified:** Clearly discussed `{', '.join(covered[:4])}`.")
        if missing:
            feedback_lines.append(f"**Key concepts to incorporate:** For maximum placement marks, be sure to highlight `{', '.join(missing[:4])}`.")

        feedback_str = "\n\n".join(feedback_lines)

        return EvaluationResult(
            score=final_score,
            concepts_covered=covered,
            concepts_missing=missing,
            feedback=feedback_str,
            reference_answer=ref_answer,
            evaluation_mode="Rule-Based Engine",
            follow_up_question=follow_up,
            technical_depth=technical_depth
        )

    def evaluate_ai(self, question_data: Dict[str, Any], user_answer: str) -> Optional[EvaluationResult]:
        """Optional AI evaluation using Gemini or OpenAI compatible REST API."""
        if not self.api_key:
            return None

        # Try Gemini API if key is available
        prompt = f"""
You are an expert senior technical interviewer evaluating a college student's answer for campus placement.
Question: {question_data.get('question')}
Subject: {question_data.get('subject')} | Topic: {question_data.get('topic')} | Difficulty: {question_data.get('difficulty')}
Expected Concepts: {json.dumps(question_data.get('expected_concepts', []))}
Reference Answer: {question_data.get('reference_answer')}
Evaluation Criteria: {question_data.get('evaluation_criteria')}

Student Answer:
\"\"\"{user_answer}\"\"\"

Evaluate strictly and objectively. Return ONLY a valid JSON object with these keys:
{{
  "score": <float between 0.0 and 10.0>,
  "concepts_covered": [<list of concepts student explained correctly>],
  "concepts_missing": [<list of expected concepts student omitted or got wrong>],
  "feedback": "<constructive feedback with strengths and gaps, under 120 words>",
  "technical_depth": "<Novice | Developing | Proficient | Advanced>",
  "follow_up_question": "<relevant follow-up question>"
}}
"""
        # Determine whether it's a Gemini or OpenAI endpoint
        try:
            if self.api_key.startswith("AIza"):
                # Gemini endpoint
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
                req_data = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.2, "response_mime_type": "application/json"}
                }
                req = urllib.request.Request(
                    url,
                    data=json.dumps(req_data).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    res_body = json.loads(response.read().decode("utf-8"))
                    text_out = res_body["candidates"][0]["content"]["parts"][0]["text"]
                    parsed = json.loads(text_out)
                    return EvaluationResult(
                        score=float(parsed.get("score", 5.0)),
                        concepts_covered=parsed.get("concepts_covered", []),
                        concepts_missing=parsed.get("concepts_missing", []),
                        feedback=parsed.get("feedback", "AI evaluation completed."),
                        reference_answer=question_data.get("reference_answer", ""),
                        evaluation_mode="AI (Gemini)",
                        follow_up_question=parsed.get("follow_up_question", question_data.get("follow_up_question")),
                        technical_depth=parsed.get("technical_depth", "Proficient")
                    )
            elif self.api_key.startswith("sk-"):
                # OpenAI endpoint
                url = "https://api.openai.com/v1/chat/completions"
                req_data = {
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": "You are a senior technical interviewer returning JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"}
                }
                req = urllib.request.Request(
                    url,
                    data=json.dumps(req_data).encode("utf-8"),
                    headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    res_body = json.loads(response.read().decode("utf-8"))
                    text_out = res_body["choices"][0]["message"]["content"]
                    parsed = json.loads(text_out)
                    return EvaluationResult(
                        score=float(parsed.get("score", 5.0)),
                        concepts_covered=parsed.get("concepts_covered", []),
                        concepts_missing=parsed.get("concepts_missing", []),
                        feedback=parsed.get("feedback", "AI evaluation completed."),
                        reference_answer=question_data.get("reference_answer", ""),
                        evaluation_mode="AI (OpenAI)",
                        follow_up_question=parsed.get("follow_up_question", question_data.get("follow_up_question")),
                        technical_depth=parsed.get("technical_depth", "Proficient")
                    )
        except Exception:
            # Fallback to rule-based silently on timeout, invalid key, rate limit, etc.
            return None

        return None

    def evaluate(self, question_data: Dict[str, Any], user_answer: str) -> EvaluationResult:
        """Main entry point. Uses AI if configured and available, otherwise transparent rule-based engine."""
        if self.api_key:
            ai_result = self.evaluate_ai(question_data, user_answer)
            if ai_result is not None:
                return ai_result

        # Default guaranteed offline rule-based evaluation
        return self.evaluate_rule_based(question_data, user_answer)
