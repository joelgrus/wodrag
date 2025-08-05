---
id: task-7
title: Re-extract metadata for all workouts to populate one_sentence_summary
status: To Do
assignee: []
created_date: '2025-08-05 17:56'
labels:
  - metadata
  - data-processing
dependencies:
  - task-6
priority: high
---

## Description

Re-run the metadata extraction process for all existing workouts in the database to ensure one_sentence_summary fields are populated. This is required because the summary embedding generation depends on having quality one-sentence summaries for all workouts.

## Acceptance Criteria

- [ ] Metadata extraction script runs successfully on all existing workouts
- [ ] All workouts have one_sentence_summary field populated with concise workout descriptions
- [ ] No existing workout data is corrupted during the re-extraction process
- [ ] Progress tracking shows completion status for large dataset
