(function (root) {
  "use strict";

  const model = root.safewebModel;
  let phishvnRecords = [];
  let recordsByUrl = new Map();
  let recordsByHost = new Map();
  const keywords = ["login", "signin", "verify", "account", "password", "bank", "payment", "confirm"];
  const rules = new Set(model?.publicSuffixRules || []);
  const lettersOrNumbers = /^[\p{L}\p{N}]$/u;
  const letters = /^\p{L}$/u;
  const whitespace = /[\s\u0085]/u;
  const defaultThresholds = { low: 0.25, medium: 0.5, high: 0.75 };
  const phishvnFeatureNames = [
    "phishvn_url_len", "phishvn_dom_len", "phishvn_is_ip", "phishvn_tld_len",
    "phishvn_subdom_cnt", "phishvn_letter_cnt", "phishvn_digit_cnt", "phishvn_special_cnt",
    "phishvn_eq_cnt", "phishvn_qm_cnt", "phishvn_amp_cnt", "phishvn_dot_cnt",
    "phishvn_dash_cnt", "phishvn_under_cnt", "phishvn_letter_ratio", "phishvn_digit_ratio",
    "phishvn_spec_ratio", "phishvn_slash_cnt", "phishvn_entropy", "phishvn_path_len",
    "phishvn_query_len", "phishvn_suspicious_tld",
  ];
  const providers = [
    ["github.io", "GitHub Pages"], ["appspot.com", "Google App Engine"],
    ["weebly.com", "Weebly"], ["blogspot.com", "Blogger / Blogspot"],
    ["wordpress.com", "WordPress.com"], ["wixsite.com", "Wix"],
    ["netlify.app", "Netlify"], ["vercel.app", "Vercel"],
    ["pages.dev", "Cloudflare Pages"], ["workers.dev", "Cloudflare Workers"],
    ["web.app", "Firebase Hosting"],
  ];
  const brandRules = [
    ["vietcombank", "Vietcombank", ["vietcombank.com.vn", "vietcombank.vn"]],
    ["vietinbank", "VietinBank", ["vietinbank.vn", "vietinbank.com.vn"]],
    ["bidv", "BIDV", ["bidv.com.vn", "bidv.vn"]],
    ["vpbank", "VPBank", ["vpbank.com.vn", "vpbank.vn"]],
    ["sacombank", "Sacombank", ["sacombank.com.vn", "sacombank.vn"]],
    ["techcombank", "Techcombank", ["techcombank.com.vn", "techcombank.vn"]],
    ["agribank", "Agribank", ["agribank.com.vn", "agribank.vn"]],
    ["mbbank", "MB Bank", ["mbbank.com.vn", "mbbank.vn"]],
    ["tpbank", "TPBank", ["tpb.vn", "tpbank.com.vn"]],
    ["acb", "ACB", ["acb.com.vn", "acb.vn", "acb.com"]],
    ["paypal", "PayPal", ["paypal.com", "paypalobjects.com"]],
    ["microsoft", "Microsoft", ["microsoft.com", "microsoftonline.com"]],
    ["facebook", "Facebook", ["facebook.com", "fb.com"]],
    ["google", "Google", ["google.com", "google.vn"]],
    ["instagram", "Instagram", ["instagram.com"]],
    ["whatsapp", "WhatsApp", ["whatsapp.com"]],
    ["shopee", "Shopee", ["shopee.vn", "shopee.com"]],
    ["lazada", "Lazada", ["lazada.vn", "lazada.com"]],
    ["tiki", "Tiki", ["tiki.vn"]],
    ["amazon", "Amazon", ["amazon.com"]],
    ["steam", "Steam", ["steampowered.com", "steamcommunity.com"]],
    ["roblox", "Roblox", ["roblox.com"]],
    ["apple", "Apple", ["apple.com"]],
    ["github", "GitHub", ["github.com", "github.io"]],
    ["garena", "Garena", ["garena.com", "garena.vn"]],
    ["momo", "MoMo", ["momo.vn"]],
    ["zalo", "Zalo", ["zalo.me", "zalo.vn"]],
    ["tiktok", "TikTok", ["tiktok.com"]],
  ];
  const categoryRules = [
    ["gambling", "Cá cược / Cờ bạc / Gambling & Betting", ["casino", "gambling", "betting", "lottery", "slot", "kubet", "789bet", "bong88", "xoso", "lode"]],
    ["gaming", "Trò chơi trực tuyến / Online Gaming", ["muonline", "volam", "volamtruyenky", "gunny", "sro", "game", "gaming", "steam"]],
    ["crypto_wallet", "Ví điện tử & Tiền mã hóa / Crypto & E-Wallet", ["crypto", "bitcoin", "ethereum", "wallet", "metamask", "binance", "coinbase", "momo", "zalopay", "vnpay"]],
    ["banking_finance", "Ngân hàng & Tài chính / Banking & Finance", ["bank", "banking", "vietcombank", "vietinbank", "bidv", "vpbank", "sacombank", "techcombank", "agribank", "mbbank", "tpbank", "acb", "paypal"]],
    ["social_messaging", "Mạng xã hội & Nhắn tin / Social & Messaging", ["facebook", "instagram", "whatsapp", "zalo", "messenger", "tiktok", "telegram", "social"]],
    ["e_commerce", "Thương mại điện tử / E-Commerce", ["shopee", "lazada", "tiki", "amazon", "ecommerce", "shopping", "checkout", "cart"]],
    ["cloud_hosting", "Dịch vụ Đám mây & Lưu trữ / Cloud & Hosting", ["github", "appspot", "weebly", "blogspot", "wordpress", "netlify", "vercel", "cloudflare", "hosting", "drive", "dropbox"]],
    ["news_media", "Tin tức & Giải trí / News & Media", ["news", "media", "youtube", "netflix", "spotify", "movie", "stream"]],
    ["url_shortener", "Công cụ Rút gọn Link / URL Shortener", ["bit.ly", "tinyurl", "t.co", "shorturl", "url-short"]],
  ];

  function clamp(value, minimum, maximum) {
    return Math.min(Math.max(value, minimum), maximum);
  }

  function pythonLength(value) {
    return Array.from(value).length;
  }

  function entropy(value) {
    const characters = Array.from(value);
    if (!characters.length) return 0;
    const counts = new Map();
    characters.forEach((character) => counts.set(character, (counts.get(character) || 0) + 1));
    let result = 0;
    counts.forEach((count) => {
      const frequency = count / characters.length;
      result -= frequency * Math.log2(frequency);
    });
    return result;
  }

  function parseParts(value) {
    const match = /^([a-z][a-z0-9+.-]*):\/\//i.exec(value);
    if (!match) return { scheme: "", hostname: "", path: "", query: "" };
    const authorityStart = match[0].length;
    const suffixOffset = value.slice(authorityStart).search(/[/?#]/);
    const authorityEnd = suffixOffset < 0 ? value.length : authorityStart + suffixOffset;
    const authority = value.slice(authorityStart, authorityEnd);
    const hostPort = authority.slice(authority.lastIndexOf("@") + 1);
    let hostname = hostPort;
    if (hostPort.startsWith("[")) {
      const close = hostPort.indexOf("]");
      hostname = close < 0 ? "" : hostPort.slice(1, close);
    } else if (hostPort.includes(":")) {
      hostname = hostPort.slice(0, hostPort.lastIndexOf(":"));
    }

    const fragmentIndex = value.indexOf("#", authorityEnd);
    const queryIndex = value.indexOf("?", authorityEnd);
    const hasQuery = queryIndex >= 0 && (fragmentIndex < 0 || queryIndex < fragmentIndex);
    const pathEnd = [queryIndex, fragmentIndex]
      .filter((index) => index >= 0)
      .reduce((end, index) => Math.min(end, index), value.length);
    const path = value[authorityEnd] === "/" ? value.slice(authorityEnd, pathEnd) : "";
    const query = hasQuery
      ? value.slice(queryIndex + 1, fragmentIndex < 0 ? value.length : fragmentIndex)
      : "";

    return {
      scheme: match[1].toLowerCase(),
      hostname: hostname.toLowerCase().replace(/\.+$/, ""),
      path,
      query,
    };
  }

  function validateUrl(value) {
    if (typeof value !== "string" || !value.trim()) {
      throw new TypeError("A non-empty URL string is required.");
    }
    let healed = value.trim();
    if (Array.from(healed).some((character) => whitespace.test(character))) {
      throw new TypeError("The URL must not contain whitespace.");
    }
    if (healed.startsWith("//")) healed = `https:${healed}`;
    else if (!healed.includes("://")) {
      const host = healed.split(/[/?#]/u, 1)[0];
      if (!host.includes(".") && host.toLowerCase() !== "localhost") {
        healed = `${host}.com${healed.slice(host.length)}`;
      }
      healed = `https://${healed}`;
    }
    let parsed;
    try {
      parsed = new URL(healed);
    } catch {
      throw new TypeError("The URL is malformed.");
    }
    if (!["http:", "https:"].includes(parsed.protocol) || !parsed.hostname) {
      throw new TypeError("Enter a complete HTTP or HTTPS URL with a hostname.");
    }
    const parts = parseParts(healed);
    if (!parts.hostname || ["http", "https"].includes(parts.hostname)) {
      throw new TypeError("Enter a complete HTTP or HTTPS URL with a hostname.");
    }
    const hostname = parts.hostname.toLowerCase().replace(/\.+$/u, "");
    const authorityHost = hostname.includes(":") ? `[${hostname}]` : hostname;
    const credentials = parsed.username
      ? `${parsed.username}${parsed.password ? `:${parsed.password}` : ""}@`
      : "";
    const port = parsed.port ? `:${parsed.port}` : "";
    const path = parts.path.replace(/\/+$/u, "");
    return `${parsed.protocol.toLowerCase()}//${credentials}${authorityHost}${port}${path}${parsed.search}${parsed.hash}`;
  }

  function classifyUrl(value, impersonatedBrand = "") {
    const parts = parseParts(value);
    const hostname = parts.hostname.toLowerCase();
    const searchable = `${hostname} ${parts.path} ${parts.query}`.toLowerCase();
    const match = categoryRules.find(([, , terms]) => terms.some((term) => searchable.includes(term)));
    const category = match || ["general", "Trang Web Tổng hợp / General Website"];
    const provider = providers.find(([suffix]) => hostname === suffix || hostname.endsWith(`.${suffix}`));
    const brand = (impersonatedBrand && impersonatedBrand !== "No known brand signature")
      || detectBrandImpersonation(hostname)
      || brandRules.find(([token]) => hostname.includes(token))?.[1]
      || "No known brand signature";
    return {
      category_id: category[0],
      category: category[1],
      provider: provider?.[1] || "Custom domain",
      brand,
    };
  }

  function setDatabaseRecords(records) {
    phishvnRecords = Array.isArray(records) ? records : [];
    recordsByUrl = new Map(phishvnRecords.map((record) => [record.url_key, record]));
    recordsByHost = new Map();
    phishvnRecords.forEach((record) => {
      const host = record.url_key.split(/[/?]/u, 1)[0];
      if (!recordsByHost.has(host) || record.label === "Phishing") recordsByHost.set(host, record);
    });
  }

  function getPhishingExamples(value, limit = 5) {
    let targetHost;
    try {
      targetHost = new URL(validateUrl(value)).hostname.toLowerCase().replace(/^www\./u, "");
    } catch {
      return [];
    }

    const similarity = (left, right) => {
      const previous = Array.from({ length: right.length + 1 }, (_, index) => index);
      for (let row = 1; row <= left.length; row += 1) {
        let diagonal = previous[0];
        previous[0] = row;
        for (let column = 1; column <= right.length; column += 1) {
          const above = previous[column];
          previous[column] = Math.min(
            previous[column] + 1,
            previous[column - 1] + 1,
            diagonal + (left[row - 1] === right[column - 1] ? 0 : 1),
          );
          diagonal = above;
        }
      }
      return 1 - previous[right.length] / Math.max(left.length, right.length, 1);
    };

    return phishvnRecords
      .filter((record) => record.label === "Phishing"
        && record.detected_at
        && ["gold", "silver"].includes(String(record.tier).toLowerCase()))
      .map((record) => {
        try {
          const host = new URL(record.url).hostname.toLowerCase().replace(/^www\./u, "");
          return { ...record, similarity: similarity(targetHost, host) };
        } catch {
          return null;
        }
      })
      .filter((record) => record && record.similarity >= 0.8)
      .sort((left, right) => right.similarity - left.similarity)
      .slice(0, limit);
  }

  function isSafeWebUrl(value) {
    const parts = parseParts(value);
    return parts.hostname.toLowerCase() === "jerryishere.github.io"
      && parts.path.replace(/\/+$/u, "").toLowerCase() === "/safeweb";
  }

  function isIp(hostname) {
    if (!hostname) return false;
    const ipv4 = hostname.split(".");
    if (
      ipv4.length === 4
      && ipv4.every((part) => /^\d{1,3}$/.test(part) && (part === "0" || !part.startsWith("0")) && Number(part) <= 255)
    ) return true;
    if (!hostname.includes(":")) return false;
    try {
      return new URL(`http://[${hostname}]/`).hostname.startsWith("[");
    } catch {
      return false;
    }
  }

  function publicSuffixLength(hostname) {
    const labels = hostname.split(".").filter(Boolean);
    if (!labels.length) return 0;
    let bestLength = 1;
    for (let start = 0; start < labels.length; start += 1) {
      const tail = labels.slice(start).join(".");
      if (rules.has(`!${tail}`)) return Math.max(1, labels.length - start - 1);
      if (rules.has(tail)) bestLength = Math.max(bestLength, labels.length - start);
      if (start < labels.length - 1) {
        const wildcardSuffix = labels.slice(start + 1).join(".");
        if (rules.has(`*.${wildcardSuffix}`)) {
          bestLength = Math.max(bestLength, labels.length - start);
        }
      }
    }
    return Math.min(bestLength, labels.length);
  }

  function subdomainCount(hostname, ipAddress) {
    if (!hostname || ipAddress) return 0;
    let asciiHostname = hostname;
    try {
      asciiHostname = new URL(`http://${hostname}/`).hostname.toLowerCase().replace(/\.+$/, "");
    } catch {
      // Keep the parsed hostname; tldextract also accepts malformed label text.
    }
    const labels = asciiHostname.split(".").filter(Boolean);
    if (!labels.length) return 0;
    return Math.max(0, labels.length - publicSuffixLength(asciiHostname) - 1);
  }

  function normalizeBrandText(value) {
    return value.toLowerCase()
      .replaceAll("0", "o")
      .replaceAll("1", "l")
      .replaceAll("rn", "m")
      .replace(/[^a-z0-9]/g, "");
  }

  function editDistance(left, right, limit) {
    if (Math.abs(left.length - right.length) > limit) return limit + 1;
    let previous = Array.from({ length: right.length + 1 }, (_, index) => index);
    for (let row = 1; row <= left.length; row += 1) {
      const current = [row];
      for (let column = 1; column <= right.length; column += 1) {
        current.push(Math.min(
          current.at(-1) + 1,
          previous[column] + 1,
          previous[column - 1] + Number(left[row - 1] !== right[column - 1]),
        ));
      }
      if (Math.min(...current) > limit) return limit + 1;
      previous = current;
    }
    return previous.at(-1);
  }

  function detectBrandImpersonation(hostname) {
    const cleanHostname = hostname.toLowerCase().replace(/^www\./u, "").replace(/\.+$/u, "");
    const labels = cleanHostname.split(".").filter(Boolean);
    const suffixLength = publicSuffixLength(cleanHostname);
    if (!labels.length || suffixLength === 0) return null;
    const registrableDomain = labels.slice(-Math.min(labels.length, suffixLength + 1)).join(".");
    const registrableLabel = normalizeBrandText(labels.at(-suffixLength - 1) || "");
    const candidateLabels = [registrableLabel];
    if (cleanHostname.endsWith(".github.io")) {
      candidateLabels.push(
        ...labels.slice(0, -2)
          .flatMap((subdomain) => subdomain.split(/[-_]/u))
          .filter(Boolean)
          .map(normalizeBrandText),
      );
    }

    for (const [token, displayName, officialDomains] of brandRules) {
      if (officialDomains.includes(registrableDomain)) continue;
      const normalizedToken = normalizeBrandText(token);
      const limit = normalizedToken.length < 6 ? 1 : 2;
      if (candidateLabels.some((candidate) => editDistance(candidate, normalizedToken, limit) <= limit)) {
        return displayName;
      }
    }
    return null;
  }

  function repeatedQueryKeys(value) {
    const query = parseParts(value).query;
    if (!query) return 0;
    const keys = query.split("&").filter(Boolean).map((part) => {
      const equalsIndex = part.indexOf("=");
      return equalsIndex >= 0 ? part.slice(0, equalsIndex) : part;
    });
    return keys.reduce((count, key) => count + (keys.filter((entry) => entry === key).length > 1 ? 1 : 0), 0);
  }

  function extractFeatures(value, includeExperimental = false) {
    if (typeof value !== "string") throw new TypeError("url must be a string");
    if (!value.trim()) throw new TypeError("url must not be empty");
    value = value.replace(/^([a-z][a-z0-9+.-]*:\/\/)([^/?#]*@)?www\./iu, "$1$2");
    const parts = parseParts(value);
    const hostname = parts.hostname;
    const lowered = value.toLowerCase();
    const characters = Array.from(value);
    const features = {
      url_length: characters.length,
      domain_length: pythonLength(hostname),
      path_length: pythonLength(parts.path),
      query_length: pythonLength(parts.query),
      num_dots: value.split(".").length - 1,
      num_slashes: value.split("/").length - 1,
      num_hyphens: value.split("-").length - 1,
      num_underscores: value.split("_").length - 1,
      num_digits: characters.filter((character) => /^\p{N}$/u.test(character)).length,
      num_letters: characters.filter((character) => letters.test(character)).length,
      num_special_chars: characters.filter((character) => !lettersOrNumbers.test(character)).length,
      has_https: Number(parts.scheme === "https"),
      has_ip: Number(isIp(hostname)),
      num_subdomains: subdomainCount(hostname, isIp(hostname)),
      has_at: Number(value.includes("@")),
      has_question_mark: Number(value.includes("?")),
      has_equals: Number(value.includes("=")),
      has_percent: Number(value.includes("%")),
      has_double_slash: Number(value.split("://").slice(1).join("://").includes("//")),
      has_query: Number(Boolean(parts.query)),
      url_entropy: entropy(value),
      domain_entropy: entropy(hostname),
    };
    keywords.forEach((keyword) => {
      features[`keyword_${keyword}`] = Number(lowered.includes(keyword));
    });

    const phishvnDatabase = model?.phishvnDatabase || {};
    const profileValues = phishvnDatabase.hostProfiles?.[hostname];
    const profileFields = phishvnDatabase.hostProfileFields || [];
    const profile = profileValues
      ? Object.fromEntries(profileFields.map((name, index) => [name, profileValues[index]]))
      : {};
    const labels = hostname.split(".").filter(Boolean);
    const ipAddress = isIp(hostname);
    const suffixLength = ipAddress ? 0 : publicSuffixLength(hostname);
    const registrableLength = ipAddress ? labels.length : Math.min(labels.length, suffixLength + 1);
    const registrable = labels.slice(-registrableLength).join(".");
    const tld = ipAddress ? "" : labels.slice(-Math.min(labels.length, suffixLength)).join(".");
    const schemeStripped = value.replace(/^https?:\/\//iu, "");
    const schemeCharacters = Array.from(schemeStripped);
    const schemeLetters = schemeCharacters.filter((character) => letters.test(character)).length;
    const schemeDigits = schemeCharacters.filter((character) => /^\p{N}$/u.test(character)).length;
    const schemeLength = schemeCharacters.length;
    const sourceFeatureValues = {
      phishvn_url_len: schemeLength,
      phishvn_dom_len: pythonLength(registrable),
      phishvn_is_ip: Number(isIp(hostname)),
      phishvn_tld_len: pythonLength(tld),
      phishvn_subdom_cnt: subdomainCount(hostname, isIp(hostname)),
      phishvn_letter_cnt: schemeLetters,
      phishvn_digit_cnt: schemeDigits,
      phishvn_special_cnt: schemeLength - schemeLetters - schemeDigits,
      phishvn_eq_cnt: schemeStripped.split("=").length - 1,
      phishvn_qm_cnt: schemeStripped.split("?").length - 1,
      phishvn_amp_cnt: schemeStripped.split("&").length - 1,
      phishvn_dot_cnt: schemeStripped.split(".").length - 1,
      phishvn_dash_cnt: schemeStripped.split("-").length - 1,
      phishvn_under_cnt: schemeStripped.split("_").length - 1,
      phishvn_letter_ratio: schemeLetters / Math.max(1, schemeLength),
      phishvn_digit_ratio: schemeDigits / Math.max(1, schemeLength),
      phishvn_spec_ratio: (schemeLength - schemeLetters - schemeDigits) / Math.max(1, schemeLength),
      phishvn_slash_cnt: schemeStripped.split("/").length - 1,
      phishvn_entropy: entropy(schemeStripped),
      phishvn_path_len: pythonLength(parts.path.replace(/^\/+|\/+$/gu, "")),
      phishvn_query_len: pythonLength(parts.query),
      phishvn_suspicious_tld: 0,
    };
    phishvnFeatureNames.forEach((name) => {
      features[name] = name === "phishvn_suspicious_tld"
        ? 0
        : ["phishvn_dot_cnt", "phishvn_subdom_cnt"].includes(name)
          ? sourceFeatureValues[name]
          : profile[name] ?? sourceFeatureValues[name];
    });
    const encodedCharacterCount = 3 * (value.match(/%[0-9A-Fa-f]{2}/g) || []).length;
    features.phiusiil_has_obfuscation = Number(encodedCharacterCount > 0);
    features.phiusiil_obfuscated_char_count = encodedCharacterCount;
    features.phiusiil_obfuscation_ratio = encodedCharacterCount / Math.max(1, characters.length);

    if (!includeExperimental) return features;

    features.digit_to_letter_ratio = characters.filter((character) => /^\p{N}$/u.test(character)).length / Math.max(1, characters.filter((character) => letters.test(character)).length);
    features.digit_ratio = characters.filter((character) => /^\p{N}$/u.test(character)).length / Math.max(1, characters.length);
    features.special_char_ratio = characters.filter((character) => !lettersOrNumbers.test(character)).length / Math.max(1, characters.length);
    features.query_parameter_count = (parts.query ? parts.query.split("&").filter(Boolean) : []).length;
    features.hostname_depth = hostname ? hostname.split(".").filter(Boolean).length : 0;
    features.has_punycode_or_idn = Number(/xn--|[^\u0000-\u007F]/u.test(hostname));
    features.percent_encoding_count = (value.match(/%[0-9A-Fa-f]{2}/g) || []).length;
    features.has_repeated_characters = Number(/[A-Za-z0-9]([A-Za-z0-9])\1/.test(value));
    features.has_username_password = Number(/[^/@]+:[^/@]+@/u.test(value));
    features.has_unusual_port = Number(/:\d{1,5}(?:[/?#]|$)/u.test(value) && !/^https?:\/\/.+?:\d{1,5}\//u.test(value));
    features.hostname_token_count = hostname ? hostname.toLowerCase().split(/[^a-z0-9]+/u).filter(Boolean).length : 0;
    features.repeated_query_keys = repeatedQueryKeys(value);
    return features;
  }

  function riskLevelForProbability(probability, thresholds = defaultThresholds) {
    if (probability >= (thresholds.high ?? 0.75)) return "VERY HIGH";
    if (probability >= (thresholds.medium ?? 0.5)) return "HIGH";
    if (probability >= (thresholds.low ?? 0.25)) return "CAUTION";
    return "LOW";
  }

  function riskThemeForLevel(level) {
    if (level === "VERY HIGH") return "danger";
    if (level === "HIGH") return "high-risk";
    if (level === "CAUTION") return "caution";
    return "safe";
  }

  function buildReasons(features, impersonatedBrand) {
    const reasons = [];

    if (impersonatedBrand) {
      reasons.push(`Potential brand lookalike detected: ${impersonatedBrand}.`);
    }
    if (features.url_length >= 100) {
      reasons.push(`URL is unusually long: ${features.url_length} characters.`);
    }
    if (features.num_subdomains >= 3) {
      reasons.push(`Hostname contains ${features.num_subdomains} subdomains.`);
    }
    if (features.has_ip) {
      reasons.push("Hostname uses an IP address instead of a domain name.");
    }
    if (features.has_at) {
      reasons.push("URL contains user info or authentication-style syntax.");
    }
    if (features.num_special_chars >= 8) {
      reasons.push(`URL contains ${features.num_special_chars} special characters.`);
    }
    if (features.has_percent) {
      reasons.push("URL includes percent-encoded content.");
    }
    if (features.phiusiil_has_obfuscation) {
      reasons.push(`PhiUSIIL obfuscation signal: ${features.phiusiil_obfuscated_char_count} encoded characters.`);
    }
    if (features.url_entropy >= 4.5) {
      reasons.push(`URL entropy is ${features.url_entropy.toFixed(2)}, indicating a complex string.`);
    }

    const foundKeywords = keywords.filter((keyword) => features[`keyword_${keyword}`]);
    if (foundKeywords.length) {
      reasons.push(`Suspicious keywords detected: ${foundKeywords.join(", ")}.`);
    }

    if (!reasons.length) {
      reasons.push("No strong URL-only signals were detected.");
    }

    return reasons.slice(0, 5);
  }

  function buildRecommendations(level) {
    if (level === "LOW") {
      return [
        "No strong URL-only warning was detected. Still review the sender before sharing sensitive details.",
        "Verify the domain through an official source before entering credentials.",
      ];
    }
    if (level === "CAUTION") {
      return [
        "Check the domain and sender carefully before continuing.",
        "Do not enter passwords or payment details unless the destination has been verified separately.",
      ];
    }
    if (level === "HIGH") {
      return [
        "Do not log in or provide personal information on this URL.",
        "Verify the site through an official channel before you trust it.",
      ];
    }
    return [
      "Do not continue to this page or enter credentials, banking details, or MFA codes.",
      "Close the page and reach the service through the official website or app.",
    ];
  }

  function buildAvailableSignals(features, databaseMatch, probability, impersonatedBrand) {
    const hasKeyword = keywords.some((keyword) => features[`keyword_${keyword}`]);
    const structuralWarning = features.has_at || features.has_percent || features.num_special_chars >= 8;
    const hostWarning = features.has_ip || features.num_subdomains >= 3;
    return {
      url_structure: structuralWarning ? "Warning" : "Checked",
      hostname_checks: hostWarning ? "Warning" : "Checked",
      keyword_scan: hasKeyword ? "Warning" : "Checked",
      phishvn_database: databaseMatch.matched ? "Database match" : "Checked",
      brand_lookalike: impersonatedBrand ? "Warning" : "Checked",
      url_obfuscation: features.phiusiil_has_obfuscation ? "Warning" : "Checked",
      machine_learning: probability >= 0.5 ? "Warning" : "Checked",
      https_status: features.has_https ? "HTTPS detected" : "HTTP detected",
      dns_resolution: "Not checked",
      redirect_chain: "Not checked",
      page_metadata: "Not checked",
      screenshot_preview: "Not checked",
    };
  }

  function databaseMatch(url, features) {
    const database = model?.phishvnDatabase;
    if (!database) return { matched: false, type: null, provenance: null };
    const parts = parseParts(url);
    let hostname = parts.hostname.toLowerCase().replace(/\.+$/u, "");
    if (hostname.startsWith("www.")) hostname = hostname.slice(4);
    const path = parts.path.replace(/\/+$/u, "");
    const key = `${hostname}${path}?${parts.query}`.replace(/\?$/u, "");
    const record = recordsByUrl.get(key);
    if (record) {
      return {
        matched: true,
        type: "exact_url",
        provenance: "Matched in reference database",
        record,
      };
    }
    if (database.knownPhishingUrlKeys?.includes(key)) {
      return {
        matched: true,
        type: "exact_url",
        provenance: "Matched in reference database",
        record: recordsByUrl.get(key) || recordsByHost.get(hostname) || null,
      };
    }
    if (database.knownPhishingHosts?.some((host) => host.replace(/^www\./u, "") === hostname)) {
      return {
        matched: true,
        type: "known_phishing_host",
        provenance: "Matched in reference database",
        record: recordsByHost.get(hostname) || null,
      };
    }
    const signatureNames = database.signatureFeatureNames || [];
    const signature = signatureNames
      .map((name) => Number(features[name] ?? features[`phishvn_${name}`] ?? 0).toFixed(5))
      .join(",");
    if (database.knownPhishingFeatureSignatures?.includes(signature)) {
      return { matched: true, type: "feature_signature", provenance: "Matched in reference database" };
    }
    return { matched: false, type: null, provenance: null };
  }

  function buildRiskAssessment(features, probability, sourceMatch, impersonatedBrand) {
    const numericProbability = Number.isFinite(probability) ? clamp(Number(probability), 0, 1) : 0;
    let heuristicScore = 0;

    if (features.url_length >= 120) heuristicScore += 18;
    if (features.num_subdomains >= 3) heuristicScore += 16;
    if (features.has_ip) heuristicScore += 18;
    if (features.has_at) heuristicScore += 12;
    if (features.num_special_chars >= 8) heuristicScore += 10;
    if (features.has_percent) heuristicScore += 8;
    if (features.url_entropy >= 4.5) heuristicScore += 10;

    const keywordCount = keywords.filter((keyword) => features[`keyword_${keyword}`]).length;
    heuristicScore += keywordCount * 8;

    const score = impersonatedBrand
      ? 100
      : clamp(Math.round((numericProbability * 100 * 0.6) + heuristicScore), 0, 100);
    const level = impersonatedBrand ? "VERY HIGH" : riskLevelForProbability(numericProbability);
    const reasons = buildReasons(features, impersonatedBrand);
    if (sourceMatch.matched) reasons.unshift("Matched in reference database.");
    const recommendations = buildRecommendations(level);
    const verdicts = {
      LOW: "No strong URL-only warning was detected.",
      CAUTION: "The URL shows some risky characteristics and deserves caution.",
      HIGH: "This URL shows multiple suspicious characteristics.",
      "VERY HIGH": "This URL shows strong phishing indicators and should not be trusted.",
    };

    return {
      risk_score: score,
      risk_level: level,
      risk_theme: riskThemeForLevel(level),
      verdict: verdicts[level],
      reasons,
      recommendations,
      available_signals: buildAvailableSignals(features, sourceMatch, numericProbability, impersonatedBrand),
      disclaimer: "This is a dataset-backed risk assessment, not proof that a destination is safe or malicious.",
    };
  }

  function treeOutput(tree, features) {
    let total = 0;
    tree.forEach((entry) => {
      let node = 0;
      while (entry.left[node] !== -1) {
        const feature = model.features[entry.feature[node]];
        node = features[feature] <= entry.threshold[node] ? entry.left[node] : entry.right[node];
      }
      total += entry.output[node];
    });
    return total;
  }

  function scaledDecision(features, classifier) {
    return classifier.coefficients.reduce(
      (score, coefficient, index) => score
        + ((features[model.features[index]] - classifier.mean[index]) / classifier.scale[index]) * coefficient,
      classifier.intercept,
    );
  }

  function sigmoid(value) {
    return 1 / (1 + Math.exp(-value));
  }

  function modelProbabilities(features) {
    if (!model || !Array.isArray(model.features) || !model.models) {
      throw new Error("The browser model is unavailable.");
    }
    const forest = model.models.random_forest.trees;
    const boosting = model.models.gradient_boosting;
    const svm = model.models.svm;
    const logistic = model.models.logistic_regression;
    const probabilities = {
      random_forest: treeOutput(forest, features) / forest.length,
      gradient_boosting: sigmoid(
        boosting.initialRawScore + boosting.learningRate * treeOutput(boosting.trees, features),
      ),
      svm: sigmoid(-(svm.calibrationA * scaledDecision(features, svm) + svm.calibrationB)),
      logistic_regression: sigmoid(scaledDecision(features, logistic)),
    };
    return probabilities;
  }

  function predict(features, thresholds = defaultThresholds) {
    const models = modelProbabilities(features);
    const probability = Object.values(models).reduce((sum, value) => sum + value, 0) / 4;
    const prediction = probability > 0.5 ? "phishing" : "legitimate";
    const riskLevel = riskLevelForProbability(probability, thresholds);
    const assessments = Object.fromEntries(Object.entries(models).map(([name, score]) => {
      const modelThreshold = name === "svm" ? model.models.svm.decisionThreshold ?? 0.5 : 0.5;
      return [name, {
        prediction: score >= modelThreshold ? "phishing" : "legitimate",
        probability: score,
        risk_level: riskLevelForProbability(score, thresholds),
      }];
    }));
    return { prediction, probability, risk_level: riskLevel, models: assessments };
  }

  function explainFeatures(features) {
    const explanations = [];
    if (features.url_length >= 100) explanations.push("The URL is unusually long, a signal considered by the model.");
    if (features.num_subdomains >= 3) explanations.push("The hostname contains several subdomain levels.");
    if (features.has_ip) explanations.push("The hostname is an IP address rather than a domain name.");
    if (features.num_special_chars >= 8) explanations.push("The URL contains many non-alphanumeric characters.");
    if (features.url_entropy >= 4.5) explanations.push("The URL has relatively high character entropy.");
    const foundKeywords = keywords.filter((keyword) => features[`keyword_${keyword}`]);
    if (foundKeywords.length) {
      explanations.push(`The URL contains configured keyword signals: ${foundKeywords.join(", ")}.`);
    }
    if (!explanations.length) {
      explanations.push("No configured URL signals stood out; this is not proof of safety.");
    }
    return explanations;
  }

  function assessUrl(value, thresholds, options = {}) {
    const url = validateUrl(value);
    const includeExperimental = Boolean(options.includeExperimental);
    const features = extractFeatures(url, includeExperimental);
    const modelAssessment = predict(features, thresholds || defaultThresholds);
    const modelEnsemble = {
      prediction: modelAssessment.prediction,
      probability: modelAssessment.probability,
      risk_level: modelAssessment.risk_level,
    };
    const sourceMatch = databaseMatch(url, features);
    const impersonatedBrand = detectBrandImpersonation(parseParts(url).hostname);
    const urlCategory = classifyUrl(url, sourceMatch.record?.brand || "");
    if (sourceMatch.matched) {
      const recordLabel = sourceMatch.record?.label;
      modelAssessment.prediction = recordLabel === "Benign" ? "legitimate" : "phishing";
      modelAssessment.risk_level = recordLabel === "Benign" ? "LOW" : "VERY HIGH";
    }
    const riskAssessment = buildRiskAssessment(
      features,
      modelAssessment.probability,
      sourceMatch,
      impersonatedBrand,
    );
    if (sourceMatch.matched && !sourceMatch.record) {
      riskAssessment.risk_level = "VERY HIGH";
      riskAssessment.risk_theme = "danger";
      riskAssessment.risk_score = 100;
      riskAssessment.verdict = "Direct database result: confirmed phishing host or signature.";
    }
    if (sourceMatch.record) {
      riskAssessment.risk_level = sourceMatch.record.label === "Benign" ? "LOW" : "VERY HIGH";
      riskAssessment.risk_theme = sourceMatch.record.label === "Benign" ? "safe" : "danger";
      riskAssessment.risk_score = sourceMatch.record.label === "Benign" ? 0 : 100;
      riskAssessment.verdict = sourceMatch.record.label === "Benign"
        ? "Direct database result: verified benign URL."
        : "Direct database result: confirmed phishing URL.";
    }
    if (impersonatedBrand) {
      modelAssessment.prediction = "phishing";
      modelAssessment.risk_level = "VERY HIGH";
      riskAssessment.risk_level = "VERY HIGH";
      riskAssessment.risk_theme = "danger";
      riskAssessment.risk_score = 100;
      riskAssessment.verdict = `Potential brand lookalike detected: ${impersonatedBrand}.`;
    }
    const ownSite = isSafeWebUrl(url);
    if (ownSite) {
      modelAssessment.prediction = "legitimate";
      modelAssessment.risk_level = "LOW";
      riskAssessment.risk_level = "LOW";
      riskAssessment.risk_theme = "safe";
      riskAssessment.risk_score = 0;
    }

    return {
      url,
      ...modelAssessment,
      risk_score: riskAssessment.risk_score,
      risk_level: riskAssessment.risk_level,
      risk_theme: riskAssessment.risk_theme,
      verdict: riskAssessment.verdict,
      reasons: riskAssessment.reasons,
      recommendations: riskAssessment.recommendations,
      available_signals: riskAssessment.available_signals,
      database_match: sourceMatch,
      url_category: urlCategory,
      direct_database_verdict: sourceMatch.matched ? {
        label: sourceMatch.record?.label || "Phishing",
        record: sourceMatch.record,
      } : null,
      model_ensemble: modelEnsemble,
      brand_impersonation: impersonatedBrand,
      easter_egg: ownSite,
      verification_stages: {
        database: sourceMatch.matched ? "matched" : "checked_no_match",
        machine_learning: "evaluated",
      },
      features,
      explanations: explainFeatures(features),
      disclaimer: riskAssessment.disclaimer,
    };
  }

  const api = {
    assessUrl,
    classifyUrl,
    extractFeatures,
    getPhishingExamples,
    isSafeWebUrl,
    predict,
    setDatabaseRecords,
    validateUrl,
  };
  root.SafewebBrowserModel = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(globalThis);