import pytest


@pytest.mark.django_db
class TestLocalization:
    """Test that locale selection via Django's LANGUAGES setting and Fluent translations work correctly."""

    @pytest.mark.parametrize(
        ("accept_language", "expected_language", "expected_nav"),
        [
            (None, "en-us", ["Leagues", "Events"]),
            ("en-us", "en-us", ["Leagues", "Events"]),
            ("en", "en-us", ["Leagues", "Events"]),
            ("es", "es", ["Ligas", "Eventos"]),
        ],
        ids=["default", "explicit-en-us", "bare-en", "spanish"],
    )
    def test_supported_language(
        self, client, accept_language, expected_language, expected_nav
    ):
        headers = {"Accept-Language": accept_language} if accept_language else {}
        response = client.get("/", headers=headers)
        content = response.content.decode()

        assert response["Content-Language"] == expected_language
        assert f'lang="{expected_language}"' in content
        for term in expected_nav:
            assert term in content

    @pytest.mark.parametrize(
        "accept_language",
        ["fr", "de", "ja"],
        ids=["french", "german", "japanese"],
    )
    def test_unsupported_language_falls_back_to_english(self, client, accept_language):
        """Unsupported language should resolve to en-us at the Django level,
        verified via the Content-Language header."""
        response = client.get("/", headers={"Accept-Language": accept_language})
        content = response.content.decode()

        assert response["Content-Language"] == "en-us"
        assert "Leagues" in content
        assert "Events" in content
