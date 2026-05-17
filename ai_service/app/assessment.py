"""
ai_service/app/assessment.py — Complete AI Assessment Pipeline

Integrated with SkillCert system:
  1. Institutions upload learning materials
  2. AI generates contextual exam questions
  3. Students answer questions
  4. AI grades answers against material
  5. Provides scoring + feedback
  6. Results fed to backend for blockchain certification
"""

import json
import hashlib
from typing import List, Dict, Any
from datetime import datetime
from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

# ═══════════════════════════════════════════════════════════════════════════
# 1. MATERIAL INGESTION & STORAGE
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class LearningMaterial:
    """Represents learning material from an institution"""
    material_id: str
    institution_id: str
    programme: str
    title: str
    content: str
    topics: List[str]
    difficulty_level: str  # "beginner", "intermediate", "advanced"
    created_at: str
    content_hash: str  # For integrity verification

    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = hashlib.sha256(self.content.encode()).hexdigest()


class MaterialStore:
    """
    In-memory store for learning materials.
    In production, this would be PostgreSQL via backend.
    """
    def __init__(self):
        self.materials: Dict[str, LearningMaterial] = {}

    def ingest_material(self, material: LearningMaterial) -> str:
        """Store learning material and return material_id"""
        self.materials[material.material_id] = material
        return material.material_id

    def get_material(self, material_id: str) -> LearningMaterial:
        """Retrieve material by ID"""
        return self.materials.get(material_id)

    def extract_key_concepts(self, content: str, num_concepts: int = 5) -> List[str]:
        """Extract key concepts from material using TF-IDF"""
        # Simple concept extraction: sentences with high TF-IDF scores
        sentences = content.split('.')
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

        if len(sentences) < num_concepts:
            return sentences

        vectorizer = TfidfVectorizer(max_features=50, stop_words='english')
        try:
            vectorizer.fit_transform(sentences)
            feature_names = np.array(vectorizer.get_feature_names_out())

            # Get top sentences by TF-IDF
            tfidf_matrix = vectorizer.transform(sentences)
            importance = tfidf_matrix.mean(axis=1).A1
            top_indices = np.argsort(importance)[-num_concepts:]

            return [sentences[i] for i in sorted(top_indices)]
        except:
            return sentences[:num_concepts]


# ═══════════════════════════════════════════════════════════════════════════
# 2. QUESTION GENERATION
# ═══════════════════════════════════════════════════════════════════════════

