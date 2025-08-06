from unittest.mock import MagicMock, patch

import pytest

from wodrag.services.embedding_service import EmbeddingService


class TestEmbeddingService:
    @patch("wodrag.services.embedding_service.openai.embeddings.create")
    @patch("wodrag.services.embedding_service.os.getenv")
    def test_initialization_success(
        self, mock_getenv: MagicMock, mock_create: MagicMock
    ) -> None:
        mock_getenv.return_value = "test-api-key"

        service = EmbeddingService()

        assert service.model == "text-embedding-3-small"
        # Check that OPENAI_API_KEY was called (among other calls from dependencies)
        mock_getenv.assert_any_call("OPENAI_API_KEY")

    @patch("wodrag.services.embedding_service.os.getenv")
    def test_initialization_no_api_key(self, mock_getenv: MagicMock) -> None:
        mock_getenv.return_value = None

        with pytest.raises(ValueError) as exc_info:
            EmbeddingService()

        assert "OPENAI_API_KEY environment variable is required" in str(exc_info.value)

    @patch("wodrag.services.embedding_service.openai.embeddings.create")
    @patch("wodrag.services.embedding_service.os.getenv")
    def test_generate_embedding_success(
        self, mock_getenv: MagicMock, mock_create: MagicMock
    ) -> None:
        mock_getenv.return_value = "test-api-key"
        mock_embedding = [0.1, 0.2, 0.3, 0.4]
        mock_create.return_value.data = [MagicMock(embedding=mock_embedding)]

        service = EmbeddingService()
        result = service.generate_embedding("test text")

        assert result == mock_embedding
        mock_create.assert_called_once_with(
            model="text-embedding-3-small", input="test text"
        )

    @patch("wodrag.services.embedding_service.openai.embeddings.create")
    @patch("wodrag.services.embedding_service.os.getenv")
    def test_generate_embedding_strips_whitespace(
        self, mock_getenv: MagicMock, mock_create: MagicMock
    ) -> None:
        mock_getenv.return_value = "test-api-key"
        mock_embedding = [0.1, 0.2, 0.3]
        mock_create.return_value.data = [MagicMock(embedding=mock_embedding)]

        service = EmbeddingService()
        service.generate_embedding("  test text  ")

        mock_create.assert_called_once_with(
            model="text-embedding-3-small", input="test text"
        )

    @patch("wodrag.services.embedding_service.os.getenv")
    def test_generate_embedding_empty_text(self, mock_getenv: MagicMock) -> None:
        mock_getenv.return_value = "test-api-key"

        service = EmbeddingService()

        with pytest.raises(ValueError) as exc_info:
            service.generate_embedding("")

        assert "Text cannot be empty" in str(exc_info.value)

    @patch("wodrag.services.embedding_service.openai.embeddings.create")
    @patch("wodrag.services.embedding_service.os.getenv")
    def test_generate_embedding_api_error(
        self, mock_getenv: MagicMock, mock_create: MagicMock
    ) -> None:
        mock_getenv.return_value = "test-api-key"
        mock_create.side_effect = Exception("API Error")

        service = EmbeddingService()

        with pytest.raises(RuntimeError) as exc_info:
            service.generate_embedding("test text")

        assert "Failed to generate embedding" in str(exc_info.value)

    @patch("wodrag.services.embedding_service.openai.embeddings.create")
    @patch("wodrag.services.embedding_service.os.getenv")
    def test_generate_batch_embeddings_success(
        self, mock_getenv: MagicMock, mock_create: MagicMock
    ) -> None:
        mock_getenv.return_value = "test-api-key"
        mock_embeddings = [
            MagicMock(embedding=[0.1, 0.2]),
            MagicMock(embedding=[0.3, 0.4]),
        ]
        mock_create.return_value.data = mock_embeddings

        service = EmbeddingService()
        texts = ["text 1", "text 2"]
        results = service.generate_batch_embeddings(texts)

        assert len(results) == 2
        assert results[0] == [0.1, 0.2]
        assert results[1] == [0.3, 0.4]
        mock_create.assert_called_once_with(
            model="text-embedding-3-small", input=["text 1", "text 2"]
        )

    @patch("wodrag.services.embedding_service.openai.embeddings.create")
    @patch("wodrag.services.embedding_service.os.getenv")
    def test_generate_batch_embeddings_with_empty_texts(
        self, mock_getenv: MagicMock, mock_create: MagicMock
    ) -> None:
        mock_getenv.return_value = "test-api-key"
        mock_embeddings = [MagicMock(embedding=[0.1, 0.2])]
        mock_create.return_value.data = mock_embeddings

        service = EmbeddingService()
        texts = ["", "text 2", "  "]
        results = service.generate_batch_embeddings(texts)

        assert len(results) == 3
        assert results[0] == []  # Empty for first text
        assert results[1] == [0.1, 0.2]  # Embedding for second text
        assert results[2] == []  # Empty for third text
        mock_create.assert_called_once_with(
            model="text-embedding-3-small", input=["text 2"]
        )

    @patch("wodrag.services.embedding_service.os.getenv")
    def test_generate_batch_embeddings_empty_list(self, mock_getenv: MagicMock) -> None:
        mock_getenv.return_value = "test-api-key"

        service = EmbeddingService()
        results = service.generate_batch_embeddings([])

        assert results == []

    @patch("wodrag.services.embedding_service.os.getenv")
    def test_generate_batch_embeddings_all_empty(self, mock_getenv: MagicMock) -> None:
        mock_getenv.return_value = "test-api-key"

        service = EmbeddingService()

        with pytest.raises(ValueError) as exc_info:
            service.generate_batch_embeddings(["", "  ", None])

        assert "All texts are empty" in str(exc_info.value)

    @patch("wodrag.services.embedding_service.openai.embeddings.create")
    @patch("wodrag.services.embedding_service.os.getenv")
    def test_generate_batch_embeddings_api_error(
        self, mock_getenv: MagicMock, mock_create: MagicMock
    ) -> None:
        mock_getenv.return_value = "test-api-key"
        mock_create.side_effect = Exception("Batch API Error")

        service = EmbeddingService()

        with pytest.raises(RuntimeError) as exc_info:
            service.generate_batch_embeddings(["text 1", "text 2"])

        assert "Failed to generate batch embeddings" in str(exc_info.value)

    @patch("wodrag.services.embedding_service.os.getenv")
    def test_custom_model(self, mock_getenv: MagicMock) -> None:
        mock_getenv.return_value = "test-api-key"

        service = EmbeddingService(model="text-embedding-ada-002")

        assert service.model == "text-embedding-ada-002"
