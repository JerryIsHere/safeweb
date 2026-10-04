const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

require("../web/static/model-data.js");
const browserModel = require("../web/static/browser-model.js");

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

test("browser model performs real inference and returns a bounded probability", () => {
  const result = browserModel.assessUrl("https://example.com/login");

  assert.ok(["phishing", "legitimate"].includes(result.prediction));
  assert.ok(result.probability >= 0 && result.probability <= 1);
  assert.ok(["LOW", "MEDIUM", "HIGH"].includes(result.risk_level));
  assert.equal(Object.keys(result.features).length, 30);
});

test("browser validation rejects empty, malformed, and non-HTTP URLs", () => {
  for (const value of ["", "   ", "ftp://example.com", "https://bad host.test", "http://[bad"]) {
    assert.throws(() => browserModel.validateUrl(value));
  }
});

test("the client never fetches or submits the entered URL", () => {
  const clientScript = fs.readFileSync(
    path.join(__dirname, "../web/static/script.js"),
    "utf8",
  );

  assert.doesNotMatch(clientScript, /\bfetch\s*\(/);
  assert.doesNotMatch(clientScript, /XMLHttpRequest|sendBeacon/);
});

test("all four language dictionaries include local model states", () => {
  const context = { window: {} };
  const translationsPath = path.join(__dirname, "../web/static/translations.js");
  vm.runInNewContext(fs.readFileSync(translationsPath, "utf8"), context);

  for (const language of ["vi", "en", "fr", "de"]) {
    assert.ok(context.window.safewebTranslations[language].modelReady);
    assert.ok(context.window.safewebTranslations[language].errorModelUnavailable);
  }
});