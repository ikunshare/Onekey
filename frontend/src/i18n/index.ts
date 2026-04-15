import {computed, ref} from 'vue'
import zh from './zh'
import en from './en'

const langs: Record<string, Record<string, string>> = {zh, en}
const currentLang = ref(localStorage.getItem('language') || 'zh')

export function setLanguage(lang: string) {
    currentLang.value = lang
    localStorage.setItem('language', lang)
}

export function getLanguage() {
    return currentLang.value
}

export function t(key: string, params?: Record<string, string>): string {
    const dict = langs[currentLang.value] || langs['zh']
    let text = dict[key] || key
    if (params) {
        for (const [k, v] of Object.entries(params)) {
            text = text.replace(new RegExp(`\\{${k}\\}`, 'g'), v)
        }
    }
    return text
}

export function useI18n() {
    return {
        t,
        lang: computed(() => currentLang.value),
        setLanguage,
    }
}
