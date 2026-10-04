(function (root) {
  "use strict";

  const model = root.safewebModel;
  const keywords = ["login", "signin", "verify", "account", "password", "bank", "payment", "confirm"];
  const rules = new Set(model?.publicSuffixRules || []);
  const lettersOrNumbers = /^[\p{L}\p{N}]$/u;
  const letters = /^\p{L}$/u;
  const whitespace = /[\s\u0085]/u;

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

  function extractFeatures(value) {
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
    return features;
  }

  function predict(features, thresholds = { medium: 0.35, high: 0.7 }) {
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
    const riskLevel = probability >= thresholds.high ? "HIGH" : probability >= thresholds.medium ? "MEDIUM" : "LOW";
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

  function assessUrl(value, thresholds) {
    const url = validateUrl(value);
    const features = extractFeatures(url);
    return {
      ...predict(features, thresholds),
      features,
      explanations: explainFeatures(features),
      disclaimer: "This is a model assessment of URL characteristics, not proof of safety or harm.",
    };
  }

  const api = { assessUrl, extractFeatures, predict, validateUrl };
  root.SafewebBrowserModel = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(globalThis);