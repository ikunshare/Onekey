<template>
  <div>
    <n-space :size="24" vertical>
      <!-- Key Management -->
      <n-card :title="t('settings.key_management')">
        <n-space :size="12" vertical>
          <div v-if="keyLoading">
            <n-spin size="small"/>
            {{ t('settings.loading_key') }}
          </div>
          <template v-else-if="detailedConfig && detailedConfig.key">
            <n-alert :bordered="false" :type="keyInfo && keyInfo.isActive ? 'success' : 'warning'">
              Key: {{ detailedConfig.key.substring(0, 12) }}...
            </n-alert>
            <n-descriptions v-if="keyInfo" :column="2" bordered size="small">
              <n-descriptions-item :label="t('oobe.key_type')">
                {{ t('key_type.' + keyInfo.type) || keyInfo.type }}
              </n-descriptions-item>
              <n-descriptions-item :label="t('oobe.key_status')">
                <n-tag :type="keyInfo.isActive ? 'success' : 'error'" size="small">
                  {{ keyInfo.isActive ? t('oobe.active') : t('oobe.inactive') }}
                </n-tag>
              </n-descriptions-item>
              <n-descriptions-item :label="t('oobe.key_expires')">
                {{ keyInfo.expiresAt ? new Date(keyInfo.expiresAt).toLocaleDateString() : t('oobe.permanent') }}
              </n-descriptions-item>
              <n-descriptions-item :label="t('oobe.key_usage')">
                {{ keyInfo.usageCount }} / {{ keyInfo.totalUsage }}
              </n-descriptions-item>
            </n-descriptions>
          </template>

          <n-divider/>
          <n-text strong>{{ t('settings.change_key') }}</n-text>
          <n-input-group>
            <n-input
                v-model:value="newKey"
                :placeholder="t('settings.new_key_placeholder')"
                style="flex: 1"
            />
            <n-button
                v-if="!newKeyVerified"
                type="info"
                @click="verifyNewKey"
            >
              {{ t('settings.verify') }}
            </n-button>
            <n-button
                v-else
                type="primary"
                @click="saveNewKey"
            >
              {{ t('settings.save') }}
            </n-button>
          </n-input-group>
        </n-space>
      </n-card>

      <!-- Steam Config -->
      <n-card :title="t('settings.steam_config')">
        <n-space :size="12" vertical>
          <n-form-item :label="t('settings.steam_path_label')">
            <n-input-group>
              <n-input
                  v-model:value="steamPath"
                  :placeholder="t('settings.steam_path_placeholder')"
                  style="flex: 1"
              />
              <n-button @click="detectSteamPath">{{ t('settings.detect') }}</n-button>
            </n-input-group>
          </n-form-item>
          <n-text depth="3" style="font-size: 12px;">{{ t('settings.steam_path_helper') }}</n-text>
        </n-space>
      </n-card>

      <!-- App Config -->
      <n-card :title="t('settings.app_config')">
        <n-form-item :label="t('settings.language')">
          <n-radio-group v-model:value="language">
            <n-radio-button value="zh">{{ t('settings.lang_zh') }}</n-radio-button>
            <n-radio-button value="en">{{ t('settings.lang_en') }}</n-radio-button>
          </n-radio-group>
        </n-form-item>
      </n-card>

      <!-- About Section -->
      <n-card :title="t('settings.about')">
        <n-space :size="8" vertical>
          <n-text strong>Onekey v3.0.0</n-text>
          <n-text depth="3">{{ t('about.project_subtitle') }}</n-text>
          <n-divider style="margin: 8px 0"/>
          <n-text depth="3">{{ t('about.tech_backend') }}: {{ t('about.tech_backend_val') }}</n-text>
          <n-text depth="3">{{ t('about.tech_frontend') }}: Vue 3 / TypeScript / Vite / Naive UI</n-text>
          <n-text depth="3">{{ t('about.tech_tools') }}: {{ t('about.tech_tools_val') }}</n-text>
          <n-divider style="margin: 8px 0"/>
          <n-space :size="12" align="center">
            <n-button :loading="updateChecking" size="small" @click="checkForUpdate">
              {{ t('update.check') }}
            </n-button>
            <n-text v-if="updateInfo && updateInfo.has_update" type="warning">
              {{ t('update.new_version', {version: updateInfo.latest_version}) }}
            </n-text>
            <n-text v-else-if="updateChecked" depth="3">{{ t('update.up_to_date') }}</n-text>
          </n-space>
          <template v-if="updateInfo && updateInfo.has_update">
            <n-alert :title="t('update.title')" style="margin-top: 8px;" type="warning">
              <n-space :size="4" vertical>
                <n-text>{{ t('update.current') }}: v{{ updateInfo.current_version }}</n-text>
                <n-text>{{ t('update.latest') }}: v{{ updateInfo.latest_version }}</n-text>
                <n-text v-if="updateInfo.changelog">{{ t('update.changelog') }}: {{ updateInfo.changelog }}</n-text>
                <n-button
                    v-if="updateInfo.download_url"
                    :href="updateInfo.download_url"
                    size="small"
                    style="margin-top: 4px;"
                    tag="a"
                    target="_blank"
                    type="primary"
                >
                  {{ t('update.download') }}
                </n-button>
              </n-space>
            </n-alert>
          </template>
          <n-divider style="margin: 8px 0"/>
          <n-text depth="3">{{ t('about.copyright') }}</n-text>
        </n-space>
      </n-card>
    </n-space>
  </div>
