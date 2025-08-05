---
id: task-10
title: Update search functionality to use summary embeddings by default
status: To Do
assignee: []
created_date: '2025-08-05 17:57'
labels:
  - search
  - backend
dependencies:
  - task-9
priority: medium
---

## Description

Modify the search and similarity functions in the workout repository and service layers to use summary_embedding instead of workout_embedding for semantic search. This includes updating the vector similarity queries and ensuring backward compatibility during the transition.

## Acceptance Criteria

- [ ] Semantic search queries use summary_embedding column instead of workout_embedding
- [ ] Search performance is maintained or improved with summary embeddings
- [ ] Fallback mechanism handles workouts without summary embeddings gracefully
- [ ] Search API responses maintain the same format and accuracy
- [ ] Database queries use the correct vector similarity index for summary embeddings
