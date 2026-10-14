const translations = window.safewebTranslations || { en: {} };
const { assessUrl, validateUrl } = window.SafewebBrowserModel || {};
const supportedLanguages = ["vi", "en", "fr", "de"];
const storageKey = "safeweb.language";
const form = document.querySelector("#analysis-form");
const input = document.querySelector("#url-input");
const message = document.querySelector("#form-message");
const dialog = document.querySelector("#language-dialog");
const languageSwitcher = document.querySelector("#language-switcher");
const languageCode = document.querySelector("#language-code");
const languageOptions = [...document.querySelectorAll(".language-option")];
const confirmLanguage = document.querySelector("#language-confirm");
const cancelLanguage = document.querySelector("#language-cancel");
let currentLanguage = "en";
let selectedLanguage = "en";
let hasConfirmedLanguage = false;
let returnFocusElement = null;
let latestResult = null;
let latestEnteredUrl = null;
let latestNormalizedUrl = null;
let currentMessageKey = null;

function translation(key, language = currentLanguage) {
  const parts = key.split(".");
  const read = (value) => parts.reduce((entry, part) => entry?.[part], value);
  return read(translations[language]) ?? read(translations.en) ?? key;
}

function setTranslatedAttributes(element, declarations, language) {
  declarations.split(";").forEach((declaration) => {
    const [attribute, key] = declaration.split(":").map((part) => part.trim());
    if (attribute && key) element.setAttribute(attribute, translation(key, language));
  });
}

function applyLanguage(language) {
  const locale = supportedLanguages.includes(language) ? language : "en";
  document.documentElement.lang = locale;
  document.title = translation("pageTitle", locale);
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    element.textContent = translation(element.dataset.i18n, locale);
  });
  document.querySelectorAll("[data-i18n-attr]").forEach((element) => {
    setTranslatedAttributes(element, element.dataset.i18nAttr, locale);
  });
  languageCode.textContent = locale.toUpperCase();
  const modelState = document.querySelector(".model-state");
  if (modelState) {
    modelState.textContent = translation(window.safewebModel?.trees?.length ? "modelReady" : "modelMissing", locale);
  }
  if (currentMessageKey) message.textContent = translation(currentMessageKey, locale);
  if (latestNormalizedUrl) {
    const normalizedNote = document.querySelector("#normalized-note");
    normalizedNote.hidden = latestNormalizedUrl === latestEnteredUrl;
    normalizedNote.textContent = normalizedNote.hidden
      ? ""
      : `${translation("normalizedUrl", locale)} ${latestNormalizedUrl}`;
  }
  const themeNextKey = {
    "cyber-dark": "themeContrast",
    contrast: "themeLight",
    light: "themeDark",
  }[document.body.dataset.theme || "cyber-dark"];
  const themeButton = document.querySelector("#theme-switcher");
  if (themeButton) {
    themeButton.textContent = translation(themeNextKey, locale);
    themeButton.setAttribute("aria-label", `${translation("themeControl", locale)}: ${translation(themeNextKey, locale)}`);
  }
  if (latestResult) renderResult(latestResult, locale);
}

function setMessage(key) {
  currentMessageKey = key;
  message.textContent = key ? translation(key) : "";
}

function updateLanguageOptions() {
  languageOptions.forEach((option) => {
    const selected = option.dataset.language === selectedLanguage;
    option.setAttribute("aria-checked", String(selected));
  });
}

function selectLanguage(language) {
  if (!supportedLanguages.includes(language)) return;
  selectedLanguage = language;
  updateLanguageOptions();
  applyLanguage(language);
}

function openLanguageDialog(trigger = null) {
  returnFocusElement = trigger;
  selectedLanguage = currentLanguage;
  cancelLanguage.hidden = !hasConfirmedLanguage;
  updateLanguageOptions();
  dialog.removeAttribute("open");
  dialog.showModal();
  document.body.classList.add("language-open");
  applyLanguage(selectedLanguage);
  requestAnimationFrame(() => {
    const selectedOption = languageOptions.find((option) => option.dataset.language === selectedLanguage);
    (selectedOption || languageOptions[0]).focus();
  });
}