class QuestionGenerator:
    """
    Generates exam questions from learning materials using rule-based + ML approach.
    
    Question types:
    - Definition (recall)
    - Conceptual (understanding)
    - Application (higher-order)
    - Analysis (critical thinking)
    """

    def __init__(self):
        self.question_templates = {
            "definition": [
                "What is {concept}?",
                "Define {concept} in the context of {domain}",
                "Explain the meaning of {concept}",
            ],
            "conceptual": [
                "Why is {concept} important in {domain}?",
                "How does {concept} relate to {related_concept}?",
                "Describe the role of {concept} in {context}",
            ],
            "application": [
                "How would you apply {concept} to {scenario}?",
                "In what situations is {concept} used?",
                "Provide an example of {concept} in practice",
            ],
            "analysis": [
                "Compare {concept} with {related_concept}",
                "What are the advantages and disadvantages of {concept}?",
                "How would you address {challenge} using {concept}?",
            ],
        }

    def generate_questions(
        self,
        material: LearningMaterial,
        num_questions: int = 5,
        difficulty: str = "mixed"
    ) -> List[Dict[str, Any]]:
        """
        Generate exam questions from material
        
        Args:
            material: LearningMaterial object
            num_questions: Number of questions to generate
            difficulty: "easy", "medium", "hard", or "mixed"
        
        Returns:
            List of question dicts with {question, type, difficulty, concepts}
        """
        questions = []
        
        # Extract concepts from material
        concepts = self._extract_concepts(material.content)
        
        if not concepts:
            return []

        # Generate questions of different types
        question_types = ["definition", "conceptual", "application", "analysis"]
        
        for i in range(num_questions):
            q_type = question_types[i % len(question_types)]
            difficulty_level = self._get_difficulty(i, num_questions, difficulty)
            
            concept = concepts[i % len(concepts)]
            
            question_text = self._create_question(
                q_type=q_type,
                concept=concept,
                material=material,
                difficulty=difficulty_level
            )
            
            questions.append({
                "question_id": f"q_{i+1}",
                "question": question_text,
                "type": q_type,
                "difficulty": difficulty_level,
                "concept": concept,
                "points": self._get_points(difficulty_level),
                "material_id": material.material_id,
            })

        return questions

    def _extract_concepts(self, content: str, num_concepts: int = 5) -> List[str]:
        """Extract key concepts from material"""
        # Simple extraction: split by periods and take unique noun phrases
        sentences = content.split('.')
        concepts = []
        
        for sentence in sentences[:num_concepts]:
            # Simple: extract first noun phrase as concept
            words = sentence.strip().split()
            if len(words) > 1:
                concept = ' '.join(words[:3]).strip()
                concepts.append(concept)
        
        return concepts if concepts else ["the main topic"]

    def _get_difficulty(self, index: int, total: int, difficulty: str) -> str:
        """Determine question difficulty"""
        if difficulty == "mixed":
            if index < total // 3:
                return "easy"
            elif index < 2 * total // 3:
                return "medium"
            else:
                return "hard"
        return difficulty

    def _get_points(self, difficulty: str) -> int:
        """Points based on difficulty"""
        return {"easy": 1, "medium": 2, "hard": 3}.get(difficulty, 1)

    def _create_question(
        self,
        q_type: str,
        concept: str,
        material: LearningMaterial,
        difficulty: str
    ) -> str:
        """Create actual question text using templates"""
        templates = self.question_templates.get(q_type, [])
        if not templates:
            return f"What is {concept}?"
        
        template = templates[0]
        
        # Simple substitution (production would use NLP)
        question = template.replace("{concept}", concept)
        question = question.replace("{domain}", material.programme)
        question = question.replace("{context}", "this module")
        question = question.replace("{related_concept}", "related skills")
        question = question.replace("{scenario}", "a real-world situation")
        question = question.replace("{challenge}", "a typical problem")
        
        return question


# ═══════════════════════════════════════════════════════════════════════════
# 3. ANSWER GRADING & ASSESSMENT
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class StudentAnswer:
    """Represents a student's answer to a question"""
    assessment_id: str
    question_id: str
    student_id: str
    answer_text: str
    submission_time: str


