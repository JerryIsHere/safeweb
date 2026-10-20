const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

require("../web/static/model-data.js");
const browserModel = require("../web/static/browser-model.js");
const webInspection = require("../web/static/web-inspection.js");

test("browser features retain the Python model's ordered schema", () => {
  const features = browserModel.extractFeatures("https://one.two.example.co.uk/login?next=home");

  assert.deepEqual(Object.keys(features), globalThis.safewebModel.features);
  assert.equal(features.url_length, 45);
  assert.equal(features.num_subdomains, 2);
  assert.equal(features.has_https, 1);
  assert.equal(features.keyword_login, 1);
});

test("browser features handle IP hosts, paths, queries, and Unicode", () => {
  const ipv4 = browserModel.extractFeatures("http://192.0.2.10/a//b?x=1");
  const ipv6 = browserModel.extractFeatures("https://[2001:db8::1]/signin");
  const unicode = browserModel.extractFeatures("https://пример.рф/подтвердить?x=1");

  assert.equal(ipv4.has_ip, 1);
  assert.equal(ipv4.has_double_slash, 1);
  assert.equal(ipv4.has_query, 1);
  assert.equal(ipv6.has_ip, 1);
  assert.equal(unicode.domain_length, Array.from("пример.рф").length);
  assert.equal(browserModel.extractFeatures("https://a.b.ck/").num_subdomains, 0);
  assert.equal(browserModel.extractFeatures("https://x.www.ck/").num_subdomains, 1);
});

test("www prefixes are removed before all feature extraction", () => {
  const apex = browserModel.extractFeatures("https://divineskins.gg");
  const www = browserModel.extractFeatures("https://www.divineskins.gg");

  assert.deepEqual(www, apex);
  assert.equal(www.phishvn_suspicious_tld, 0);
});

test("experimental browser features are opt-in and preserve the default schema", () => {
  const defaultFeatures = browserModel.extractFeatures("https://example.com/login?next=home");
  const experimentalFeatures = browserModel.extractFeatures(
    "https://example.com/login?next=home",
    true,
  );

  assert.equal(Object.keys(defaultFeatures).length, 55);
  assert.equal(Object.keys(experimentalFeatures).length, 67);
  assert.equal(experimentalFeatures.query_parameter_count, 1);
  assert.equal(experimentalFeatures.hostname_depth, 2);
  assert.equal(experimentalFeatures.has_unusual_port, 0);
});

test("browser PhiUSIIL obfuscation features match Python percent-encoding semantics", () => {
  const features = browserModel.extractFeatures("https://example.com/%2F%41");

  assert.equal(features.phiusiil_has_obfuscation, 1);
  assert.equal(features.phiusiil_obfuscated_char_count, 6);
  assert.equal(features.phiusiil_obfuscation_ratio, 6 / "https://example.com/%2F%41".length);
  assert.equal(features.phiusiil_has_obfuscation, 1);
});

test("browser model returns a four-tier risk score and transparent signal status", () => {
  const result = browserModel.assessUrl("https://example.com/login");

  assert.ok(["phishing", "legitimate"].includes(result.prediction));
  assert.ok(result.probability >= 0 && result.probability <= 1);
  assert.ok(["LOW", "CAUTION", "HIGH", "VERY HIGH"].includes(result.risk_level));
  assert.ok(Number.isInteger(result.risk_score));
  assert.ok(result.risk_score >= 0 && result.risk_score <= 100);
  assert.ok(Array.isArray(result.reasons));
  assert.equal(result.available_signals.dns_resolution, "Not checked");
  assert.equal(Object.keys(result.features).length, 55);
  assert.equal(result.available_signals.url_obfuscation, "Checked");
  assert.equal(result.verification_stages.machine_learning, "evaluated");
});

test("browser SVM classification uses its exported validation threshold", () => {
  const features = browserModel.extractFeatures("https://example.com/login");
  const assessment = browserModel.predict(features).models.svm;
  const threshold = globalThis.safewebModel.models.svm.decisionThreshold ?? 0.5;

  assert.equal(assessment.prediction, assessment.probability >= threshold ? "phishing" : "legitimate");
});

