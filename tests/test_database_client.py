import os
from unittest.mock import MagicMock, patch

import pytest

from wodrag.database.client import get_postgres_connection


class TestPostgreSQLClient:
    @patch("wodrag.database.client.psycopg2.connect")
    @patch.dict(
        os.environ,
        {"DATABASE_URL": "postgresql://user:pass@localhost:5432/db"},
    )
    def test_get_postgres_connection_success(self, mock_connect: MagicMock) -> None:
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        with get_postgres_connection() as conn:
            assert conn == mock_conn

        mock_connect.assert_called_once_with("postgresql://user:pass@localhost:5432/db")
        mock_conn.close.assert_called_once()

    @patch.dict(os.environ, {}, clear=True)
    def test_get_postgres_connection_missing_url(self) -> None:
        with pytest.raises(ValueError) as exc_info, get_postgres_connection():
            pass

        assert "DATABASE_URL not found in environment" in str(exc_info.value)

    @patch("wodrag.database.client.psycopg2.connect")
    @patch.dict(
        os.environ,
        {"DATABASE_URL": "postgresql://user:pass@localhost:5432/db"},
    )
    def test_get_postgres_connection_closes_on_exception(
        self, mock_connect: MagicMock
    ) -> None:
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        with pytest.raises(RuntimeError), get_postgres_connection() as conn:
            assert conn == mock_conn
            raise RuntimeError("Test exception")

        mock_conn.close.assert_called_once()
