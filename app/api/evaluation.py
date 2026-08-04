from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.evaluation_service import evaluation_engine

router = APIRouter()


@router.get("/dataset")
async def get_evaluation_dataset(db: Session = Depends(get_db)):
    # Get the evaluation dataset (ground truth)
    dataset = evaluation_engine.create_evaluation_dataset(db)
    return {
        "total_samples": len(dataset),
        "dataset": dataset
    }


@router.post("/run")
async def run_evaluation(
    top_k: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    # Run evaluation
    result = evaluation_engine.run_evaluation(db, top_k)
    return result


@router.get("/report")
async def get_evaluation_report(db: Session = Depends(get_db)):
    # Generate evaluation report
    return evaluation_engine.generate_report(db)


@router.get("/precision")
async def get_precision_metrics(db: Session = Depends(get_db)):
    # Get precision metrics only
    result = evaluation_engine.run_evaluation(db)
    
    if "error" in result:
        return result
    
    return {
        "total_samples": result["total_samples"],
        "correct_predictions": result["correct_predictions"],
        "top1_precision": result["top1_precision"],
        "top3_precision": result["top3_precision"],
        "top5_precision": result["top5_precision"],
        "mean_reciprocal_rank": result["mean_reciprocal_rank"]
    }
