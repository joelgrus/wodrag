import os
import pytest
from unittest.mock import patch, MagicMock
from wodrag.database.client import get_supabase_client, reset_client


class TestSupabaseClient:
    def setup_method(self) -> None:
        """Reset client before each test."""
        reset_client()

    def teardown_method(self) -> None:
        """Reset client after each test."""
        reset_client()

    @patch("wodrag.database.client.create_client")
    @patch.dict(os.environ, {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_ANON_KEY": "test-key"
    })
    def test_get_supabase_client_creates_client(self, mock_create_client: MagicMock) -> None:
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client
        
        client = get_supabase_client()
        
        mock_create_client.assert_called_once_with(
            "https://test.supabase.co",
            "test-key"
        )
        assert client == mock_client

    @patch("wodrag.database.client.create_client")
    @patch.dict(os.environ, {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_ANON_KEY": "test-key"
    })
    def test_get_supabase_client_returns_cached_client(self, mock_create_client: MagicMock) -> None:
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client
        
        # First call creates client
        client1 = get_supabase_client()
        # Second call returns cached client
        client2 = get_supabase_client()
        
        # Should only be called once
        mock_create_client.assert_called_once()
        assert client1 == client2

    @patch.dict(os.environ, {}, clear=True)
    def test_get_supabase_client_missing_url(self) -> None:
        os.environ["SUPABASE_ANON_KEY"] = "test-key"
        
        with pytest.raises(ValueError) as exc_info:
            get_supabase_client()
        
        assert "Missing Supabase credentials" in str(exc_info.value)

    @patch.dict(os.environ, {}, clear=True)
    def test_get_supabase_client_missing_key(self) -> None:
        os.environ["SUPABASE_URL"] = "https://test.supabase.co"
        
        with pytest.raises(ValueError) as exc_info:
            get_supabase_client()
        
        assert "Missing Supabase credentials" in str(exc_info.value)

    @patch.dict(os.environ, {}, clear=True)
    def test_get_supabase_client_missing_both(self) -> None:
        with pytest.raises(ValueError) as exc_info:
            get_supabase_client()
        
        assert "Missing Supabase credentials" in str(exc_info.value)

    @patch("wodrag.database.client.create_client")
    @patch.dict(os.environ, {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_ANON_KEY": "test-key"
    })
    def test_reset_client_clears_cache(self, mock_create_client: MagicMock) -> None:
        mock_client1 = MagicMock()
        mock_client2 = MagicMock()
        mock_create_client.side_effect = [mock_client1, mock_client2]
        
        # First call creates client
        client1 = get_supabase_client()
        assert client1 == mock_client1
        
        # Reset the client
        reset_client()
        
        # Next call creates new client
        client2 = get_supabase_client()
        assert client2 == mock_client2
        
        # Should be called twice
        assert mock_create_client.call_count == 2