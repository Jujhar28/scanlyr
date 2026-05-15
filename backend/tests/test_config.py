"""Sanity check that test DB configuration resolves."""

from __future__ import annotations

import pytest


@pytest.mark.integration
def test_database_url_fixture(database_url: str) -> None:
    assert "postgresql" in database_url.lower()