class AnswerGrader:
    """
    Grades student answers against learning material.
    
    Scoring approach:
    - Semantic similarity to key concepts (cosine similarity)
    - Keyword matching
    - Answer length/completeness check
    - Question type-specific rubrics
    """

    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english')

    def grade_answer(
        self,
        question: Dict[str, Any],
        answer: str,
        material: LearningMaterial
    ) -> Dict[str, Any]:
        """
        Grade an answer and provide feedback
        
        Args:
            question: Question dict from QuestionGenerator
            answer: Student's answer text
            material: Original learning material
        
        Returns:
            {score, max_points, feedback, confidence, rubric_scores}
        """
        
        # Extract relevant section from material
        relevant_section = self._extract_relevant_section(
            material.content,
            question.get("concept", "")
        )
        
        # Grade based on question type
        question_type = question.get("type", "definition")
        
        if question_type == "definition":
            score, feedback = self._grade_definition(answer, relevant_section, question)
        elif question_type == "conceptual":
            score, feedback = self._grade_conceptual(answer, relevant_section, question)
        elif question_type == "application":
            score, feedback = self._grade_application(answer, relevant_section, question)
        elif question_type == "analysis":
            score, feedback = self._grade_analysis(answer, relevant_section, question)
        else:
            score, feedback = 0.5, "Question type not recognized"
        
        max_points = question.get("points", 1)
        points_earned = int(score * max_points)
        
        return {
            "score": score,  # 0.0 to 1.0
            "points_earned": points_earned,
            "max_points": max_points,
            "feedback": feedback,
            "confidence": self._calculate_confidence(answer, relevant_section),
            "rubric_scores": {
                "completeness": self._score_completeness(answer),
                "accuracy": score,
                "clarity": self._score_clarity(answer),
            }
        }

    def _extract_relevant_section(self, material: str, concept: str) -> str:
        """Extract material section relevant to the concept"""
        sentences = material.split('.')
        relevant = [s for s in sentences if concept.lower() in s.lower()]
        return '. '.join(relevant) if relevant else material[:500]

    def _grade_definition(self, answer: str, material_section: str, question: Dict) -> tuple:
        """Grade a definition question"""
        # Check if answer contains key words from material
        material_words = set(material_section.lower().split())
        answer_words = set(answer.lower().split())
        
        overlap = len(answer_words & material_words) / (len(answer_words) + 1)
        
        # Bonus for completeness
        completeness = min(len(answer.split()) / 20, 1.0)  # 20 words = full marks
        
        score = min(overlap * 0.6 + completeness * 0.4, 1.0)
        
        if score > 0.7:
            feedback = "Good definition that captures the key concept."
        elif score > 0.4:
            feedback = "Partial answer. Consider including more details from the material."
        else:
            feedback = "Answer missing key aspects. Review the material carefully."
        
        return score, feedback

    def _grade_conceptual(self, answer: str, material_section: str, question: Dict) -> tuple:
        """Grade a conceptual understanding question"""
        # Semantic similarity
        try:
            vectors = self.vectorizer.fit_transform([material_section, answer])
            similarity = cosine_similarity(vectors[0], vectors[1])[0][0]
        except:
            similarity = 0.5
        
        # Check for explanation keywords
        explanation_indicators = ['because', 'reason', 'causes', 'affects', 'related', 'connected']
        has_explanation = any(word in answer.lower() for word in explanation_indicators)
        
        score = (similarity * 0.7 + (0.3 if has_explanation else 0.1))
        
        if score > 0.7:
            feedback = "Excellent understanding demonstrated with clear explanations."
        elif score > 0.4:
            feedback = "Good grasp of the concept. Add more explanation of connections."
        else:
            feedback = "Review the material. Consider how different concepts relate."
        
        return min(score, 1.0), feedback

    def _grade_application(self, answer: str, material_section: str, question: Dict) -> tuple:
        """Grade an application question"""
        # Check for practical elements
        has_example = any(word in answer.lower() for word in ['example', 'scenario', 'situation', 'case', 'real'])
        has_practical = any(word in answer.lower() for word in ['use', 'apply', 'implement', 'perform', 'practice'])
        has_reason = any(word in answer.lower() for word in ['because', 'reason', 'since', 'therefore'])
        
        # Length check (application answers should be more detailed)
        completeness = min(len(answer.split()) / 30, 1.0)  # 30 words for application
        
        score = (
            (0.3 if has_example else 0) +
            (0.3 if has_practical else 0) +
            (0.2 if has_reason else 0) +
            (0.2 * completeness)
        )
        
        if score > 0.7:
            feedback = "Excellent application with clear examples and reasoning."
        elif score > 0.4:
            feedback = "Good attempt. Provide more concrete examples from practice."
        else:
            feedback = "Application unclear. Work through a specific example step-by-step."
        
        return score, feedback

    def _grade_analysis(self, answer: str, material_section: str, question: Dict) -> tuple:
        """Grade an analysis/synthesis question"""
        # Look for critical thinking indicators
        critical_words = ['however', 'although', 'while', 'versus', 'compared', 'advantage', 'disadvantage', 'tradeoff']
        critical_thinking = sum(1 for word in critical_words if word in answer.lower())
        
        # Semantic match
        try:
            vectors = self.vectorizer.fit_transform([material_section, answer])
            similarity = cosine_similarity(vectors[0], vectors[1])[0][0]
        except:
            similarity = 0.5
        
        score = (similarity * 0.6 + min(critical_thinking / 3, 0.4))
        
        if score > 0.7:
            feedback = "Sophisticated analysis with clear critical thinking."
        elif score > 0.4:
            feedback = "Good analysis. Develop more comparative or contrasting points."
        else:
            feedback = "Deepen your analysis. Consider multiple perspectives and tradeoffs."
        
        return min(score, 1.0), feedback

    def _calculate_confidence(self, answer: str, material: str) -> float:
        """Calculate confidence in grade (0-1)"""
        # Confidence based on answer length and material overlap
        answer_length = len(answer.split())
        overlap_ratio = len(set(answer.lower().split()) & set(material.lower().split())) / (len(answer.split()) + 1)
        
        confidence = (min(answer_length / 50, 1.0) * 0.5 + overlap_ratio * 0.5)
        return min(confidence, 1.0)

    def _score_completeness(self, answer: str) -> float:
        """Score answer completeness (0-1)"""
        word_count = len(answer.split())
        return min(word_count / 40, 1.0)

    def _score_clarity(self, answer: str) -> float:
        """Score answer clarity (0-1)"""
        # Simple: proper grammar indicators
        sentences = answer.split('.')
        avg_sentence_length = len(answer.split()) / (len(sentences) + 1)
        
        # Ideal sentence length: 10-25 words
        clarity = 1.0 - abs(avg_sentence_length - 15) / 15
        return max(min(clarity, 1.0), 0.3)


