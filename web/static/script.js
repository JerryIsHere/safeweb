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

function renderResult(result, language = currentLanguage) {
  const level = result.risk_level || "LOW";
  const score = Number.isFinite(result.risk_score)
    ? Math.max(0, Math.min(100, Number(result.risk_score)))
    : Math.round((Number(result.probability) || 0) * 100);

  document.body.dataset.riskState = riskTheme(level);

  const predictionKey = result.prediction === "phishing"
    ? "predictionSuspicious"
    : "predictionLegitimate";
  document.querySelector("#result-title").textContent = result.verdict || translation(predictionKey, language);

  const badge = document.querySelector("#risk-badge");
  badge.textContent = riskLabel(level, language);
  badge.className = `risk-badge risk-${riskClass(level)}`;

  const levelLabel = document.querySelector("#risk-level-label");
  levelLabel.textContent = riskLabel(level, language);
  const verdict = document.querySelector("#risk-verdict");
  verdict.textContent = result.verdict || translation(predictionKey, language);

  const scoreValue = document.querySelector("#score-value");
  scoreValue.innerHTML = `${score}<span>%</span>`;
  const fill = document.querySelector("#score-fill");
  fill.style.width = `${score}%`;
  fill.classList.toggle("high", level === "HIGH" || level === "VERY HIGH");
  fill.classList.toggle("danger", level === "VERY HIGH");

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
    item.textContent = `${name.replaceAll("_", " ").replace(/\b\w/g, (character) => character.toUpperCase())}: ${value}`;
    signalSummary.append(item);
  });

  const recommendations = Array.isArray(result.recommendations) && result.recommendations.length
    ? result.recommendations
    : [translation("recommendationGeneric", language)];
  const recommendationList = document.querySelector("#recommendation-list");
  recommendationList.replaceChildren();
  recommendations.forEach((itemText) => {
    const item = document.createElement("li");
    item.textContent = itemText;
    recommendationList.append(item);
  });

  const limitations = document.querySelector("#result-limitations");
  limitations.textContent = result.disclaimer || translation("disclaimer", language);

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
}

languageSwitcher.addEventListener("click", () => openLanguageDialog(languageSwitcher));
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

form.addEventListener("submit", (event) => {
  event.preventDefault();
  setMessage(null);
  if (!input.value.trim()) {
    setMessage("errorUrlRequired");
    input.setAttribute("aria-invalid", "true");
    input.focus();
    return;
  }

  let url;
  try {
    url = validateUrl(input.value);
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

  try {
    latestResult = assessUrl(url);
    renderResult(latestResult);
  } catch (error) {
    setMessage(error?.message === "The browser model is unavailable." ? "errorModelUnavailable" : "errorPredictionUnavailable");
  }
});

input.addEventListener("input", () => {
  input.removeAttribute("aria-invalid");
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