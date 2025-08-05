#!/usr/bin/env python3
"""
Script to extract and populate metadata for all workouts in the database.

This script:
1. Iterates over all records in the database
2. Extracts metadata using the ExtractMetadata agent
3. Updates the database with the extracted metadata
4. Handles batching, error recovery, and progress tracking
"""

import argparse
import logging
import time
from datetime import UTC, datetime
from typing import Any

import dspy  # type: ignore
from postgrest.exceptions import APIError

from wodrag.agents.extract_metadata import extractor
from wodrag.database import Workout, WorkoutRepository
from wodrag.services import WorkoutService, EmbeddingService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('metadata_extraction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Handles the extraction and population of workout metadata."""

    def __init__(
        self,
        batch_size: int = 50,
        delay_between_batches: float = 1.0,
        max_retries: int = 3,
        retry_delay: float = 5.0
    ):
        self.repository = WorkoutRepository()
        self.embedding_service = EmbeddingService()
        self.workout_service = WorkoutService(self.repository, self.embedding_service)
        self.batch_size = batch_size
        self.delay_between_batches = delay_between_batches
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Statistics
        self.stats: dict[str, Any] = {
            'total_processed': 0,
            'successful_updates': 0,
            'failed_extractions': 0,
            'failed_updates': 0,
            'skipped_no_workout': 0,
            'start_time': datetime.now(UTC)
        }

    def get_workouts_needing_metadata(
        self,
        limit: int | None = None,
        offset: int = 0
    ) -> list[Workout]:
        """Get workouts that need metadata extraction."""
        try:
            # Get workouts where metadata fields are null or empty
            query = self.repository.client.table("workouts").select("*")

            # Filter for workouts missing metadata
            query = query.or_(
                "movements.is.null,"
                "equipment.is.null,"
                "workout_type.is.null,"
                "movements.eq.[],"
                "equipment.eq.[]"
            )

            query = query.order("date", desc=False)  # Process oldest first

            if limit:
                query = query.limit(limit)
            if offset:
                query = query.offset(offset)

            result = query.execute()
            return [Workout.from_dict(row) for row in result.data]

        except APIError as e:
            logger.error(f"Failed to fetch workouts needing metadata: {e}")
            return []

    def extract_metadata_with_retry(self, workout_text: str) -> dict[str, Any] | None:
        """Extract metadata with retry logic."""
        for attempt in range(self.max_retries + 1):
            try:
                # Extract metadata using the dspy agent
                result = extractor(workout=workout_text)

                # Validate and clean the results
                metadata = {
                    'movements': self._validate_movements(result.movements),
                    'equipment': self._validate_equipment(result.equipment),
                    'workout_type': self._validate_workout_type(result.workout_type),
                    'workout_name': self._validate_workout_name(result.workout_name)
                }

                return metadata

            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                else:
                    logger.error(
                        f"Failed to extract metadata after "
                        f"{self.max_retries + 1} attempts"
                    )

        return None

    def _validate_movements(self, movements: list[str]) -> list[str]:
        """Validate and clean movements list."""
        if not isinstance(movements, list):
            return []

        # Clean and deduplicate
        cleaned = []
        for movement in movements:
            if isinstance(movement, str) and movement.strip():
                cleaned_movement = movement.strip().lower()
                if cleaned_movement not in cleaned:
                    cleaned.append(cleaned_movement)

        return cleaned[:20]  # Limit to 20 movements max

    def _validate_equipment(self, equipment: list[str]) -> list[str]:
        """Validate and clean equipment list."""
        if not isinstance(equipment, list):
            return []

        # Clean and deduplicate
        cleaned = []
        for item in equipment:
            if isinstance(item, str) and item.strip():
                cleaned_item = item.strip().lower()
                if cleaned_item not in cleaned:
                    cleaned.append(cleaned_item)

        return cleaned[:15]  # Limit to 15 equipment items max

    def _validate_workout_type(self, workout_type: str) -> str | None:
        """Validate workout type."""
        valid_types = {
            "metcon", "strength", "hero", "girl", "benchmark",
            "team", "endurance", "skill", "other"
        }

        if isinstance(workout_type, str) and workout_type.lower() in valid_types:
            return workout_type.lower()
        return None

    def _validate_workout_name(self, workout_name: str | None) -> str | None:
        """Validate workout name."""
        if isinstance(workout_name, str) and workout_name.strip():
            cleaned = workout_name.strip()
            # Limit length and clean up
            if len(cleaned) <= 100 and cleaned.lower() not in ["none", "n/a", "null"]:
                return cleaned
        return None

    def update_workout_metadata_batch(self, updates: list[dict[str, Any]]) -> int:
        """Update multiple workouts with metadata in a batch."""
        successful_updates = 0

        for update in updates:
            try:
                workout_id = update['id']
                metadata = update['metadata']

                result = self.repository.update_workout_metadata(
                    workout_id=workout_id,
                    movements=metadata.get('movements'),
                    equipment=metadata.get('equipment'),
                    workout_type=metadata.get('workout_type'),
                    workout_name=metadata.get('workout_name')
                )

                if result:
                    successful_updates += 1
                    logger.debug(f"Updated workout {workout_id}")
                else:
                    logger.warning(f"Failed to update workout {workout_id}")
                    self.stats['failed_updates'] = int(self.stats['failed_updates']) + 1

            except Exception as e:
                logger.error(
                    f"Error updating workout {update.get('id', 'unknown')}: {e}"
                )
                self.stats['failed_updates'] = int(self.stats['failed_updates']) + 1

        return successful_updates

    def process_batch(self, workouts: list[Workout]) -> None:
        """Process a batch of workouts."""
        logger.info(f"Processing batch of {len(workouts)} workouts")

        updates = []

        for workout in workouts:
            self.stats['total_processed'] = int(self.stats['total_processed']) + 1

            # Skip if no workout text
            if not workout.workout or not workout.workout.strip():
                logger.debug(f"Skipping workout {workout.id} - no workout text")
                self.stats['skipped_no_workout'] = (
                    int(self.stats['skipped_no_workout']) + 1
                )
                continue

            # Extract metadata
            metadata = self.extract_metadata_with_retry(workout.workout)

            if metadata:
                updates.append({
                    'id': workout.id,
                    'metadata': metadata
                })
                logger.debug(f"Extracted metadata for workout {workout.id}: {metadata}")
            else:
                logger.warning(f"Failed to extract metadata for workout {workout.id}")
                self.stats['failed_extractions'] = (
                    int(self.stats['failed_extractions']) + 1
                )

        # Update database in batch
        if updates:
            successful_updates = self.update_workout_metadata_batch(updates)
            self.stats['successful_updates'] = (
                int(self.stats['successful_updates']) + successful_updates
            )
            logger.info(
                f"Successfully updated {successful_updates}/{len(updates)} workouts"
            )

        # Add delay between batches to avoid rate limiting
        if self.delay_between_batches > 0:
            time.sleep(self.delay_between_batches)

    def print_progress(self) -> None:
        """Print current progress statistics."""
        start_time = self.stats['start_time']
        if isinstance(start_time, datetime):
            elapsed_time = datetime.now(UTC) - start_time
            total_processed = int(self.stats['total_processed'])
            rate = (
                total_processed / elapsed_time.total_seconds()
                if elapsed_time.total_seconds() > 0
                else 0
            )
            elapsed_str = str(elapsed_time)
        else:
            elapsed_str = "unknown"
            rate = 0.0

        logger.info(f"""
=== Progress Report ===
Total Processed: {self.stats['total_processed']}
Successful Updates: {self.stats['successful_updates']}
Failed Extractions: {self.stats['failed_extractions']}
Failed Updates: {self.stats['failed_updates']}
Skipped (No Workout): {self.stats['skipped_no_workout']}
Elapsed Time: {elapsed_str}
Processing Rate: {rate:.2f} workouts/second
=======================
        """)

    def run(
        self,
        limit: int | None = None,
        dry_run: bool = False,
        resume_from_offset: int = 0
    ) -> None:
        """Run the metadata extraction process."""
        logger.info(f"Starting metadata extraction {'(DRY RUN)' if dry_run else ''}")
        logger.info(
            f"Batch size: {self.batch_size}, Resume from offset: {resume_from_offset}"
        )

        if dry_run:
            logger.info("DRY RUN MODE - No database updates will be performed")

        offset = resume_from_offset
        processed_count = 0

        while True:
            # Get next batch of workouts
            workouts = self.get_workouts_needing_metadata(
                limit=self.batch_size,
                offset=offset
            )

            if not workouts:
                logger.info("No more workouts to process")
                break

            if not dry_run:
                self.process_batch(workouts)
            else:
                # Dry run - just extract metadata without updating
                for workout in workouts:
                    if workout.workout:
                        metadata = self.extract_metadata_with_retry(workout.workout)
                        logger.info(f"Workout {workout.id}: {metadata}")
                self.stats['total_processed'] = (
                    int(self.stats['total_processed']) + len(workouts)
                )

            processed_count += len(workouts)
            offset += len(workouts)

            # Print progress every 10 batches
            if processed_count % (self.batch_size * 10) == 0:
                self.print_progress()

            # Check if we've hit the limit
            if limit and processed_count >= limit:
                logger.info(f"Reached processing limit of {limit} workouts")
                break

        # Final progress report
        self.print_progress()
        logger.info("Metadata extraction completed!")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Extract and populate workout metadata"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Number of workouts to process in each batch"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of workouts to process"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between batches in seconds"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without updating the database"
    )
    parser.add_argument(
        "--resume-from-offset",
        type=int,
        default=0,
        help="Resume processing from this offset"
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum number of retries for failed extractions"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="openrouter/google/gemini-2.5-flash",
        help="LLM model to use for extraction"
    )

    args = parser.parse_args()

    # Configure dspy
    dspy.configure(lm=dspy.LM(args.model, max_tokens=100000))

    # Create and run extractor
    metadata_extractor = MetadataExtractor(
        batch_size=args.batch_size,
        delay_between_batches=args.delay,
        max_retries=args.max_retries
    )

    try:
        metadata_extractor.run(
            limit=args.limit,
            dry_run=args.dry_run,
            resume_from_offset=args.resume_from_offset
        )
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        metadata_extractor.print_progress()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        metadata_extractor.print_progress()
        raise


if __name__ == "__main__":
    main()