function readPreference() {
  try {
    const value = localStorage.getItem(storageKey);
    const valid = supportedLanguages.includes(value);
    return { exists: value !== null, valid, language: valid ? value : "en" };
  } catch {
    return { exists: false, valid: false, language: "en" };
  }
}

function savePreference(language) {
  try {
    localStorage.setItem(storageKey, language);
  } catch {
    // Keep the current selection for this visit when storage is unavailable.
  }
}

function translateExplanation(explanation, language) {
  const explanationKeys = {
    "The URL is unusually long, a signal considered by the model.": "signalLong",
    "The hostname contains several subdomain levels.": "signalSubdomains",
    "The hostname is an IP address rather than a domain name.": "signalIp",
    "The URL contains many non-alphanumeric characters.": "signalSpecial",
    "The URL has relatively high character entropy.": "signalEntropy",
    "No configured URL signals stood out; this is not proof of safety.": "signalNone",
    "Matched in PhishVN Database.": "databaseMatchReason",
  };

  if (typeof explanation === "string") {
    if (explanationKeys[explanation]) return translation(explanationKeys[explanation], language);
    if (explanation.startsWith("URL is unusually long:")) return translation("signalLong", language);
    if (explanation.startsWith("Hostname contains")) return translation("signalSubdomains", language);
    if (explanation.startsWith("Hostname uses an IP address")) return translation("signalIp", language);
    if (explanation.startsWith("URL contains") && explanation.includes("special characters")) return translation("signalSpecial", language);
    if (explanation.startsWith("URL entropy is")) return translation("signalEntropy", language);
    if (explanation.startsWith("Suspicious keywords detected")) {
      const keywordSuffix = explanation.replace(/^Suspicious keywords detected:\s*/, "").replace(/\.$/, "");
      return translation("signalKeywords", language).replace("{keywords}", keywordSuffix);
    }
    if (explanation.startsWith("No strong URL-only signals")) return translation("signalNone", language);
  }

  const keywordPrefix = "The URL contains configured keyword signals: ";
  if (typeof explanation === "string" && explanation.startsWith(keywordPrefix)) {
    const keywords = explanation.slice(keywordPrefix.length).replace(/\.$/, "");
    return translation("signalKeywords", language).replace("{keywords}", keywords);
  }
  return translation("signalUnknown", language);
}

function riskTheme(level) {
  const themes = {
    LOW: "safe",
    CAUTION: "caution",
    HIGH: "high-risk",
    "VERY HIGH": "danger",
  };
  return themes[level] || "safe";
}

function riskClass(level) {
  const classes = {
    LOW: "low",
    CAUTION: "caution",
    HIGH: "high",
    "VERY HIGH": "danger",
  };
  return classes[level] || "low";
}

function riskLabel(level, language = currentLanguage) {
  const labels = {
    LOW: "riskLevelLow",
    CAUTION: "riskLevelCaution",
    HIGH: "riskLevelHigh",
    "VERY HIGH": "riskLevelVeryHigh",
  };
  return translation(labels[level] || "riskLevelLow", language);
}

function translateBackendText(text, language = currentLanguage) {
  const verbatimText = text || "";
  const textKeys = {
    "No strong URL-only warning was detected.": "verdictLow",
    "The URL shows some risky characteristics and deserves caution.": "verdictCaution",
    "This URL shows multiple suspicious characteristics.": "verdictHigh",
    "This URL shows strong phishing indicators and should not be trusted.": "verdictVeryHigh",
    "No strong URL-only warning was detected. Still review the sender before sharing sensitive details.": "recommendationLow1",
    "Verify the domain through an official source before entering credentials.": "recommendationLow2",
    "Check the domain and sender carefully before continuing.": "recommendationCaution1",
    "Do not enter passwords or payment details unless the destination has been verified separately.": "recommendationCaution2",
    "Do not log in or provide personal information on this URL.": "recommendationHigh1",
    "Verify the site through an official channel before you trust it.": "recommendationHigh2",
    "Do not continue to this page or enter credentials, banking details, or MFA codes.": "recommendationVeryHigh1",
    "Close the page and reach the service through the official website or app.": "recommendationVeryHigh2",
    "This assessment uses only URL text and local model features. Domain age, DNS status, reputation feeds, and page content are not checked unless a trusted client-side source is available.": "disclaimer",
    "This is a dataset-backed risk assessment, not proof that a destination is safe or malicious.": "disclaimer",
  };
  return translation(textKeys[verbatimText] || verbatimText, language);
}

