"""Deterministic category, hosting-provider, and brand hints for URLs."""

from __future__ import annotations

from urllib.parse import urlsplit


_HOSTING_PROVIDERS = (
    ("github.io", "GitHub Pages"),
    ("appspot.com", "Google App Engine"),
    ("weebly.com", "Weebly"),
    ("blogspot.com", "Blogger / Blogspot"),
    ("wordpress.com", "WordPress.com"),
    ("wixsite.com", "Wix"),
    ("netlify.app", "Netlify"),
    ("vercel.app", "Vercel"),
    ("pages.dev", "Cloudflare Pages"),
    ("workers.dev", "Cloudflare Workers"),
    ("web.app", "Firebase Hosting"),
)

_BRANDS = (
    ("vietcombank", "Vietcombank"), ("vietinbank", "VietinBank"),
    ("bidv", "BIDV"), ("vpbank", "VPBank"), ("sacombank", "Sacombank"),
    ("techcombank", "Techcombank"), ("agribank", "Agribank"),
    ("mbbank", "MB Bank"), ("tpbank", "TPBank"), ("acb", "ACB"),
    ("paypal", "PayPal"), ("microsoft", "Microsoft"), ("facebook", "Facebook"),
    ("instagram", "Instagram"), ("whatsapp", "WhatsApp"),
    ("shopee", "Shopee"), ("lazada", "Lazada"), ("tiki", "Tiki"),
    ("amazon", "Amazon"), ("steam", "Steam"),
)

_CATEGORY_RULES = (
    ("gambling", "Cá cược / Cờ bạc / Gambling & Betting", ("casino", "gambling", "betting", "lottery", "slot", "kubet", "789bet", "bong88", "xoso", "lode")),
    ("gaming", "Trò chơi trực tuyến / Online Gaming", ("muonline", "volam", "volamtruyenky", "gunny", "sro", "game", "gaming", "steam")),
    ("crypto_wallet", "Ví điện tử & Tiền mã hóa / Crypto & E-Wallet", ("crypto", "bitcoin", "ethereum", "wallet", "metamask", "binance", "coinbase", "momo", "zalopay", "vnpay")),
    ("banking_finance", "Ngân hàng & Tài chính / Banking & Finance", ("bank", "banking", "vietcombank", "vietinbank", "bidv", "vpbank", "sacombank", "techcombank", "agribank", "mbbank", "tpbank", "acb", "paypal")),
    ("social_messaging", "Mạng xã hội & Nhắn tin / Social & Messaging", ("facebook", "instagram", "whatsapp", "zalo", "messenger", "tiktok", "telegram", "social")),
    ("e_commerce", "Thương mại điện tử / E-Commerce", ("shopee", "lazada", "tiki", "amazon", "ecommerce", "shopping", "checkout", "cart")),
    ("cloud_hosting", "Dịch vụ Đám mây & Lưu trữ / Cloud & Hosting", ("github", "appspot", "weebly", "blogspot", "wordpress", "netlify", "vercel", "cloudflare", "hosting", "drive", "dropbox")),
    ("news_media", "Tin tức & Giải trí / News & Media", ("news", "media", "youtube", "netflix", "spotify", "movie", "stream")),
    ("url_shortener", "Công cụ Rút gọn Link / URL Shortener", ("bit.ly", "tinyurl", "t.co", "shorturl", "url-short")),
)


def classify_url(
    url: str,
    *,
    scenario: str = "",
    impersonated_brand: str = "",
) -> dict[str, str]:
    """Return a rule-based category and recognizable platform/brand hints."""
    parts = urlsplit(url if "://" in url else f"https://{url}")
    hostname = (parts.hostname or "").lower().rstrip(".")
    searchable = f"{hostname} {parts.path} {parts.query}".lower()
    category_id = "general"
    category = "Trang Web Tổng hợp / General Website"
    for candidate, label, terms in _CATEGORY_RULES:
        if any(term in searchable for term in terms):
            category_id, category = candidate, label
            break
    if category_id == "general" and scenario:
        scenario_text = scenario.lower().replace("_", " ")
        for candidate, label, terms in _CATEGORY_RULES:
            if any(term in scenario_text for term in terms):
                category_id, category = candidate, label
                break

    provider = next(
        (name for suffix, name in _HOSTING_PROVIDERS if hostname == suffix or hostname.endswith(f".{suffix}")),
        "Custom domain",
    )
    brand = impersonated_brand.strip()
    if not brand:
        brand = next(
            (name for token, name in _BRANDS if token in hostname),
            "No known brand signature",
        )
    return {
        "category_id": category_id,
        "category": category,
        "provider": provider,
        "brand": brand,
    }