test("lookalike brands trigger a high-risk warning without changing raw model scores", () => {
  const result = browserModel.assessUrl("https://faceboook.com");

  assert.equal(result.brand_impersonation, "Facebook");
  assert.equal(result.prediction, "phishing");
  assert.equal(result.risk_level, "VERY HIGH");
  assert.equal(result.risk_theme, "danger");
  assert.equal(result.risk_score, 100);
  assert.ok(result.reasons.includes("Potential brand lookalike detected: Facebook."));
  assert.equal(result.available_signals.brand_lookalike, "Warning");
  assert.equal(result.probability, result.model_ensemble.probability);
});

test("neutral brand and TLD signals do not raise the legitimate DivineSkins URL", () => {
  const result = browserModel.assessUrl("https://www.divineskins.gg");

  assert.equal(result.brand_impersonation, null);
  assert.equal(result.risk_level, "LOW");
  assert.equal(result.features.phishvn_suspicious_tld, 0);
});

test("official Google Drive URL overrides the model-only false positive transparently", () => {
  const result = browserModel.assessUrl("https://drive.google.com/drive/my-drive");
  const components = result.risk_score_components;

  assert.equal(result.prediction, "legitimate");
  assert.equal(result.risk_level, "LOW");
  assert.equal(result.url_category.category_id, "cloud_hosting");
  assert.equal(result.url_category.brand, "Google");
  assert.equal(result.brand_impersonation, null);
  assert.ok(result.model_ensemble.probability > 0.9);
  assert.ok(components.official_brand_adjustment < 0);
  assert.equal(components.url_category, 0);
  assert.equal(components.total, result.risk_score);
  assert.equal(
    components.model
      + components.url_structure
      + components.brand
      + components.official_brand_adjustment
      + components.url_category
      + components.database,
    result.risk_score,
  );
  assert.equal(result.available_signals.official_brand_domain, "Verified brand domain");
  assert.equal(result.available_signals.url_category, "Informational only");
  assert.ok(result.reasons.some((reason) => reason.includes("URL-only model warning was adjusted")));
});

test("official brand adjustment does not suppress URL obfuscation warnings", () => {
  const result = browserModel.assessUrl("https://drive.google.com/drive/my-drive?next=%2Flogin");

  assert.equal(result.prediction, "phishing");
  assert.equal(result.available_signals.url_obfuscation, "Warning");
  assert.equal(result.risk_score_components.official_brand_adjustment, 0);
});

test("known PhishVN hosts are attributed and still pass through model verification", () => {
  const result = browserModel.assessUrl("http://tiktokshopseller-vn.com");

  assert.equal(result.database_match.matched, true);
  assert.equal(result.database_match.type, "exact_url");
  assert.equal(result.direct_database_verdict.label, "Phishing");
  assert.equal(result.database_match.provenance, "Matched in reference database");
  assert.equal(result.prediction, "phishing");
  assert.equal(result.risk_level, "VERY HIGH");
  assert.equal(result.verification_stages.machine_learning, "evaluated");
});

test("comparison examples require a high-confidence phishing record and 80% host similarity", () => {
  browserModel.setDatabaseRecords([
    {
      url: "https://pinteresst.com/login",
      url_key: "pinteresst.com/login",
      label: "Phishing",
      detected_at: "2025-04-03",
      tier: "Silver",
      category_id: "social_messaging",
      category: "Social Media",
      provider: "Custom domain",
      brand: "Pinterest",
    },
    {
      url: "https://unrelated.example/login",
      url_key: "unrelated.example/login",
      label: "Phishing",
      detected_at: "2025-04-03",
      tier: "Gold",
    },
    {
      url: "https://pinterest-login.example/verify",
      url_key: "pinterest-login.example/verify",
      label: "Phishing",
      detected_at: "2025-04-03",
      tier: "Silver",
    },
    {
      url: "https://pinteresst.com/offer",
      url_key: "pinteresst.com/offer",
      label: "Phishing",
      detected_at: "2025-04-03",
      tier: "Bronze",
    },
  ]);

  const examples = browserModel.getPhishingExamples("https://pinterest.com", 5);

  assert.equal(examples.length, 1);
  assert.equal(examples[0].url, "https://pinteresst.com/login");
  assert.ok(examples[0].similarity >= 0.8);
});

