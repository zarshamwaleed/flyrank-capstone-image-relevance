from app.core.database import SessionLocal
from app.services.matching_service import matching_service
from app.models.post import BlogPost
from app.models.suggestion import Suggestion

db = SessionLocal()

# Get all posts
posts = db.query(BlogPost).all()
print(f'Found {len(posts)} blog posts')

total_saved = 0

for post in posts:
    print(f'Processing: {post.title}')
    
    # Get matches
    matches, total = matching_service.find_matches(post.id, db, 5, 0)
    
    if matches:
        # Delete existing suggestions for this post
        db.query(Suggestion).filter(Suggestion.post_id == post.id).delete()
        
        # Create new suggestions
        for i, match in enumerate(matches, 1):
            suggestion = Suggestion(
                post_id=post.id,
                image_id=match['image_id'],
                similarity_score=match['similarity_score'],
                guard_passed='pending',
                rank=i
            )
            db.add(suggestion)
            total_saved += 1
        
        db.commit()
        print(f'  ✅ Created {len(matches)} suggestions')
    else:
        print(f'  ❌ No matches found')

db.close()
print(f'\n✅ DONE! Saved {total_saved} suggestions total')
