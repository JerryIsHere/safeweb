from src.url_intelligence import classify_url


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