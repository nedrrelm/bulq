import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

// Import translation files
import errorsEn from './locales/en/errors.json'
import successEn from './locales/en/success.json'
import commonEn from './locales/en/common.json'

// Translation resources
const resources = {
  en: {
    errors: errorsEn,
    success: successEn,
    common: commonEn,
  },
  // Future languages will be added here:
  // ru: { errors: errorsRu, success: successRu, common: commonRu },
  // sr: { errors: errorsSr, success: successSr, common: commonSr },
}

i18n
  .use(initReactI18next) // Pass i18n instance to react-i18next
  .init({
    resources,
    lng: 'en', // Default language
    fallbackLng: 'en', // Fallback language if translation is missing

    // Namespaces
    ns: ['errors', 'success', 'common'],
    defaultNS: 'common',

    interpolation: {
      escapeValue: false, // React already escapes values
    },

    // Debug mode (disable in production)
    debug: import.meta.env.DEV,

    // Return key if translation is missing (useful for development)
    saveMissing: false,
    missingKeyHandler: (lng, ns, key) => {
      if (import.meta.env.DEV) {
        console.warn(`Missing translation: [${lng}][${ns}] ${key}`)
      }
    },
  })

export default i18n
