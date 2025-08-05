---
id: task-11
title: Phase out full-text embeddings after summary embedding validation
status: To Do
assignee: []
created_date: '2025-08-05 17:57'
labels:
  - cleanup
  - deprecation
dependencies:
  - task-10
priority: low
---

## Description

Remove or deprecate the full-text embedding functionality once summary embeddings prove superior in A/B testing. This includes cleaning up unused database columns, removing generation scripts, and updating documentation to reflect the new embedding strategy.

## Acceptance Criteria

- [ ] Full-text embedding generation scripts are deprecated or removed
- [ ] workout_embedding column is marked for future removal or archived
- [ ] Documentation updated to reflect summary embedding as the primary approach
- [ ] Search codebase no longer references full-text embeddings
- [ ] Database cleanup migration prepared for removing unused embedding data