test("exact PhishVN benign records decide the verdict without changing model scores", () => {
  browserModel.setDatabaseRecords([{
    url: "https://verified.example/account",
    url_key: "verified.example/account",
    label: "Benign",
    detected_at: "2025-01-02",
    tier: "Gold",
    category_id: "banking_finance",
    category: "Banking & Finance",
    provider: "Custom domain",
    brand: "Example Bank",
    key_features: {},
  }]);

  const result = browserModel.assessUrl("https://verified.example/account");

  assert.equal(result.database_match.type, "exact_url");
  assert.equal(result.direct_database_verdict.label, "Benign");
  assert.equal(result.prediction, "legitimate");
  assert.equal(result.risk_level, "LOW");
  assert.equal(result.model_ensemble.prediction, "phishing");
  assert.ok(result.model_ensemble.probability > 0.5);
  assert.equal(Object.keys(result.models).length, 4);
  assert.equal(result.models.random_forest.probability >= 0, true);
});

  test("known phishing host matches attach their PhishVN source record", () => {
    browserModel.setDatabaseRecords([{
      url: "http://tiktokshopseller-vn.com/login",
      url_key: "tiktokshopseller-vn.com/login",
      label: "Phishing",
      detected_at: "2025-04-03",
      tier: "Silver",
      category_id: "social_messaging",
      category: "Social Media",
      provider: "Custom domain",
      brand: "TikTok",
      key_features: {},
    }]);
    const result = browserModel.assessUrl("http://tiktokshopseller-vn.com");

    assert.equal(result.database_match.type, "exact_url");
    assert.equal(result.direct_database_verdict.record.tier, "Silver");
  });

test("SafeWeb URL variants trigger the easter egg and URL intelligence", () => {
  for (const url of [
    "https://jerryishere.github.io/safeweb",
    "http://JERRYISHERE.github.io/safeweb/?ref=check",
    "jerryishere.github.io/safeweb/",
  ]) {
    assert.equal(browserModel.isSafeWebUrl(browserModel.validateUrl(url)), true);
  }
  const identity = browserModel.classifyUrl("https://vietcombank-login.github.io/verify");
  assert.equal(identity.category_id, "banking_finance");
  assert.equal(identity.provider, "GitHub Pages");
  assert.equal(identity.brand, "Vietcombank");
  const safeweb = browserModel.assessUrl("https://jerryishere.github.io/safeweb");
  assert.equal(safeweb.brand_impersonation, null);
  assert.equal(safeweb.risk_level, "LOW");
});

test("browser validation rejects empty, malformed, and non-HTTP URLs", () => {
  for (const value of ["", "   ", "ftp://example.com", "https://bad host.test", "http://[bad"]) {
    assert.throws(() => browserModel.validateUrl(value));
  }
});

test("browser validation heals bare names, domains, default ports, and trailing slashes", () => {
  assert.equal(browserModel.validateUrl("divineskins.gg"), "https://divineskins.gg");
  assert.equal(browserModel.validateUrl("vietcombank"), "https://vietcombank.com");
  assert.equal(browserModel.validateUrl("vietcombank/login?next=home"), "https://vietcombank.com/login?next=home");
  assert.equal(browserModel.validateUrl("HTTP://WWW.Example.COM:80/path/"), "http://www.example.com/path");
});

test("redirect and DNS inspection distinguish nested targets, NXDOMAIN, and resolver failures", () => {
  assert.equal(
    webInspection.unwrapRedirectParameters("https://short.example/?next=https%3A%2F%2Fexample.org%2Flogin"),
    "https://example.org/login",
  );
  assert.equal(
    webInspection.summarizeDnsReplies([
      ["A", { status: 3, answers: [] }],
      ["AAAA", { status: 3, answers: [] }],
    ]).domainExists,
    false,
  );
  assert.equal(
    webInspection.summarizeDnsReplies([["A", { status: 2, answers: [] }]]).domainExists,
    null,
  );
  assert.equal(
    webInspection.summarizeDnsReplies([
      ["A", { status: 3, answers: [] }],
      ["AAAA", null],
    ]).domainExists,
    null,
  );
  const resolved = webInspection.summarizeDnsReplies([
    ["A", { status: 0, answers: [{ type: 1, data: "192.0.2.5" }] }],
  ]);
  assert.equal(resolved.domainExists, true);
  assert.deepEqual(resolved.addresses, ["192.0.2.5"]);
});