# ═══════════════════════════════════════════════════════════════════════════
# 4. ASSESSMENT SESSION MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class AssessmentSession:
    """Represents one student's assessment attempt"""
    assessment_id: str
    student_id: str
    institution_id: str
    material_id: str
    questions: List[Dict[str, Any]]
    answers: List[StudentAnswer]
    started_at: str
    completed_at: str = None
    scores: List[float] = None


class AssessmentEngine:
    """
    Orchestrates full assessment: material → questions → grading → results
    """

    def __init__(self):
        self.material_store = MaterialStore()
        self.question_generator = QuestionGenerator()
        self.answer_grader = AnswerGrader()
        self.sessions: Dict[str, AssessmentSession] = {}

    def create_assessment(
        self,
        institution_id: str,
        material_id: str,
        student_id: str,
        num_questions: int = 5,
        difficulty: str = "mixed"
    ) -> Dict[str, Any]:
        """
        Create and return a new assessment
        
        Flow: Material → Generate Questions → Create Session
        """
        
        # Get material
        material = self.material_store.get_material(material_id)
        if not material:
            return {"error": "Material not found"}
        
        # Generate questions
        questions = self.question_generator.generate_questions(
            material=material,
            num_questions=num_questions,
            difficulty=difficulty
        )
        
        if not questions:
            return {"error": "Could not generate questions"}
        
        # Create assessment session
        assessment_id = f"assess_{int(datetime.now().timestamp())}"
        session = AssessmentSession(
            assessment_id=assessment_id,
            student_id=student_id,
            institution_id=institution_id,
            material_id=material_id,
            questions=questions,
            answers=[],
            started_at=datetime.now().isoformat()
        )
        
        self.sessions[assessment_id] = session
        
        return {
            "assessment_id": assessment_id,
            "material_title": material.title,
            "num_questions": len(questions),
            "questions": [
                {
                    "question_id": q["question_id"],
                    "question": q["question"],
                    "type": q["type"],
                    "difficulty": q["difficulty"],
                    "points": q["points"],
                }
                for q in questions
            ]
        }

    def submit_answer(
        self,
        assessment_id: str,
        question_id: str,
        answer_text: str
    ) -> Dict[str, Any]:
        """Student submits an answer"""
        
        session = self.sessions.get(assessment_id)
        if not session:
            return {"error": "Assessment not found"}
        
        # Store answer
        student_answer = StudentAnswer(
            assessment_id=assessment_id,
            question_id=question_id,
            student_id=session.student_id,
            answer_text=answer_text,
            submission_time=datetime.now().isoformat()
        )
        
        session.answers.append(student_answer)
        
        return {
            "assessment_id": assessment_id,
            "question_id": question_id,
            "received": True,
            "progress": f"{len(session.answers)}/{len(session.questions)}"
        }

    def grade_assessment(self, assessment_id: str) -> Dict[str, Any]:
        """
        Grade all answers and return results
        
        Returns: {score, max_score, percentage, feedback_per_question, overall_feedback}
        """
        
        session = self.sessions.get(assessment_id)
        if not session:
            return {"error": "Assessment not found"}
        
        material = self.material_store.get_material(session.material_id)
        if not material:
            return {"error": "Material not found"}
        
        # Grade each answer
        results = []
        total_points = 0
        total_earned = 0
        
        for question in session.questions:
            # Find corresponding answer
            answer_obj = next(
                (a for a in session.answers if a.question_id == question["question_id"]),
                None
            )
            
            if not answer_obj:
                grade = {"score": 0, "points_earned": 0, "max_points": question["points"], "feedback": "Not answered"}
            else:
                grade = self.answer_grader.grade_answer(
                    question=question,
                    answer=answer_obj.answer_text,
                    material=material
                )
            
            total_earned += grade["points_earned"]
            total_points += grade["max_points"]
            
            results.append({
                "question_id": question["question_id"],
                "question": question["question"],
                "answer": answer_obj.answer_text if answer_obj else "Not answered",
                **grade
            })
        
        # Calculate overall
        percentage = (total_earned / total_points * 100) if total_points > 0 else 0
        overall_feedback = self._generate_overall_feedback(percentage, material.programme)
        
        # Update session
        session.completed_at = datetime.now().isoformat()
        session.scores = [r["score"] for r in results]
        
        return {
            "assessment_id": assessment_id,
            "student_id": session.student_id,
            "material_id": session.material_id,
            "total_earned": total_earned,
            "total_points": total_points,
            "percentage": round(percentage, 2),
            "passed": percentage >= 70,  # 70% pass threshold
            "overall_feedback": overall_feedback,
            "detailed_results": results,
            "completed_at": session.completed_at
        }

    def _generate_overall_feedback(self, percentage: float, programme: str) -> str:
        """Generate overall assessment feedback"""
        if percentage >= 90:
            return f"Excellent mastery of {programme} concepts. Outstanding work!"
        elif percentage >= 80:
            return f"Strong understanding of {programme}. Well prepared."
        elif percentage >= 70:
            return f"Competent grasp of {programme} fundamentals. Keep practicing."
        elif percentage >= 50:
            return f"Foundational understanding of {programme}. Review weak areas."
        else:
            return f"Needs more study in {programme}. Revisit the material."

    def get_assessment_summary(self, assessment_id: str) -> Dict[str, Any]:
        """Get summary of an assessment"""
        session = self.sessions.get(assessment_id)
        if not session:
            return {"error": "Assessment not found"}
        
        return {
            "assessment_id": assessment_id,
            "student_id": session.student_id,
            "material_id": session.material_id,
            "num_questions": len(session.questions),
            "num_answers": len(session.answers),
            "started_at": session.started_at,
            "completed_at": session.completed_at,
            "is_complete": session.completed_at is not None
        }


# ═══════════════════════════════════════════════════════════════════════════
# Global engine instance (used by FastAPI routes)
# ═══════════════════════════════════════════════════════════════════════════

assessment_engine = AssessmentEngine()