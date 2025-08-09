from __future__ import annotations

import os

import openai
from openai import OpenAI


class EmbeddingService:
    """Service for generating text embeddings using OpenAI."""

    def __init__(self, model: str = "text-embedding-3-small"):
        """
        Initialize the embedding service.

        Args:
            model: OpenAI embedding model to use
        """
        self.model = model
        # Initialize OpenAI client with API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = OpenAI(api_key=api_key)

    def generate_embedding(self, text: str) -> list[float]:
        """
        Generate an embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector

        Raises:
            RuntimeError: If embedding generation fails
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        try:
            response = self.client.embeddings.create(
                model=self.model, input=text.strip()
            )
            return response.data[0].embedding
        except (openai.OpenAIError, ValueError) as e:
            raise RuntimeError(f"Failed to generate embedding: {e}") from e

    def generate_batch_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts in a single API call.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors in the same order as input texts

        Raises:
            RuntimeError: If embedding generation fails
        """
        if not texts:
            return []

        # Filter out empty texts and keep track of indices
        non_empty_texts = []
        text_indices = []

        for i, text in enumerate(texts):
            if text and text.strip():
                non_empty_texts.append(text.strip())
                text_indices.append(i)

        if not non_empty_texts:
            raise ValueError("All texts are empty")

        try:
            response = self.client.embeddings.create(
                model=self.model, input=non_empty_texts
            )

            # Create result list with same length as input
            embeddings: list[list[float]] = [[] for _ in texts]

            # Fill in embeddings for non-empty texts
            for i, embedding_data in enumerate(response.data):
                original_index = text_indices[i]
                embeddings[original_index] = embedding_data.embedding

            return embeddings

        except (openai.OpenAIError, ValueError) as e:
            raise RuntimeError(f"Failed to generate batch embeddings: {e}") from e
