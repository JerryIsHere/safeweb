(function (root) {
  "use strict";

  const model = root.safewebModel;
  const keywords = ["login", "signin", "verify", "account", "password", "bank", "payment", "confirm"];
  const rules = new Set(model?.publicSuffixRules || []);
  const lettersOrNumbers = /^[\p{L}\p{N}]$/u;
  const letters = /^\p{L}$/u;
  const whitespace = /[\s\u0085]/u;
  const defaultThresholds = { low: 0.25, medium: 0.5, high: 0.75 };

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
    const trimmed = value.trim();
    if (Array.from(trimmed).some((character) => whitespace.test(character))) {
      throw new TypeError("The URL must not contain whitespace.");
    }
    let parsed;
    try {
      parsed = new URL(trimmed);
    } catch {
      throw new TypeError("The URL is malformed.");
    }
    if (!["http:", "https:"].includes(parsed.protocol) || !parsed.hostname) {
      throw new TypeError("Enter a complete HTTP or HTTPS URL with a hostname.");
    }
    return trimmed;
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

  function buildReasons(features) {
    const reasons = [];

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

  function buildAvailableSignals(features) {
    return {
      url_structure: "Checked",
      hostname_checks: "Checked",
      keyword_scan: "Checked",
      https_status: features.has_https ? "HTTPS detected" : "HTTP detected",
      domain_age: "Not checked",
      dns_reputation: "Not checked",
      page_content: "Not checked",
      redirect_chain: "Not checked",
      reputation_feed: "Not checked",
    };
  }

  function buildRiskAssessment(features, probability) {
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

    const score = clamp(Math.round((numericProbability * 100 * 0.6) + heuristicScore), 0, 100);
    const level = riskLevelForProbability(numericProbability);
    const reasons = buildReasons(features);
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
      available_signals: buildAvailableSignals(features),
      disclaimer: "This assessment uses only URL text and local model features. Domain age, DNS status, reputation feeds, and page content are not checked unless a trusted client-side source is available.",
    };
  }

  function predict(features, thresholds = defaultThresholds) {
    if (!model || !Array.isArray(model.trees) || !Array.isArray(model.features)) {
      throw new Error("The browser model is unavailable.");
    }
    let probability = 0;
    model.trees.forEach((tree) => {
      let node = 0;
      while (tree.left[node] !== -1) {
        const feature = model.features[tree.feature[node]];
        node = features[feature] <= tree.threshold[node] ? tree.left[node] : tree.right[node];
      }
      probability += tree.positiveProbability[node];
    });
    probability /= model.trees.length;
    const prediction = probability > 0.5 ? "phishing" : "legitimate";
    const riskLevel = riskLevelForProbability(probability, thresholds);
    return { prediction, probability, risk_level: riskLevel };
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
    const riskAssessment = buildRiskAssessment(features, modelAssessment.probability);

    return {
      ...modelAssessment,
      risk_score: riskAssessment.risk_score,
      risk_level: riskAssessment.risk_level,
      risk_theme: riskAssessment.risk_theme,
      verdict: riskAssessment.verdict,
      reasons: riskAssessment.reasons,
      recommendations: riskAssessment.recommendations,
      available_signals: riskAssessment.available_signals,
      features,
      explanations: explainFeatures(features),
      disclaimer: riskAssessment.disclaimer,
    };
  }

  const api = { assessUrl, extractFeatures, predict, validateUrl };
  root.SafewebBrowserModel = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(globalThis);