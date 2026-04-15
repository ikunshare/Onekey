<template>
  <n-config-provider>
    <n-message-provider>
      <div class="oobe-wrapper">
        <n-card style="max-width: 560px; width: 100%;">
          <template #header>
            <n-space vertical align="center" :size="4">
              <n-text strong style="font-size: 24px;">{{ t('oobe.title') }}</n-text>
              <n-text depth="3">{{ t('oobe.subtitle') }}</n-text>
            </n-space>
          </template>

          <n-space vertical :size="24">
            <n-steps :current="currentStep + 1" size="small">
              <n-step :title="t('oobe.step_welcome')" />
              <n-step :title="t('oobe.step_key')" />
              <n-step :title="t('oobe.step_done')" />
            </n-steps>

            <!-- Step 0: Welcome -->
            <div v-show="currentStep === 0">
              <n-space vertical :size="8">
                <n-h3>{{ t('oobe.welcome_title') }}</n-h3>
                <n-text>{{ t('oobe.welcome_desc') }}</n-text>
                <n-text>{{ t('oobe.welcome_desc2') }}</n-text>
                <n-text strong>{{ t('oobe.features') }}</n-text>
                <n-ul>
                  <n-li>{{ t('oobe.feature1') }}</n-li>
                  <n-li>{{ t('oobe.feature2') }}</n-li>
                  <n-li>{{ t('oobe.feature3') }}</n-li>
                  <n-li>{{ t('oobe.feature4') }}</n-li>
                </n-ul>
                <n-a href="https://shop.ikunshare.com" target="_blank">{{ t('oobe.buy_key') }}</n-a>
              </n-space>
            </div>

            <!-- Step 1: Key Verification -->
            <div v-show="currentStep === 1">
              <n-space vertical :size="16">
                <n-h3>{{ t('oobe.key_title') }}</n-h3>
                <n-text>{{ t('oobe.key_desc') }}</n-text>
                <n-form-item :label="t('oobe.key_label')">
                  <n-input
                    v-model:value="keyInput"
                    :placeholder="t('oobe.key_placeholder')"
                    @keypress.enter="verifyKey"
                  />
                </n-form-item>
                <n-text depth="3" style="font-size: 12px;">{{ t('oobe.key_helper') }}</n-text>

                <n-alert
                  v-if="keyStatus.show"
                  :type="keyStatus.type === 'success' ? 'success' : 'error'"
                  :title="keyStatus.message"
                >
                  <n-descriptions v-if="keyData" :columns="1" label-placement="left" size="small">
                    <n-descriptions-item :label="t('oobe.key_type')">{{ keyTypeLabel(keyData.type) }}</n-descriptions-item>
                    <n-descriptions-item :label="t('oobe.key_expires')">{{ keyData.expiresAt ? formatDate(keyData.expiresAt) : t('oobe.permanent') }}</n-descriptions-item>
                    <n-descriptions-item :label="t('oobe.key_usage')">{{ keyData.usageCount }} / {{ keyData.totalUsage }}</n-descriptions-item>
                    <n-descriptions-item :label="t('oobe.key_status')">{{ keyData.isActive ? t('oobe.active') : t('oobe.inactive') }}</n-descriptions-item>
                  </n-descriptions>
                </n-alert>
              </n-space>
            </div>

            <!-- Step 2: Done -->
            <div v-show="currentStep === 2">
              <n-space vertical :size="16">
                <n-h3>{{ t('oobe.done_title') }}</n-h3>
                <n-text>{{ t('oobe.done_desc') }}</n-text>
                <n-text>{{ t('oobe.done_desc2') }}</n-text>
                <n-descriptions v-if="keyData" :columns="1" label-placement="left" bordered size="small" style="margin-top: 16px">
                  <n-descriptions-item :label="t('oobe.key_type')">{{ keyTypeLabel(keyData.type) }}</n-descriptions-item>
                  <n-descriptions-item :label="t('oobe.key_expires')">{{ keyData.expiresAt ? formatDateTime(keyData.expiresAt) : t('oobe.permanent') }}</n-descriptions-item>
                </n-descriptions>
              </n-space>
            </div>

            <!-- Navigation -->
            <n-space justify="space-between">
              <n-button v-if="currentStep > 0" @click="currentStep--">
                {{ t('oobe.prev') }}
              </n-button>
              <div v-else />
              <n-button v-if="currentStep === 0" type="primary" @click="currentStep++">
                {{ t('oobe.next') }}
              </n-button>
              <n-button v-if="currentStep === 1" type="primary" @click="verifyKey" :loading="loading">
                {{ t('oobe.verify_btn') }}
              </n-button>
              <n-button v-if="currentStep === 2" type="primary" @click="finishSetup" :loading="loading">
                {{ t('oobe.finish') }}
              </n-button>
            </n-space>
          </n-space>
        </n-card>
      </div>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { useI18n } from '../i18n'
import { VerifyKey, UpdateConfig } from '../../wailsjs/go/main/App'

const { t } = useI18n()
const router = useRouter()
const message = useMessage()

const currentStep = ref(0)
const keyInput = ref('')
const keyData = ref<any>(null)
const loading = ref(false)
const keyStatus = ref<{ show: boolean; type: string; message: string }>({ show: false, type: '', message: '' })

function keyTypeLabel(type: string) {
  return t(`key_type.${type}`) || type
}

function formatDate(dateStr: string | null) {
  if (!dateStr) return t('oobe.permanent')
  return new Date(dateStr).toLocaleDateString()
}

function formatDateTime(dateStr: string | null) {
  if (!dateStr) return t('oobe.permanent')
  const d = new Date(dateStr)
  return `${d.toLocaleDateString()} ${d.toLocaleTimeString()}`
}

async function verifyKey() {
  const key = keyInput.value.trim()
  if (!key) {
    message.error(t('oobe.enter_key'))
    return
  }

  loading.value = true
  try {
    const result = await VerifyKey(key)
    if (result.key && result.info) {
      keyData.value = result.info
      keyStatus.value = { show: true, type: 'success', message: t('oobe.verify_success') }
      setTimeout(() => {
        currentStep.value = 2
      }, 2000)
    } else {
      keyStatus.value = { show: true, type: 'error', message: t('oobe.verify_fail') }
    }
  } catch (e) {
    keyStatus.value = { show: true, type: 'error', message: t('oobe.verify_error') }
  } finally {
    loading.value = false
  }
}

async function finishSetup() {
  if (!keyData.value) {
    message.error(t('oobe.enter_key'))
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
      message.success(t('oobe.config_saved'))
      setTimeout(() => {
        router.push('/')
      }, 1500)
    } else {
      message.error(result.message || t('oobe.config_save_failed'))
    }
  } catch (e: any) {
    message.error(t('oobe.config_save_failed'))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.oobe-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 24px;
}
</style>
