---
id: task-6
title: Execute SQL migration to add summary_embedding column
status: To Do
assignee: []
created_date: '2025-08-05 17:56'
labels:
  - database
  - migration
dependencies: []
priority: high
---

## Description

Run the SQL migration script 004_add_summary_embedding.sql to add the summary_embedding column to the workouts table in the database. This creates the infrastructure needed to store embeddings generated from one-sentence summaries alongside existing full-text embeddings.

## Acceptance Criteria

- [ ] Database schema updated with summary_embedding column of type vector(1536)
- [ ] IVF index created for efficient similarity search on summary embeddings
- [ ] Migration completed without errors affecting existing data
