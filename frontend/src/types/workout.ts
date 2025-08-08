export interface Workout {
  id?: number;
  date?: string; // ISO date
  url?: string | null;
  raw_text?: string | null;
  workout?: string | null;
  scaling?: string | null;
  has_video?: boolean;
  has_article?: boolean;
  month_file?: string | null;
  created_at?: string | null;
  workout_search_vector?: string | null;
  workout_embedding?: number[] | null;
  movements?: string[];
  equipment?: string[];
  workout_type?: string | null;
  workout_name?: string | null;
  one_sentence_summary?: string | null;
  summary_embedding?: number[] | null;
}

export interface SearchResultModel {
  workout: Workout;
  similarity_score?: number | null;
  bm25_score?: number | null;
  hybrid_score?: number | null;
  metadata_match?: boolean;
}

export interface WorkoutWithSimilar {
  workout: Workout;
  similar: SearchResultModel[];
}