function renderResult(result, language = currentLanguage) {
  const level = result.risk_level || "LOW";
  document.body.dataset.riskState = riskTheme(level);

  const predictionKey = result.prediction === "phishing"
    ? "predictionSuspicious"
    : "predictionLegitimate";
  const verdictKey = result.live_inspection?.domainExists === false
    ? "verdictDomainMissing"
    : predictionKey;
  const translatedVerdict = result.live_inspection?.domainExists === false
    ? translation(verdictKey, language)
    : translateBackendText(result.verdict || translation(verdictKey, language), language);
  document.querySelector("#result-title").textContent = translatedVerdict;

  const badge = document.querySelector("#risk-badge");
  badge.textContent = riskLabel(level, language);
  badge.className = `risk-badge risk-${riskClass(level)}`;

  const levelLabel = document.querySelector("#risk-level-label");
  levelLabel.textContent = riskLabel(level, language);
  const verdict = document.querySelector("#risk-verdict");
  verdict.textContent = translatedVerdict;
  document.querySelector("#verdict-icon").textContent = ({
    LOW: "✓", CAUTION: "!", HIGH: "!", "VERY HIGH": "×",
  })[level] || "?";
  const meter = document.querySelector("#signal-meter");
  const severity = ({ LOW: 1, CAUTION: 2, HIGH: 3, "VERY HIGH": 4 })[level] || 0;
  meter.replaceChildren(...[1, 2, 3, 4].map((step) => {
    const segment = document.createElement("span");
    segment.className = step <= severity ? `meter-segment ${riskClass(level)}` : "meter-segment";
    return segment;
  }));
  meter.setAttribute("aria-label", riskLabel(level, language));

  const sources = document.querySelector("#verification-sources");
  sources.replaceChildren();
  const sourceLabels = [
    ["database", result.database_match?.matched ? "databaseMatched" : "databaseChecked"],
    ["machine_learning", "mlChecked"],
  ];
  sourceLabels.forEach(([name, key]) => {
    const badge = document.createElement("span");
    badge.className = `source-pill${name === "database" && result.database_match?.matched ? " matched" : ""}`;
    badge.textContent = translation(key, language);
    sources.append(badge);
  });
  if (result.live_inspection) {
    const badge = document.createElement("span");
    badge.className = "source-pill live";
    badge.textContent = translation("liveChecked", language);
    sources.append(badge);
  }

  const reasons = Array.isArray(result.reasons) && result.reasons.length
    ? result.reasons
    : Array.isArray(result.explanations)
      ? result.explanations
      : [];
  const reasonList = document.querySelector("#reason-list");
  reasonList.replaceChildren();
  reasons.forEach((explanation) => {
    const item = document.createElement("li");
    item.textContent = translateExplanation(explanation, language);
    reasonList.append(item);
  });

  const availableSignals = result.available_signals || {};
  const signalSummary = document.querySelector("#signal-summary");
  signalSummary.replaceChildren();
  Object.entries(availableSignals).forEach(([name, value]) => {
    const item = document.createElement("li");
    item.className = `criterion ${value === "Not checked" ? "unchecked" : ["Database match", "Warning", "HTTP detected", "Domain not found"].includes(value) ? "warning" : "checked"}`;
    const label = document.createElement("span");
    const status = document.createElement("span");
    label.textContent = translation(`criteria.${name}`, language);
    const statusKeys = {
      Checked: "statusChecked",
      "Not checked": "statusNotChecked",
      "Database match": "statusDatabaseMatch",
      Warning: "statusWarning",
      "HTTPS detected": "statusHttps",
      "HTTP detected": "statusHttp",
      "Domain resolves": "statusDomainLive",
      "Domain not found": "statusDomainMissing",
      Inspected: "statusInspected",
      "Not available": "statusUnavailable",
    };
    status.textContent = translation(statusKeys[value] || "statusChecked", language);
    status.className = "criterion-status";
    item.append(label, status);
    signalSummary.append(item);
  });

  const recommendations = Array.isArray(result.recommendations) && result.recommendations.length
    ? result.recommendations
    : [translation("recommendationGeneric", language)];
  const recommendationList = document.querySelector("#recommendation-list");
  recommendationList.replaceChildren();
  recommendations.forEach((itemText) => {
    const item = document.createElement("li");
    item.textContent = translateBackendText(itemText, language);
    recommendationList.append(item);
  });

  const limitations = document.querySelector("#result-limitations");
  limitations.textContent = `${translation("disclaimer", language)}${result.live_inspection ? translation("liveDisclaimer", language) : ""}`;

  const explanations = Array.isArray(result.explanations) ? result.explanations : [];
  const signalList = document.querySelector("#signal-list");
  signalList.replaceChildren();
  explanations.forEach((explanation) => {
    const item = document.createElement("li");
    item.textContent = translateExplanation(explanation, language);
    signalList.append(item);
  });
  document.querySelector("#signal-count").textContent = String(explanations.length);

  const featureList = document.querySelector("#feature-list");
  featureList.replaceChildren();
  Object.entries(result.features || {}).forEach(([name, value]) => {
    const pair = document.createElement("div");
    const label = document.createElement("dt");
    const amount = document.createElement("dd");
    const featureKey = `features.${name}`;
    const translatedName = translation(featureKey, language);
    label.textContent = translatedName === featureKey ? name.replaceAll("_", " ") : translatedName;
    amount.textContent = typeof value === "number"
      ? value.toFixed(2).replace(/\.00$/, "")
      : String(value);
    pair.append(label, amount);
    featureList.append(pair);
  });
  document.querySelector("#result-disclaimer").textContent = translation("disclaimer", language);
  renderLiveInspection(result.live_inspection, language);
}

