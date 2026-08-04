from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.post import BlogPost
from app.models.image import Image
from app.services.matching_service import matching_service


class EvaluationEngine:
    # Service for evaluating matching accuracy
    
    def create_evaluation_dataset(self, db: Session) -> List[Dict[str, Any]]:
        ground_truth = []
        
        # Get ground truth from database
        result = db.execute(text("""
            SELECT post_id, image_id 
            FROM evaluation_ground_truth
        """))
        
        for row in result:
            post = db.query(BlogPost).filter(BlogPost.id == row[0]).first()
            image = db.query(Image).filter(Image.id == row[1]).first()
            
            if post and image:
                ground_truth.append({
                    "post_id": post.id,
                    "post_title": post.title,
                    "correct_image_id": image.id,
                    "correct_image_filename": image.filename,
                    "correct_subject": image.image_metadata.subject if image.image_metadata else "Unknown"
                })
        
        return ground_truth
    
    def evaluate_post(self, post_id: int, correct_image_id: int, db: Session, top_k: int = 5) -> Dict[str, Any]:
        post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
        if not post or not post.embedding_vector:
            return {
                "post_id": post_id,
                "post_title": post.title if post else "Unknown",
                "correct_image_id": correct_image_id,
                "rank": -1,
                "found": False,
                "error": "No embedding found"
            }
        
        matches, total = matching_service.find_matches(post_id, db, top_k, min_similarity=0)
        
        rank = -1
        for i, match in enumerate(matches, 1):
            if match["image_id"] == correct_image_id:
                rank = i
                break
        
        return {
            "post_id": post_id,
            "post_title": post.title,
            "correct_image_id": correct_image_id,
            "rank": rank,
            "found": rank != -1,
            "top_k": top_k
        }
    
    def run_evaluation(self, db: Session, top_k: int = 5) -> Dict[str, Any]:
        ground_truth = self.create_evaluation_dataset(db)
        
        if not ground_truth:
            return {
                "error": "No ground truth data available. Please create evaluation dataset first.",
                "total_samples": 0,
                "correct_predictions": 0,
                "top1_precision": 0.0,
                "top3_precision": 0.0,
                "top5_precision": 0.0,
                "mean_reciprocal_rank": 0.0,
                "results": []
            }
        
        results = []
        correct_at_1 = 0
        correct_at_3 = 0
        correct_at_5 = 0
        reciprocal_ranks = []
        
        for sample in ground_truth:
            result = self.evaluate_post(
                sample["post_id"],
                sample["correct_image_id"],
                db,
                top_k
            )
            
            results.append({
                "post_id": sample["post_id"],
                "post_title": sample["post_title"],
                "correct_image_id": sample["correct_image_id"],
                "correct_image_filename": sample["correct_image_filename"],
                "rank": result["rank"],
                "found": result["found"]
            })
            
            if result["found"]:
                rank = result["rank"]
                reciprocal_ranks.append(1.0 / rank)
                
                if rank == 1:
                    correct_at_1 += 1
                if rank <= 3:
                    correct_at_3 += 1
                if rank <= 5:
                    correct_at_5 += 1
        
        total = len(ground_truth)
        top1_precision = correct_at_1 / total if total > 0 else 0
        top3_precision = correct_at_3 / total if total > 0 else 0
        top5_precision = correct_at_5 / total if total > 0 else 0
        mrr = sum(reciprocal_ranks) / total if total > 0 else 0
        
        if top1_precision >= 0.8:
            recommendation = "Excellent! Your matching engine is working very well."
        elif top1_precision >= 0.6:
            recommendation = "Good performance. Consider improving your embeddings."
        elif top1_precision >= 0.4:
            recommendation = "Moderate performance. Try using better models for embeddings."
        else:
            recommendation = "Low performance. Check your embedding models and data quality."
        
        return {
            "total_samples": total,
            "correct_predictions": correct_at_1,
            "top1_precision": top1_precision,
            "top3_precision": top3_precision,
            "top5_precision": top5_precision,
            "mean_reciprocal_rank": mrr,
            "results": results,
            "recommendation": recommendation
        }
    
    def generate_report(self, db: Session) -> Dict[str, Any]:
        result = self.run_evaluation(db)
        
        if "error" in result:
            return result
        
        summary = f"""
        ========================================
        EVALUATION REPORT
        ========================================
        
        Total Samples: {result['total_samples']}
        Correct Predictions (Top-1): {result['correct_predictions']}
        
        Top-1 Precision: {result['top1_precision']:.2%}
        Top-3 Precision: {result['top3_precision']:.2%}
        Top-5 Precision: {result['top5_precision']:.2%}
        Mean Reciprocal Rank: {result['mean_reciprocal_rank']:.3f}
        
        Recommendation: {result['recommendation']}
        ========================================
        """
        
        return {
            "summary": summary,
            "metrics": {
                "top1_precision": result["top1_precision"],
                "top3_precision": result["top3_precision"],
                "top5_precision": result["top5_precision"],
                "mean_reciprocal_rank": result["mean_reciprocal_rank"]
            },
            "details": result["results"],
            "recommendation": result["recommendation"]
        }


evaluation_engine = EvaluationEngine()
