import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

// Import English translation files
import errorsEn from './locales/en/errors.json'
import successEn from './locales/en/success.json'
import commonEn from './locales/en/common.json'
import authEn from './locales/en/auth.json'
import groupsEn from './locales/en/groups.json'
import groupEn from './locales/en/group.json'
import runEn from './locales/en/run.json'
import shoppingEn from './locales/en/shopping.json'
import profileEn from './locales/en/profile.json'
import storeEn from './locales/en/store.json'
import productEn from './locales/en/product.json'
import adminEn from './locales/en/admin.json'
import notificationsEn from './locales/en/notifications.json'

// Import Russian translation files
import errorsRu from './locales/ru/errors.json'
import successRu from './locales/ru/success.json'
import commonRu from './locales/ru/common.json'
import authRu from './locales/ru/auth.json'
import groupsRu from './locales/ru/groups.json'
import groupRu from './locales/ru/group.json'
import runRu from './locales/ru/run.json'
import shoppingRu from './locales/ru/shopping.json'
import profileRu from './locales/ru/profile.json'
import storeRu from './locales/ru/store.json'
import productRu from './locales/ru/product.json'
import adminRu from './locales/ru/admin.json'
import notificationsRu from './locales/ru/notifications.json'

// Import Serbian translation files
import errorsSr from './locales/sr/errors.json'
import successSr from './locales/sr/success.json'
import commonSr from './locales/sr/common.json'
import authSr from './locales/sr/auth.json'
import groupsSr from './locales/sr/groups.json'
import groupSr from './locales/sr/group.json'
import runSr from './locales/sr/run.json'
import shoppingSr from './locales/sr/shopping.json'
import profileSr from './locales/sr/profile.json'
import storeSr from './locales/sr/store.json'
import productSr from './locales/sr/product.json'
import adminSr from './locales/sr/admin.json'
import notificationsSr from './locales/sr/notifications.json'

// Translation resources
const resources = {
  en: {
    errors: errorsEn,
    success: successEn,
    common: commonEn,
    auth: authEn,
    groups: groupsEn,
    group: groupEn,
    run: runEn,
    shopping: shoppingEn,
    profile: profileEn,
    store: storeEn,
    product: productEn,
    admin: adminEn,
    notifications: notificationsEn,
  },
  ru: {
    errors: errorsRu,
    success: successRu,
    common: commonRu,
    auth: authRu,
    groups: groupsRu,
    group: groupRu,
    run: runRu,
    shopping: shoppingRu,
    profile: profileRu,
    store: storeRu,
    product: productRu,
    admin: adminRu,
    notifications: notificationsRu,
  },
  sr: {
    errors: errorsSr,
    success: successSr,
    common: commonSr,
    auth: authSr,
    groups: groupsSr,
    group: groupSr,
    run: runSr,
    shopping: shoppingSr,
    profile: profileSr,
    store: storeSr,
    product: productSr,
    admin: adminSr,
    notifications: notificationsSr,
  },
}

i18n
  .use(initReactI18next) // Pass i18n instance to react-i18next
  .init({
    resources,
    lng: 'en', // Default language
    fallbackLng: 'en', // Fallback language if translation is missing

    // Namespaces
    ns: ['errors', 'success', 'common', 'auth', 'groups', 'group', 'run', 'shopping', 'profile', 'store', 'product', 'admin', 'notifications'],
    defaultNS: 'common',

    // Key separator configuration
    keySeparator: '.', // Default is '.' which we're using
    nsSeparator: ':', // Use ':' to separate namespace from key (e.g., 'namespace:key.subkey')

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
