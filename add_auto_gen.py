import sys
sys.path.append('/app')

# Read the current posts.py file
with open('/app/app/api/posts.py', 'r') as f:
    content = f.read()

# Check if auto-generation is already added
if 'auto_generate_suggestions' not in content:
    print('Adding auto-generation to posts.py...')
    
    # Add the import
    content = content.replace(
        'from app.services.embedding_service import embedding_service',
        'from app.services.embedding_service import embedding_service\nfrom app.services.matching_service import matching_service\nfrom app.models.suggestion import Suggestion'
    )
    
    # Add auto-generation after post creation
    content = content.replace(
        'db.refresh(db_post)\n    \n    return db_post',
        'db.refresh(db_post)\n    \n    # Auto-generate suggestions\n    try:\n        matches, total = matching_service.find_matches(db_post.id, db, 5, 0)\n        for i, match in enumerate(matches, 1):\n            suggestion = Suggestion(\n                post_id=db_post.id,\n                image_id=match["image_id"],\n                similarity_score=match["similarity_score"],\n                guard_passed="pending",\n                rank=i\n            )\n            db.add(suggestion)\n        db.commit()\n        print(f"Auto-generated {len(matches)} suggestions for post {db_post.id}")\n    except Exception as e:\n        print(f"Error auto-generating suggestions: {e}")\n    \n    return db_post'
    )
    
    # Write back
    with open('/app/app/api/posts.py', 'w') as f:
        f.write(content)
    
    print('✅ Auto-generation added!')
else:
    print('Auto-generation already exists!')
