<template>
  <div>
    <header class="app-bar">
      <div class="app-bar-content">
        <button class="btn btn-text" @click="router.push('/')">
          <span class="material-icons">arrow_back</span>
        </button>
        <span class="material-icons app-icon">settings</span>
        <h1 class="app-title">{{ t('settings.title') }}</h1>
      </div>
    </header>

    <main class="main-content settings-main">
      <!-- Key Management -->
      <div class="card">
        <div class="card-header">
          <span class="material-icons">verified</span>
          <h2>{{ t('settings.key_management') }}</h2>
        </div>
        <div class="card-content">
          <div class="settings-section">
            <div id="keyInfoSection">
              <div v-if="!detailedConfig" class="loading">{{ t('settings.loading_key') }}</div>
              <div v-else-if="detailedConfig.key" class="status-item">
                <span class="material-icons status-icon success">vpn_key</span>
                <span class="status-text">Key: {{ detailedConfig.key.substring(0, 12) }}...</span>
              </div>
            </div>

            <div class="key-change-section" style="margin-top: 16px">
              <h4 style="margin: 0 0 16px 0;">
                <span class="material-icons" style="vertical-align: middle; margin-right: 8px">swap_horiz</span>
                {{ t('settings.change_key') }}
              </h4>
              <div class="key-input-group" style="display: flex; gap: 8px; align-items: flex-start;">
                <div class="input-group" style="flex: 1; margin: 0">
                  <label for="newKey" class="input-label">{{ t('settings.new_key_label') }}</label>
                  <input type="text" id="newKey" v-model="newKey" class="text-field" :placeholder="t('settings.new_key_placeholder')" autocomplete="off" />
                  <div class="input-helper">{{ t('settings.new_key_helper') }}</div>
                </div>
                <button type="button" class="btn btn-secondary" @click="verifyNewKey" v-if="!newKeyVerified">
                  <span class="material-icons">check</span>
                  {{ t('settings.verify') }}
                </button>
                <button type="button" class="btn btn-primary" @click="saveNewKey" v-if="newKeyVerified">
                  <span class="material-icons">save</span>
                  {{ t('settings.save') }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Steam Config -->
      <div class="card">
        <div class="card-header">
          <span class="material-icons">games</span>
          <h2>{{ t('settings.steam_config') }}</h2>
        </div>
        <div class="card-content">
          <div class="settings-section">
            <div class="input-group">
              <label for="steamPath" class="input-label">{{ t('settings.steam_path_label') }}</label>
              <div style="display: flex; gap: 8px;">
                <input type="text" id="steamPath" v-model="steamPath" class="text-field" :placeholder="t('settings.steam_path_placeholder')" style="flex: 1" />
                <button type="button" class="btn btn-secondary" @click="detectSteamPath">
                  <span class="material-icons">search</span>
                  {{ t('settings.detect') }}
                </button>
              </div>
              <div class="input-helper">{{ t('settings.steam_path_helper') }}</div>
            </div>
            <div class="status-indicator">
              <span class="material-icons status-icon" :class="steamPath ? 'success' : ''">{{ steamPath ? 'check_circle' : 'info' }}</span>
              <span class="status-text">{{ steamPath || t('settings.steam_path_waiting') }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- App Config -->
      <div class="card">
        <div class="card-header">
          <span class="material-icons">tune</span>
          <h2>{{ t('settings.app_config') }}</h2>
        </div>
        <div class="card-content">
          <div class="settings-section">
            <div class="setting-item">
              <label class="setting-label">{{ t('settings.language') }}</label>
              <div class="radio-group">
                <label class="radio-item">
                  <input type="radio" v-model="language" value="zh" />
                  <span class="radio-button"></span>
                  <span class="radio-label">{{ t('settings.lang_zh') }}</span>
                </label>
                <label class="radio-item">
                  <input type="radio" v-model="language" value="en" />
                  <span class="radio-button"></span>
                  <span class="radio-label">{{ t('settings.lang_en') }}</span>
                </label>
              </div>
            </div>

            <div class="setting-item">
              <label class="checkbox-item">
                <input type="checkbox" v-model="debugMode" />
                <span class="checkbox-button"></span>
                <div class="checkbox-content">
                  <span class="checkbox-label">{{ t('settings.debug_mode') }}</span>
                  <span class="checkbox-description">{{ t('settings.debug_desc') }}</span>
                </div>
              </label>
            </div>

            <div class="setting-item">
              <label class="checkbox-item">
                <input type="checkbox" v-model="loggingFiles" />
                <span class="checkbox-button"></span>
                <div class="checkbox-content">
                  <span class="checkbox-label">{{ t('settings.logging') }}</span>
                  <span class="checkbox-description">{{ t('settings.logging_desc') }}</span>
                </div>
              </label>
            </div>

            <div class="setting-item">
              <label class="checkbox-item">
                <input type="checkbox" v-model="showConsole" />
                <span class="checkbox-button"></span>
                <div class="checkbox-content">
                  <span class="checkbox-label">{{ t('settings.console') }}</span>
                  <span class="checkbox-description">{{ t('settings.console_desc') }}</span>
                </div>
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="card">
        <div class="card-content">
          <div class="action-buttons" style="display: flex; gap: 12px; flex-wrap: wrap;">
            <button type="button" class="btn btn-primary" @click="saveConfig">
              <span class="material-icons">save</span>
              {{ t('settings.save_config') }}
            </button>
            <button type="button" class="btn btn-secondary" @click="showResetDialog = true">
              <span class="material-icons">restore</span>
              {{ t('settings.reset_config') }}
            </button>
          </div>
        </div>
      </div>
    </main>

    <!-- Confirm Dialog -->
    <div v-if="showResetDialog" class="dialog-overlay" @click.self="showResetDialog = false">
      <div class="dialog">
        <div class="dialog-header">
          <h3>{{ t('settings.confirm_title') }}</h3>
        </div>
        <div class="dialog-content">
          <p>{{ t('settings.confirm_reset') }}</p>
        </div>
        <div class="dialog-actions">
          <button type="button" class="btn btn-text" @click="showResetDialog = false">{{ t('settings.cancel') }}</button>
          <button type="button" class="btn btn-primary" @click="resetConfig">{{ t('settings.confirm') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, inject } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from '../i18n'
import { GetDetailedConfig, UpdateConfig, ResetConfig, VerifyKey, GetConfig } from '../../wailsjs/go/main/App'

const { t, setLanguage: setI18nLang } = useI18n()
const router = useRouter()
const showSnackbar = inject<any>('showSnackbar')

const detailedConfig = ref<any>(null)
const newKey = ref('')
const newKeyVerified = ref(false)
const steamPath = ref('')
const language = ref('zh')
const debugMode = ref(false)
const loggingFiles = ref(true)
const showConsole = ref(false)
const showResetDialog = ref(false)

onMounted(async () => {
  try {
    const resp = await GetDetailedConfig()
    if (resp.success) {
      detailedConfig.value = resp.config
      steamPath.value = resp.config.steam_path || ''
      language.value = resp.config.language || 'zh'
      debugMode.value = resp.config.debug_mode
      loggingFiles.value = resp.config.logging_files
      showConsole.value = resp.config.show_console
    }
  } catch (e) {}
})

async function verifyNewKey() {
  const key = newKey.value.trim()
  if (!key) return
  try {
    const result = await VerifyKey(key)
    if (result.key && result.info) {
      newKeyVerified.value = true
      showSnackbar(t('oobe.verify_success'), 'success')
    } else {
      showSnackbar(t('oobe.verify_fail'), 'error')
    }
  } catch (e) {
    showSnackbar(t('oobe.verify_error'), 'error')
  }
}

async function saveNewKey() {
  await saveConfigWith(newKey.value.trim())
  newKeyVerified.value = false
  newKey.value = ''
  // Reload config
  const resp = await GetDetailedConfig()
  if (resp.success) detailedConfig.value = resp.config
}

async function detectSteamPath() {
  try {
    const resp = await GetConfig()
    if (resp.success && resp.config.steam_path) {
      steamPath.value = resp.config.steam_path
      showSnackbar('Steam路径: ' + resp.config.steam_path, 'success')
    } else {
      showSnackbar(t('home.steam_path_not_found'), 'error')
    }
  } catch (e) {}
}

async function saveConfig() {
  await saveConfigWith(detailedConfig.value?.key || '')
}

async function saveConfigWith(key: string) {
  try {
    setI18nLang(language.value)
    const result = await UpdateConfig({
      key: key,
      steam_path: steamPath.value,
      debug_mode: debugMode.value,
      logging_files: loggingFiles.value,
      show_console: showConsole.value,
      language: language.value,
    })
    if (result.success) {
      showSnackbar(result.message, 'success')
    } else {
      showSnackbar(result.message, 'error')
    }
  } catch (e: any) {
    showSnackbar(e.message || 'Error', 'error')
  }
}

async function resetConfig() {
  showResetDialog.value = false
  try {
    const result = await ResetConfig()
    if (result.success) {
      showSnackbar(result.message, 'success')
      // Reload
      const resp = await GetDetailedConfig()
      if (resp.success) {
        detailedConfig.value = resp.config
        steamPath.value = resp.config.steam_path || ''
        language.value = resp.config.language || 'zh'
        debugMode.value = resp.config.debug_mode
        loggingFiles.value = resp.config.logging_files
        showConsole.value = resp.config.show_console
      }
    } else {
      showSnackbar(result.message, 'error')
    }
  } catch (e: any) {
    showSnackbar(e.message || 'Error', 'error')
  }
}
</script>
