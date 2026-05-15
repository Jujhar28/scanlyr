"""Tests for app.core.openapi_metadata — static OpenAPI tag definitions."""
from __future__ import annotations

import pytest

from app.core.openapi_metadata import API_DESCRIPTION, API_VERSION, OPENAPI_TAGS

# ---------------------------------------------------------------------------
# OPENAPI_TAGS structure
# ---------------------------------------------------------------------------

EXPECTED_TAG_NAMES = {
    "health",
    "auth",
    "detections",
    "reports",
    "integrations-microsoft",
    "admin",
}


class TestOpenApiTags:
    def test_openapi_tags_is_a_list(self) -> None:
        assert isinstance(OPENAPI_TAGS, list)

    def test_openapi_tags_is_not_empty(self) -> None:
        assert len(OPENAPI_TAGS) > 0

    def test_each_tag_is_a_dict(self) -> None:
        for tag in OPENAPI_TAGS:
            assert isinstance(tag, dict), f"Expected dict, got {type(tag)}"

    def test_each_tag_has_name_key(self) -> None:
        for tag in OPENAPI_TAGS:
            assert "name" in tag, f"Tag missing 'name': {tag}"

    def test_each_tag_has_description_key(self) -> None:
        for tag in OPENAPI_TAGS:
            assert "description" in tag, f"Tag missing 'description': {tag}"

    def test_tag_name_values_are_strings(self) -> None:
        for tag in OPENAPI_TAGS:
            assert isinstance(tag["name"], str)

    def test_tag_description_values_are_non_empty_strings(self) -> None:
        for tag in OPENAPI_TAGS:
            assert isinstance(tag["description"], str)
            assert len(tag["description"]) > 0

    def test_all_expected_tags_present(self) -> None:
        actual_names = {t["name"] for t in OPENAPI_TAGS}
        assert EXPECTED_TAG_NAMES.issubset(actual_names), (
            f"Missing tags: {EXPECTED_TAG_NAMES - actual_names}"
        )

    def test_tag_names_are_unique(self) -> None:
        names = [t["name"] for t in OPENAPI_TAGS]
        assert len(names) == len(set(names)), "Duplicate tag names found"

    def test_health_tag_present(self) -> None:
        names = {t["name"] for t in OPENAPI_TAGS}
        assert "health" in names

    def test_auth_tag_present(self) -> None:
        names = {t["name"] for t in OPENAPI_TAGS}
        assert "auth" in names

    def test_admin_tag_present(self) -> None:
        names = {t["name"] for t in OPENAPI_TAGS}
        assert "admin" in names

    def test_integrations_microsoft_tag_present(self) -> None:
        names = {t["name"] for t in OPENAPI_TAGS}
        assert "integrations-microsoft" in names

    @pytest.mark.parametrize("tag_name", list(EXPECTED_TAG_NAMES))
    def test_each_expected_tag_has_nonempty_description(self, tag_name: str) -> None:
        tag = next((t for t in OPENAPI_TAGS if t["name"] == tag_name), None)
        assert tag is not None
        assert len(tag["description"].strip()) > 0

    def test_openapi_tags_count(self) -> None:
        assert len(OPENAPI_TAGS) == 6

    def test_tag_dicts_have_only_name_and_description(self) -> None:
        for tag in OPENAPI_TAGS:
            extra_keys = set(tag.keys()) - {"name", "description"}
            assert extra_keys == set(), f"Unexpected extra keys in tag {tag['name']}: {extra_keys}"


# ---------------------------------------------------------------------------
# API_DESCRIPTION
# ---------------------------------------------------------------------------


class TestApiDescription:
    def test_api_description_is_string(self) -> None:
        assert isinstance(API_DESCRIPTION, str)

    def test_api_description_is_not_empty(self) -> None:
        assert len(API_DESCRIPTION.strip()) > 0

    def test_api_description_mentions_scanlyr(self) -> None:
        assert "Scanlyr" in API_DESCRIPTION

    def test_api_description_mentions_bearer(self) -> None:
        assert "Bearer" in API_DESCRIPTION

    def test_api_description_mentions_auth(self) -> None:
        assert "auth" in API_DESCRIPTION.lower()

    def test_api_description_mentions_api_v1(self) -> None:
        assert "/api/v1" in API_DESCRIPTION

    def test_api_description_mentions_health_endpoint(self) -> None:
        assert "/api/v1/health" in API_DESCRIPTION


# ---------------------------------------------------------------------------
# API_VERSION
# ---------------------------------------------------------------------------


class TestApiVersion:
    def test_api_version_is_string(self) -> None:
        assert isinstance(API_VERSION, str)

    def test_api_version_is_not_empty(self) -> None:
        assert len(API_VERSION) > 0

    def test_api_version_follows_semver_pattern(self) -> None:
        import re
        semver_re = re.compile(r"^\d+\.\d+\.\d+$")
        assert semver_re.match(API_VERSION), f"'{API_VERSION}' is not a semver string"

    def test_api_version_is_1_0_0(self) -> None:
        assert API_VERSION == "1.0.0"