"""
ai_service/app/main.py — FastAPI routes for AI Assessment Service

Integrated Assessment Pipeline:
  1. Institution uploads learning material
  2. AI generates contextual exam questions
  3. Student takes exam (answers questions)
  4. AI grades answers against material
  5. Results feed to backend for blockchain cert

Endpoints:
  POST /ingest-material        — Institution uploads learning material
  POST /create-assessment      — Generate exam questions from material
  POST /submit-answer          — Student submits answer
  POST /grade-assessment       — Grade all answers and provide feedback
  GET  /assessment/{id}/summary — Get assessment status/results
  GET  /health                 — Health check
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from assessment import (
    LearningMaterial,
    assessment_engine,
)

# ═══════════════════════════════════════════════════════════════════════════
# FastAPI App Setup
# ═══════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="SkillCert AI Assessment Service",
    description="Generates exams from materials and grades student answers",
    version="2.0"
)

# CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════════════════════
# Request/Response Models
# ═══════════════════════════════════════════════════════════════════════════

class MaterialIngestionRequest(BaseModel):
    """Institution uploads learning material"""
    institution_id: str
    programme: str
    title: str
    content: str
    difficulty_level: str = "intermediate"
    topics: Optional[List[str]] = None


class AssessmentCreationRequest(BaseModel):
    """Create assessment from material"""
    material_id: str
    student_id: str
    num_questions: int = 5
    difficulty: str = "mixed"


class AnswerSubmissionRequest(BaseModel):
    """Student submits answer to question"""
    assessment_id: str
    question_id: str
    answer_text: str


# ═══════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "SkillCert AI Assessment",
        "version": "2.0",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/ingest-material")
async def ingest_material(req: MaterialIngestionRequest):
    """
    Institution uploads learning material
    
    Used by: Backend API → Institution Dashboard
    Flow: Material → Stored → Ready for assessment
    """
    
    try:
        material = LearningMaterial(
            material_id=f"mat_{int(datetime.now().timestamp())}",
            institution_id=req.institution_id,
            programme=req.programme,
            title=req.title,
            content=req.content,
            topics=req.topics or [],
            difficulty_level=req.difficulty_level,
            created_at=datetime.now().isoformat(),
            content_hash=""
        )
        
        material_id = assessment_engine.material_store.ingest_material(material)
        
        key_concepts = assessment_engine.material_store.extract_key_concepts(
            req.content,
            num_concepts=5
        )
        
        return {
            "status": "success",
            "material_id": material_id,
            "institution_id": req.institution_id,
            "programme": req.programme,
            "title": req.title,
            "content_length": len(req.content),
            "key_concepts": key_concepts,
            "created_at": material.created_at,
            "ready_for_assessment": True
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/create-assessment")
async def create_assessment(req: AssessmentCreationRequest):
    """
    Generate exam questions from material
    
    Used by: Learner Portal → "Start Assessment"
    Flow: Material → Questions → Student answers
    """
    
    try:
        result = assessment_engine.create_assessment(
            institution_id="",
            material_id=req.material_id,
            student_id=req.student_id,
            num_questions=req.num_questions,
            difficulty=req.difficulty
        )
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return {
            "status": "success",
            "assessment_id": result["assessment_id"],
            "material_title": result["material_title"],
            "num_questions": result["num_questions"],
            "student_id": req.student_id,
            "questions": result["questions"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/submit-answer")
async def submit_answer(req: AnswerSubmissionRequest):
    """
    Student submits answer to question
    
    Used by: Learner Portal → Answer input → "Next"
    Flow: Stores answer, continues assessment
    """
    
    try:
        result = assessment_engine.submit_answer(
            assessment_id=req.assessment_id,
            question_id=req.question_id,
            answer_text=req.answer_text
        )
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return {
            "status": "success",
            "assessment_id": result["assessment_id"],
            "question_id": result["question_id"],
            "received": result["received"],
            "progress": result["progress"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/grade-assessment")
async def grade_assessment_endpoint(assessment_id: str):
    """
    Grade completed assessment
    
    Used by: Learner Portal → "Submit Assessment"
    Returns: Scores + feedback + PASS/FAIL → Backend for blockchain
    """
    
    try:
        result = assessment_engine.grade_assessment(assessment_id)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return {
            "status": "success",
            "assessment_id": result["assessment_id"],
            "student_id": result["student_id"],
            "total_earned": result["total_earned"],
            "total_points": result["total_points"],
            "percentage": result["percentage"],
            "passed": result["passed"],
            "overall_feedback": result["overall_feedback"],
            "detailed_results": result["detailed_results"],
            "completed_at": result["completed_at"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/assessment/{assessment_id}/summary")
async def get_assessment_summary(assessment_id: str):
    """Get assessment status and progress"""
    
    try:
        result = assessment_engine.get_assessment_summary(assessment_id)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return {
            "status": "success",
            "assessment_id": result["assessment_id"],
            "student_id": result["student_id"],
            "num_questions": result["num_questions"],
            "answered": result["num_answers"],
            "progress_percent": (result["num_answers"] / result["num_questions"] * 100) if result["num_questions"] > 0 else 0,
            "is_complete": result["is_complete"],
            "started_at": result["started_at"],
            "completed_at": result["completed_at"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)