</template>

<script lang="ts" setup>
import {onMounted, ref, watch} from 'vue'
import {useMessage} from 'naive-ui'
import {useI18n} from '../i18n'
import {CheckUpdate, GetConfig, GetDetailedConfig, UpdateConfig, VerifyKey} from '../../wailsjs/go/main/App'

const {t, setLanguage: setI18nLang} = useI18n()
const message = useMessage()

const detailedConfig = ref<any>(null)
const keyInfo = ref<any>(null)
const keyLoading = ref(true)
const newKey = ref('')
const newKeyVerified = ref(false)
const steamPath = ref('')
const language = ref('zh')
const updateInfo = ref<any>(null)
const updateChecking = ref(false)
const updateChecked = ref(false)

onMounted(async () => {
  try {
    const resp = await GetDetailedConfig()
    if (resp.success) {
      detailedConfig.value = resp.config
      steamPath.value = resp.config.steam_path || ''
      language.value = resp.config.language || 'zh'
      // Fetch key details
      if (resp.config.key) {
        try {
          const result = await VerifyKey(resp.config.key)
          if (result.info) keyInfo.value = result.info
        } catch (e) {
        }
      }
    }
  } catch (e) {
  }
  keyLoading.value = false
})

// Language: save immediately on change
watch(language, async (val) => {
  setI18nLang(val)
  if (!detailedConfig.value) return
  try {
    await UpdateConfig({
      key: detailedConfig.value.key || '',
      steam_path: steamPath.value,
      debug_mode: false,
      logging_files: false,
      show_console: false,
      language: val,
    })
  } catch (e) {
  }
})

async function checkForUpdate() {
  updateChecking.value = true
  updateChecked.value = false
  try {
    const info = await CheckUpdate()
    updateInfo.value = info
    updateChecked.value = true
    if (info.has_update) {
      message.info(t('update.new_version', {version: info.latest_version}))
    } else {
      message.success(t('update.up_to_date'))
    }
  } catch (e) {
    message.error(t('update.check_failed'))
  } finally {
    updateChecking.value = false
  }
}

async function verifyNewKey() {
  const key = newKey.value.trim()
  if (!key) return
  try {
    const result = await VerifyKey(key)
    if (result.key && result.info) {
      newKeyVerified.value = true
      message.success(t('oobe.verify_success'))
    } else {
      message.error(t('oobe.verify_fail'))
    }
  } catch (e) {
    message.error(t('oobe.verify_error'))
  }
}

async function saveNewKey() {
  const key = newKey.value.trim()
  try {
    const result = await UpdateConfig({
      key,
      steam_path: steamPath.value,
      debug_mode: false,
      logging_files: false,
      show_console: false,
      language: language.value,
    })
    if (result.success) {
      message.success(result.message)
    } else {
      message.error(result.message)
    }
  } catch (e: any) {
    message.error(e.message || 'Error')
  }
  newKeyVerified.value = false
  newKey.value = ''
  // Refresh key info
  const resp = await GetDetailedConfig()
  if (resp.success) {
    detailedConfig.value = resp.config
    if (resp.config.key) {
      try {
        const info = await VerifyKey(resp.config.key)
        if (info.info) keyInfo.value = info.info
      } catch (e) {
      }
    }
  }
}

async function detectSteamPath() {
  try {
    const resp = await GetConfig()
    if (resp.success && resp.config.steam_path) {
      steamPath.value = resp.config.steam_path
      message.success('Steam: ' + resp.config.steam_path)
    } else {
      message.error(t('home.steam_path_not_found'))
    }
  } catch (e) {
  }
}
</script>