function renderLiveInspection(inspection, language = currentLanguage) {
  const panel = document.querySelector("#live-results");
  panel.hidden = !inspection;
  if (!inspection) return;
  const dns = document.querySelector("#dns-summary");
  dns.replaceChildren();
  Object.entries(inspection.dns?.records || {}).forEach(([type, answers]) => {
    const item = document.createElement("li");
    item.textContent = `${type}: ${answers.length ? answers.join(", ") : translation("statusNoRecord", language)}`;
    dns.append(item);
  });
  const dnsState = document.createElement("li");
  dnsState.className = `criterion ${inspection.domainExists ? "checked" : inspection.domainExists === false ? "warning" : "unchecked"}`;
  dnsState.textContent = inspection.domainExists === null
    ? translation("statusUnavailable", language)
    : translation(inspection.domainExists ? "statusDomainLive" : "statusDomainMissing", language);
  dns.append(dnsState);

  const chain = document.querySelector("#redirect-chain");
  chain.replaceChildren(...inspection.redirectChain.map((url) => {
    const item = document.createElement("li");
    item.textContent = url;
    return item;
  }));
  const metadata = document.querySelector("#metadata-summary");
  metadata.replaceChildren();
  const entries = Object.entries(inspection.metadata || {}).filter(([, value]) => value);
  if (!entries.length) {
    const empty = document.createElement("dd");
    empty.textContent = translation("metadataUnavailable", language);
    metadata.append(empty);
  }
  entries.forEach(([name, value]) => {
    const label = document.createElement("dt");
    const text = document.createElement("dd");
    label.textContent = translation(`metadata.${name}`, language);
    text.textContent = value;
    metadata.append(label, text);
  });
  document.querySelector("#screenshot-card").hidden = !inspection.screenshotUrl;
  if (inspection.screenshotUrl) {
    const image = document.querySelector("#site-screenshot");
    const skeleton = document.querySelector(".screenshot-skeleton");
    const previewEnabled = document.querySelector("#screenshot-toggle").checked;
    const frame = document.querySelector("#screenshot-frame");
    frame.hidden = !previewEnabled;
    image.hidden = true;
    skeleton.hidden = !previewEnabled;
    image.onload = () => {
      image.hidden = !document.querySelector("#screenshot-toggle").checked;
      skeleton.hidden = true;
    };
    image.onerror = () => {
      skeleton.textContent = translation("screenshotUnavailable", language);
      image.hidden = true;
      skeleton.hidden = !document.querySelector("#screenshot-toggle").checked;
      if (latestResult?.available_signals) latestResult.available_signals.screenshot_preview = "Not available";
      const screenshotLabel = translation("criteria.screenshot_preview", language);
      const criterion = [...document.querySelectorAll("#signal-summary .criterion")]
        .find((item) => item.firstElementChild?.textContent === screenshotLabel);
      if (criterion) {
        criterion.className = "criterion unchecked";
        criterion.lastElementChild.textContent = translation("statusUnavailable", language);
      }
    };
    image.src = inspection.screenshotUrl;
  }
}

