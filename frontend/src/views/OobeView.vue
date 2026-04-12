<template>
  <div class="oobe-container">
    <div class="oobe-card">
      <div class="oobe-header">
        <button type="button" class="theme-toggle" @click="toggleTheme" :title="t('nav.settings')">
          <span class="material-icons">{{ isDark ? 'dark_mode' : 'light_mode' }}</span>
        </button>
        <div class="oobe-logo">
          <span class="material-icons" style="font-size: inherit">extension</span>
        </div>
        <h1 class="oobe-title">{{ t('oobe.title') }}</h1>
        <p class="oobe-subtitle">{{ t('oobe.subtitle') }}</p>
      </div>

      <div class="oobe-content">
        <div class="step-indicator">
          <div v-for="i in 3" :key="i" :class="['step-dot', { active: currentStep === i - 1, completed: currentStep > i - 1 }]"></div>
        </div>

        <!-- Step 0: Welcome -->
        <div v-show="currentStep === 0" class="oobe-step">
          <div class="welcome-text">
            <h3>{{ t('oobe.welcome_title') }}</h3>
            <p>{{ t('oobe.welcome_desc') }}</p>
            <p>{{ t('oobe.welcome_desc2') }}</p>
            <p><strong>{{ t('oobe.features') }}</strong></p>
            <p>• {{ t('oobe.feature1') }}</p>
            <p>• {{ t('oobe.feature2') }}</p>
            <p>• {{ t('oobe.feature3') }}</p>
            <p>• {{ t('oobe.feature4') }}</p>
            <a href="https://shop.ikunshare.com" target="_blank">• {{ t('oobe.buy_key') }}</a>
          </div>
        </div>

        <!-- Step 1: Key Verification -->
        <div v-show="currentStep === 1" class="oobe-step">
          <div class="welcome-text">
            <h3>{{ t('oobe.key_title') }}</h3>
            <p>{{ t('oobe.key_desc') }}</p>
          </div>
          <div class="key-input-section">
            <div class="input-group">
              <label for="activationKey" class="input-label">{{ t('oobe.key_label') }}</label>
              <input
                type="text"
                id="activationKey"
                v-model="keyInput"
                class="text-field"
                :placeholder="t('oobe.key_placeholder')"
                autocomplete="off"
                @keypress.enter="verifyKey"
              />
              <div class="input-helper">{{ t('oobe.key_helper') }}</div>
            </div>
            <div v-if="keyStatus.show" :class="['key-status', 'show', keyStatus.type]">
              <div class="status-header">
                <span class="material-icons">{{ keyStatus.icon }}</span>
                <span>{{ keyStatus.message }}</span>
              </div>
              <div v-if="keyData" class="key-info">
                <div class="key-info-item">
                  <span class="material-icons">label</span>
                  <span>类型：{{ keyTypeLabel(keyData.type) }}</span>
                </div>
                <div class="key-info-item">
                  <span class="material-icons">schedule</span>
                  <span>到期：{{ formatDate(keyData.expiresAt) }}</span>
                </div>
                <div class="key-info-item">
                  <span class="material-icons">analytics</span>
                  <span>使用次数：{{ keyData.usageCount }}</span>
                </div>
                <div class="key-info-item">
                  <span class="material-icons">{{ keyData.isActive ? 'check_circle' : 'cancel' }}</span>
                  <span>状态：{{ keyData.isActive ? '有效' : '无效' }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Step 2: Done -->
        <div v-show="currentStep === 2" class="oobe-step">
          <div class="welcome-text">
            <h3>{{ t('oobe.done_title') }}</h3>
            <p>{{ t('oobe.done_desc') }}</p>
            <p>{{ t('oobe.done_desc2') }}</p>
            <div v-if="keyData" class="key-info" style="margin-top: 24px">
              <div class="key-info-item">
                <span class="material-icons">verified_user</span>
                <span><strong>卡密类型：</strong>{{ keyTypeLabel(keyData.type) }}</span>
              </div>
              <div class="key-info-item">
                <span class="material-icons">event</span>
                <span><strong>有效期至：</strong>{{ formatDateTime(keyData.expiresAt) }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="oobe-actions">
          <button v-if="currentStep > 0" type="button" class="btn btn-text" @click="currentStep--">
            <span class="material-icons">arrow_back</span>
            {{ t('oobe.prev') }}
          </button>
          <button v-if="currentStep === 0" type="button" class="btn btn-primary btn-large" @click="currentStep++">
            <span class="material-icons">arrow_forward</span>
            {{ t('oobe.next') }}
          </button>
          <button v-if="currentStep === 1" type="button" class="btn btn-primary btn-large" @click="verifyKey" :disabled="loading">
            <span class="material-icons">verified</span>
            {{ t('oobe.verify_btn') }}
          </button>
          <button v-if="currentStep === 2" type="button" class="btn btn-primary btn-large" @click="finishSetup" :disabled="loading">
            <span class="material-icons">check</span>
            {{ t('oobe.finish') }}
          </button>
        </div>
      </div>

      <div v-if="loading" class="loading-overlay show">
        <div class="loading-spinner"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, inject } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from '../i18n'
import { VerifyKey, UpdateConfig } from '../../wailsjs/go/main/App'

const { t } = useI18n()
const router = useRouter()
const isDark = inject<any>('isDark')
const toggleTheme = inject<any>('toggleTheme')
const showSnackbar = inject<any>('showSnackbar')

const currentStep = ref(0)
const keyInput = ref('')
const keyData = ref<any>(null)
const loading = ref(false)
const keyStatus = ref({ show: false, type: '', message: '', icon: 'info' })

const typeNames: Record<string, string> = {
  day: '日卡', week: '周卡', month: '月卡', year: '年卡', permanent: '永久卡',
}

function keyTypeLabel(type: string) {
  return typeNames[type] || type
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString()
}

function formatDateTime(dateStr: string) {
  const d = new Date(dateStr)
  return `${d.toLocaleDateString()} ${d.toLocaleTimeString()}`
}

async function verifyKey() {
  const key = keyInput.value.trim()
  if (!key) {
    showSnackbar(t('oobe.enter_key'), 'error')
    return
  }
  if (!/^[A-Z0-9_-]+$/i.test(key)) {
    keyStatus.value = { show: true, type: 'error', message: t('oobe.invalid_format'), icon: 'error' }
    return
  }

  loading.value = true
  try {
    const result = await VerifyKey(key)
    if (result.key && result.info) {
      keyData.value = result.info
      keyStatus.value = { show: true, type: 'success', message: t('oobe.verify_success'), icon: 'check_circle' }
      setTimeout(() => {
        currentStep.value = 2
      }, 2000)
    } else {
      keyStatus.value = { show: true, type: 'error', message: t('oobe.verify_fail'), icon: 'error' }
    }
  } catch (e) {
    keyStatus.value = { show: true, type: 'error', message: t('oobe.verify_error'), icon: 'error' }
  } finally {
    loading.value = false
  }
}

async function finishSetup() {
  if (!keyData.value) {
    showSnackbar(t('oobe.enter_key'), 'error')
    currentStep.value = 1
    return
  }

  loading.value = true
  try {
    const result = await UpdateConfig({
      key: keyInput.value.trim(),
      steam_path: '',
      debug_mode: false,
      logging_files: true,
      show_console: false,
      language: 'zh',
    })
    if (result.success) {
      showSnackbar(t('oobe.config_saved'), 'success')
      setTimeout(() => {
        router.push('/')
      }, 1500)
    } else {
      showSnackbar(result.message || t('oobe.config_save_failed'), 'error')
    }
  } catch (e: any) {
    showSnackbar(t('oobe.config_save_failed') + ': ' + (e.message || ''), 'error')
  } finally {
    loading.value = false
  }
}
</script>
