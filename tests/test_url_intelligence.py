from src.url_intelligence import classify_url, detect_brand_impersonation


def test_classify_url_identifies_hosting_category_and_brand() -> None:
    result = classify_url("https://vietcombank-login.github.io/verify")

    assert result["category_id"] == "banking_finance"
    assert result["provider"] == "GitHub Pages"
    assert result["brand"] == "Vietcombank"


def test_classify_url_uses_dataset_brand_and_general_fallback() -> None:
    result = classify_url("https://notice.example/path", impersonated_brand="Shopee")

    assert result["category_id"] == "general"
    assert result["brand"] == "Shopee"
    assert result["provider"] == "Custom domain"


def test_brand_lookalikes_detect_typos_and_confusable_characters() -> None:
    for url, expected_brand in (
        ("https://faceboook.com", "Facebook"),
        ("https://gooogle.com", "Google"),
        ("https://vietc0mbank.com", "Vietcombank"),
        ("https://paypa1.com", "PayPal"),
        ("https://rnicrosoft.com", "Microsoft"),
    ):
        assert detect_brand_impersonation(url) == expected_brand


def test_brand_lookalikes_allow_official_hosts_and_unrelated_domains() -> None:
    for url in (
        "https://www.facebook.com",
        "https://www.vietcombank.com.vn",
        "https://www.divineskins.gg",
        "https://jerryishere.github.io/safeweb",
    ):
        assert detect_brand_impersonation(url) is None


def test_github_pages_hosting_suffix_is_not_a_github_lookalike() -> None:
    assert detect_brand_impersonation("https://jerryishere.github.io/safeweb") is None
    assert detect_brand_impersonation("https://vietcombank-login.github.io/verify") == "Vietcombank"


def test_classification_exposes_lookalike_brand_hint() -> None:
    assert classify_url("https://faceboook.com")["brand"] == "Facebook"