async function resolveDns(domain) {
  const types = { A: 1, AAAA: 28, MX: 15, NS: 2, CNAME: 5 };
  const entries = await Promise.all(Object.entries(types).map(async ([name, type]) => {
    try {
      const endpoint = `https://dns.google/resolve?name=${encodeURIComponent(domain)}&type=${type}`;
      const response = await fetch(endpoint, { headers: { accept: "application/dns-json" }, signal: AbortSignal.timeout(7000) });
      if (!response.ok) throw new Error("DNS lookup unavailable");
      const result = await response.json();
      return [name, { status: result.Status, answers: result.Answer || [] }];
    } catch {
      return [name, null];
    }
  }));
  return window.SafewebWebInspection.summarizeDnsReplies(entries);
}

async function inspectMetadata(url) {
  const endpoint = `https://api.microlink.io/?url=${encodeURIComponent(url)}&screenshot=true&meta=true`;
  const response = await fetch(endpoint, { signal: AbortSignal.timeout(12000) });
  if (!response.ok) throw new Error("Metadata lookup unavailable");
  const payload = await response.json();
  const data = payload.data || {};
  return {
    metadata: {
      title: data.title,
      description: data.description,
      author: data.author,
      generator: data.generator,
    },
    finalUrl: data.url,
    screenshotUrl: data.screenshot?.url || null,
  };
}

