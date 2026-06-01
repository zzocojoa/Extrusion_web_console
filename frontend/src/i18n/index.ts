import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import en from "./locales/en.json";
import ko from "./locales/ko.json";

const storedLanguage =
  typeof window !== "undefined" ? window.localStorage.getItem("ewc.language") : null;
const initialLanguage = storedLanguage === "en" || storedLanguage === "ko" ? storedLanguage : "ko";

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    ko: { translation: ko },
  },
  lng: initialLanguage,
  fallbackLng: "en",
  interpolation: {
    escapeValue: false,
  },
});

export default i18n;
