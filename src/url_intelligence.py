"""Deterministic category, hosting-provider, and brand hints for URLs."""

from __future__ import annotations

import re
from urllib.parse import urlsplit

import tldextract


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
    ("vietcombank", "Vietcombank", ("vietcombank.com.vn", "vietcombank.vn")),
    ("vietinbank", "VietinBank", ("vietinbank.vn", "vietinbank.com.vn")),
    ("bidv", "BIDV", ("bidv.com.vn", "bidv.vn")),
    ("vpbank", "VPBank", ("vpbank.com.vn", "vpbank.vn")),
    ("sacombank", "Sacombank", ("sacombank.com.vn", "sacombank.vn")),
    ("techcombank", "Techcombank", ("techcombank.com.vn", "techcombank.vn")),
    ("agribank", "Agribank", ("agribank.com.vn", "agribank.vn")),
    ("mbbank", "MB Bank", ("mbbank.com.vn", "mbbank.vn")),
    ("tpbank", "TPBank", ("tpb.vn", "tpbank.com.vn")),
    ("acb", "ACB", ("acb.com.vn", "acb.vn", "acb.com")),
    ("paypal", "PayPal", ("paypal.com", "paypalobjects.com")),
    ("microsoft", "Microsoft", ("microsoft.com", "microsoftonline.com")),
    ("facebook", "Facebook", ("facebook.com", "fb.com")),
    ("google", "Google", ("google.com", "google.vn")),
    ("instagram", "Instagram", ("instagram.com",)),
    ("whatsapp", "WhatsApp", ("whatsapp.com",)),
    ("shopee", "Shopee", ("shopee.vn", "shopee.com")),
    ("lazada", "Lazada", ("lazada.vn", "lazada.com")),
    ("tiki", "Tiki", ("tiki.vn",)),
    ("amazon", "Amazon", ("amazon.com",)),
    ("steam", "Steam", ("steampowered.com", "steamcommunity.com")),
    ("roblox", "Roblox", ("roblox.com",)),
    ("apple", "Apple", ("apple.com",)),
    ("github", "GitHub", ("github.com", "github.io")),
    ("garena", "Garena", ("garena.com", "garena.vn")),
    ("momo", "MoMo", ("momo.vn",)),
    ("zalo", "Zalo", ("zalo.me", "zalo.vn")),
    ("tiktok", "TikTok", ("tiktok.com",)),
)

_DOMAIN_PARSER = tldextract.TLDExtract(suffix_list_urls=())
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


def _normalized_brand_text(value: str) -> str:
    normalized = value.lower().replace("0", "o").replace("1", "l").replace("rn", "m")
    return re.sub(r"[^a-z0-9]", "", normalized)


def _edit_distance(left: str, right: str, limit: int) -> int:
    if abs(len(left) - len(right)) > limit:
        return limit + 1
    previous = list(range(len(right) + 1))
    for row, left_character in enumerate(left, start=1):
        current = [row]
        for column, right_character in enumerate(right, start=1):
            current.append(min(
                current[-1] + 1,
                previous[column] + 1,
                previous[column - 1] + (left_character != right_character),
            ))
        if min(current) > limit:
            return limit + 1
        previous = current
    return previous[-1]


def detect_brand_impersonation(url: str) -> str | None:
    """Return the likely copied brand when the registered domain is not official."""
    parts = urlsplit(url if "://" in url else f"https://{url}")
    hostname = (parts.hostname or "").lower().rstrip(".").removeprefix("www.")
    if not hostname:
        return None
    extracted = _DOMAIN_PARSER(hostname)
    registered_domain = extracted.top_domain_under_public_suffix or hostname
    label = _normalized_brand_text(extracted.domain or hostname)
    candidate_labels = [label]
    if hostname.endswith(".github.io"):
        candidate_labels.extend(
            _normalized_brand_text(token)
            for subdomain in hostname.removesuffix(".github.io").split(".")
            for token in re.split(r"[-_]", subdomain)
            if token
        )

    for brand, display_name, official_domains in _BRANDS:
        if registered_domain in official_domains:
            continue
        normalized_brand = _normalized_brand_text(brand)
        limit = 1 if len(normalized_brand) < 6 else 2
        if any(_edit_distance(candidate, normalized_brand, limit) <= limit for candidate in candidate_labels):
            return display_name
    return None


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
        brand = detect_brand_impersonation(url) or ""
    if not brand:
        brand = next(
            (name for token, name, _ in _BRANDS if token in hostname),
            "No known brand signature",
        )
    return {
        "category_id": category_id,
        "category": category,
        "provider": provider,
        "brand": brand,
    }