async function inspectLive(url) {
  const firstDestination = window.SafewebWebInspection.unwrapRedirectParameters(url);
  const chain = [url];
  if (firstDestination !== url) chain.push(firstDestination);
  let inspectedUrl = firstDestination;
  let metadata = {};
  let screenshotUrl = null;
  try {
    const result = await inspectMetadata(inspectedUrl);
    metadata = result.metadata;
    if (result.finalUrl && /^https?:\/\//iu.test(result.finalUrl) && result.finalUrl !== inspectedUrl) {
      inspectedUrl = result.finalUrl;
      if (!chain.includes(inspectedUrl)) chain.push(inspectedUrl);
    }
    screenshotUrl = result.screenshotUrl;
  } catch {
    screenshotUrl = `https://s.wordpress.com/mshots/v1/${encodeURIComponent(inspectedUrl)}?w=1000`;
  }
  const hostname = new URL(inspectedUrl).hostname;
  const [dns, destinationAssessment] = await Promise.all([
    resolveDns(hostname),
    Promise.resolve(assessUrl(inspectedUrl)),
  ]);
  const domainExists = dns.status === "resolved" ? true : dns.status === "missing" ? false : null;
  const availableSignals = { ...latestResult.available_signals };
  availableSignals.dns_resolution = domainExists === null ? "Not available" : domainExists ? "Domain resolves" : "Domain not found";
  availableSignals.redirect_chain = chain.length > 1 ? "Inspected" : "Checked";
  availableSignals.page_metadata = Object.values(metadata).some(Boolean) ? "Inspected" : "Not available";
  availableSignals.screenshot_preview = screenshotUrl ? "Inspected" : "Not available";
  const rank = { LOW: 0, CAUTION: 1, HIGH: 2, "VERY HIGH": 3 };
  const finalAssessment = { ...latestResult };
  if (rank[destinationAssessment.risk_level] > rank[finalAssessment.risk_level]) {
    Object.assign(finalAssessment, destinationAssessment);
  }
  if (domainExists === false && rank[finalAssessment.risk_level] < rank.CAUTION) {
    finalAssessment.risk_level = "CAUTION";
    finalAssessment.risk_theme = "caution";
  }
  finalAssessment.available_signals = availableSignals;
  finalAssessment.live_inspection = {
    url: inspectedUrl,
    redirectChain: chain,
    dns,
    domainExists,
    metadata,
    screenshotUrl,
    destinationAssessment,
  };
  return finalAssessment;
}

async function showScanStep(step, state) {
  const item = document.querySelector(`#scan-progress [data-step="${step}"]`);
  item.classList.remove("active", "complete", "skipped");
  item.classList.add(state);
  await new Promise((resolve) => setTimeout(resolve, 220));
}

function setTheme(theme) {
  document.body.dataset.theme = theme;
  try { localStorage.setItem("safeweb.theme", theme); } catch {}
  const nextThemeKey = { "cyber-dark": "themeContrast", contrast: "themeLight", light: "themeDark" }[theme];
  const themeButton = document.querySelector("#theme-switcher");
  themeButton.textContent = translation(nextThemeKey);
  themeButton.setAttribute("aria-label", `${translation("themeControl")}: ${translation(nextThemeKey)}`);
}

function cycleTheme() {
  const nextTheme = { "cyber-dark": "contrast", contrast: "light", light: "cyber-dark" };
  setTheme(nextTheme[document.body.dataset.theme || "cyber-dark"] || "cyber-dark");
}

languageSwitcher.addEventListener("click", () => openLanguageDialog(languageSwitcher));
document.querySelector("#theme-switcher").addEventListener("click", cycleTheme);
document.querySelector("#screenshot-toggle").addEventListener("change", (event) => {
  const visible = event.target.checked;
  const image = document.querySelector("#site-screenshot");
  const skeleton = document.querySelector(".screenshot-skeleton");
  document.querySelector("#screenshot-frame").hidden = !visible;
  image.hidden = !visible || !image.complete || image.naturalWidth === 0;
  skeleton.hidden = !visible || image.complete && image.naturalWidth > 0;
});
languageOptions.forEach((option) => {
  option.addEventListener("click", () => selectLanguage(option.dataset.language));
});

dialog.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    event.preventDefault();
    if (hasConfirmedLanguage) dialog.close("escape");
    return;
  }

  if (event.key === "Tab") {
    const focusable = [...dialog.querySelectorAll("button:not([hidden]):not([disabled])")];
    const first = focusable[0];
    const last = focusable.at(-1);
    if (event.shiftKey && (document.activeElement === first || document.activeElement === dialog)) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  if (["ArrowDown", "ArrowRight", "ArrowUp", "ArrowLeft"].includes(event.key)) {
    const activeIndex = languageOptions.indexOf(document.activeElement);
    if (activeIndex < 0) return;
    event.preventDefault();
    const direction = event.key === "ArrowDown" || event.key === "ArrowRight" ? 1 : -1;
    const nextIndex = (activeIndex + direction + languageOptions.length) % languageOptions.length;
    const nextOption = languageOptions[nextIndex];
    selectLanguage(nextOption.dataset.language);
    nextOption.focus();
  }
});