test("live requests are gated by explicit consent after local assessment", () => {
  const clientScript = fs.readFileSync(
    path.join(__dirname, "../web/static/script.js"),
    "utf8",
  );

  const localAssessment = clientScript.indexOf("latestResult = assessUrl(url)");
  const optIn = clientScript.indexOf('if (document.querySelector("#live-inspection-toggle").checked)');
  const liveRequest = clientScript.indexOf("latestResult = await inspectLive(url)");
  assert.ok(localAssessment >= 0 && optIn > localAssessment && liveRequest > optIn);
  assert.match(clientScript, /https:\/\/dns\.google\/resolve/);
  assert.match(clientScript, /https:\/\/api\.microlink\.io/);
  assert.doesNotMatch(clientScript, /XMLHttpRequest|sendBeacon/);
});

test("all four language dictionaries include local model states", () => {
  const context = { window: {} };
  const translationsPath = path.join(__dirname, "../web/static/translations.js");
  vm.runInNewContext(fs.readFileSync(translationsPath, "utf8"), context);

  for (const language of ["vi", "en", "fr", "de"]) {
    assert.ok(context.window.safewebTranslations[language].modelReady);
    assert.ok(context.window.safewebTranslations[language].modelLoading);
    assert.ok(context.window.safewebTranslations[language].modelLoadFailed);
    assert.ok(context.window.safewebTranslations[language].errorModelUnavailable);
  }
});

test("backend report text is translated using the selected locale", () => {
  const context = { window: { safewebTranslations: {} }, document: {}, localStorage: {} };
  const elementMap = new Map();
  const makeElement = () => ({
    textContent: "",
    className: "",
    style: {},
    dataset: {},
    classList: {
      toggle() {},
      add() {},
    },
    items: [],
    replaceChildren() { this.items = []; },
    append(item) { this.items.push(item); },
    addEventListener() {},
    setAttribute() {},
    removeAttribute() {},
    showModal() {},
    hidden: false,
  });

  context.document.querySelector = (selector) => {
    if (!elementMap.has(selector)) elementMap.set(selector, makeElement());
    return elementMap.get(selector);
  };
  const languageOption = () => ({
    dataset: { language: "en" },
    addEventListener() {},
    focus() {},
    setAttribute() {},
  });
  const options = [languageOption(), languageOption(), languageOption(), languageOption()];
  context.document.querySelectorAll = (selector) => {
    if (selector === ".language-option") return options;
    if (selector === "button:not([hidden]):not([disabled])") return options;
    if (selector === "[data-i18n]" || selector === "[data-i18n-attr]") return [];
    return [];
  };
  context.document.documentElement = { lang: "en", classList: { remove() {} } };
  context.document.body = makeElement();
  context.document.body.dataset = {};
  context.document.body.classList = { add() {}, remove() {} };
  context.document.activeElement = options[0];
  context.document.createElement = (tagName) => ({
    tagName,
    textContent: "",
    style: {},
    classList: { toggle() {} },
    append() {},
    appendChild() {},
    replaceChildren() {},
    setAttribute() {},
    focus() {},
  });
  context.requestAnimationFrame = (callback) => callback();

  vm.runInNewContext(fs.readFileSync(path.join(__dirname, "../web/static/translations.js"), "utf8"), context);
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, "../web/static/script.js"), "utf8"), context);

  context.renderResult({
    risk_level: "HIGH",
    risk_score: 80,
    verdict: "This URL shows multiple suspicious characteristics.",
    recommendations: [
      "Do not log in or provide personal information on this URL.",
      "Verify the site through an official channel before you trust it.",
    ],
    disclaimer: "This is a dataset-backed risk assessment, not proof that a destination is safe or malicious.",
    reasons: [],
    available_signals: {},
    explanations: [],
    features: {},
    prediction: "phishing",
  }, "fr");

  assert.equal(elementMap.get("#result-title").textContent, "Cette URL présente plusieurs caractéristiques suspectes.");
  assert.equal(elementMap.get("#risk-verdict").textContent, "Cette URL présente plusieurs caractéristiques suspectes.");
  assert.equal(elementMap.get("#result-limitations").textContent, "Le niveau de risque est un avertissement du modèle, pas une preuve qu’une URL est sûre ou malveillante.");
  assert.deepEqual(
    elementMap.get("#recommendation-list").items.map((item) => item.textContent),
    [
      "Ne vous connectez pas et ne fournissez pas d’informations personnelles sur cette URL.",
      "Vérifiez le site via un canal officiel avant de lui faire confiance.",
    ],
  );
});