dialog.addEventListener("cancel", (event) => {
  if (!hasConfirmedLanguage) event.preventDefault();
});

dialog.addEventListener("close", () => {
  document.body.classList.remove("language-open");
  document.documentElement.classList.remove("language-pending");
  selectedLanguage = currentLanguage;
  applyLanguage(currentLanguage);
  const focusTarget = returnFocusElement?.isConnected ? returnFocusElement : input;
  returnFocusElement = null;
  focusTarget.focus({ preventScroll: true });
});

confirmLanguage.addEventListener("click", () => {
  currentLanguage = selectedLanguage;
  hasConfirmedLanguage = true;
  savePreference(currentLanguage);
  dialog.close("confirm");
});

cancelLanguage.addEventListener("click", () => dialog.close("cancel"));

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  setMessage(null);
  if (!input.value.trim()) {
    setMessage("errorUrlRequired");
    input.setAttribute("aria-invalid", "true");
    input.focus();
    return;
  }

  let url;
  const enteredValue = input.value.trim();
  try {
    url = validateUrl(enteredValue);
  } catch {
    setMessage("errorInvalidUrl");
    input.setAttribute("aria-invalid", "true");
    input.focus();
    return;
  }

  input.removeAttribute("aria-invalid");
  if (!window.safewebModel?.trees?.length || typeof assessUrl !== "function") {
    setMessage("errorModelUnavailable");
    return;
  }

  const normalizedNote = document.querySelector("#normalized-note");
  latestEnteredUrl = enteredValue;
  latestNormalizedUrl = url;
  normalizedNote.hidden = url === enteredValue;
  normalizedNote.textContent = url === enteredValue
    ? ""
    : `${translation("normalizedUrl")} ${url}`;
  const progress = document.querySelector("#scan-progress");
  const progressItems = [...progress.querySelectorAll("li")];
  progress.hidden = false;
  progressItems.forEach((item) => item.classList.remove("active", "complete", "skipped"));
  const submitButton = form.querySelector(".analyze-button");
  submitButton.disabled = true;
  submitButton.querySelector(".button-label").textContent = translation("analyzing");
  try {
    await showScanStep("database", "active");
    latestResult = assessUrl(url);
    await showScanStep("database", "complete");
    renderResult(latestResult);
    if (document.querySelector("#live-inspection-toggle").checked) {
      await showScanStep("live", "active");
      latestResult = await inspectLive(url);
      await showScanStep("live", "complete");
    } else {
      await showScanStep("live", "skipped");
    }
    await showScanStep("model", "active");
    renderResult(latestResult);
    await showScanStep("model", "complete");
  } catch (error) {
    setMessage(error?.message === "The browser model is unavailable." ? "errorModelUnavailable" : "errorPredictionUnavailable");
  } finally {
    submitButton.disabled = false;
    submitButton.querySelector(".button-label").textContent = translation("analyze");
    progress.hidden = true;
  }
});

input.addEventListener("input", () => {
  input.removeAttribute("aria-invalid");
  latestEnteredUrl = null;
  latestNormalizedUrl = null;
  document.querySelector("#normalized-note").hidden = true;
  if (currentMessageKey === "errorInvalidUrl" || currentMessageKey === "errorUrlRequired") setMessage(null);
});

const preference = readPreference();
currentLanguage = preference.language;
selectedLanguage = currentLanguage;
hasConfirmedLanguage = preference.exists;
dialog.removeAttribute("open");

if (preference.exists) {
  applyLanguage(currentLanguage);
  if (!preference.valid) savePreference(currentLanguage);
  document.documentElement.classList.remove("language-pending");
} else {
  applyLanguage("en");
  openLanguageDialog();
  document.documentElement.classList.remove("language-pending");
}

  let savedTheme = "cyber-dark";
  try {
    const storedTheme = localStorage.getItem("safeweb.theme");
    if (["cyber-dark", "contrast", "light"].includes(storedTheme)) savedTheme = storedTheme;
  } catch {}
  setTheme(savedTheme);