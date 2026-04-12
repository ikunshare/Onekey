<template>
  <div>
    <!-- App Bar -->
    <header class="app-bar">
      <div class="app-bar-content">
        <span class="material-icons app-icon">games</span>
        <h1 class="app-title">Onekey</h1>
        <button type="button" class="theme-toggle" @click="toggleTheme" title="切换主题">
          <span class="material-icons">{{ isDark ? 'dark_mode' : 'light_mode' }}</span>
        </button>
        <router-link to="/settings" class="btn btn-text settings-link">
          <span class="material-icons">settings</span>
          <span class="settings-text">{{ t('nav.settings') }}</span>
        </router-link>
        <router-link to="/about" class="btn btn-text about-link">
          <span class="material-icons">info</span>
          <span class="about-text">{{ t('nav.about') }}</span>
        </router-link>
      </div>
    </header>

    <main class="main-content">
      <!-- Config Status Card -->
      <div class="card config-card">
        <div class="card-header">
          <span class="material-icons">settings</span>
          <h2>{{ t('home.config_status') }}</h2>
        </div>
        <div class="card-content">
          <div class="config-status">
            <div v-if="configLoading" class="loading">{{ t('home.checking_config') }}</div>
            <template v-else>
              <div class="status-item" v-if="configData.steam_path">
                <span class="material-icons status-icon success">check_circle</span>
                <span class="status-text">{{ t('home.steam_path') }}: {{ configData.steam_path }}</span>
              </div>
              <div class="status-item" v-else>
                <span class="material-icons status-icon error">error</span>
                <span class="status-text">{{ t('home.steam_path_not_found') }}</span>
              </div>
              <div class="status-item" v-if="configData.debug_mode">
                <span class="material-icons status-icon warning">bug_report</span>
                <span class="status-text">{{ t('home.debug_mode_on') }}</span>
              </div>
            </template>
          </div>
        </div>
      </div>

      <!-- Unlock Card -->
      <div class="card unlock-card">
        <div class="card-header">
          <span class="material-icons">lock_open</span>
          <h2>{{ t('home.unlock_title') }}</h2>
        </div>
        <div class="card-content">
          <form @submit.prevent="startUnlock" class="unlock-form">
            <div class="input-group">
              <label for="appId" class="input-label">{{ t('home.app_id_label') }}</label>
              <input
                type="text"
                id="appId"
                v-model="appId"
                class="text-field"
                :placeholder="t('home.app_id_placeholder')"
                inputmode="numeric"
                autocomplete="off"
                autofocus
                :disabled="store.isRunning"
                required
              />
              <div class="input-helper">{{ t('home.app_id_helper') }}</div>
            </div>

            <div class="input-group">
              <label class="checkbox-item">
                <input type="checkbox" v-model="includeDLC" :disabled="store.isRunning" />
                <span class="checkbox-button"></span>
                <span class="checkbox-label">{{ t('home.dlc_label') }}</span>
              </label>
              <div class="input-helper">{{ t('home.dlc_helper') }}</div>
            </div>

            <div class="button-group">
              <button type="submit" class="btn btn-primary" :disabled="store.isRunning">
                <span class="material-icons">{{ store.isRunning ? 'hourglass_empty' : 'play_arrow' }}</span>
                {{ store.isRunning ? t('home.running') : t('home.start_unlock') }}
              </button>
              <button type="button" class="btn btn-secondary" :disabled="store.isRunning" @click="resetForm">
                <span class="material-icons">refresh</span>
                {{ t('home.reset') }}
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Log Card -->
      <div class="card progress-card">
        <div class="card-header">
          <span class="material-icons">timeline</span>
          <h2>{{ t('home.log_title') }}</h2>
          <div class="card-actions">
            <button class="btn btn-text" @click="store.clearLogs()">
              <span class="material-icons">clear_all</span>
              {{ t('home.clear_log') }}
            </button>
          </div>
        </div>
        <div class="card-content">
          <div class="progress-container" ref="logContainer">
            <div v-if="store.logs.length === 0" class="progress-placeholder">
              <span class="material-icons">info</span>
              <p>{{ t('home.log_placeholder') }}</p>
            </div>
            <div v-for="(log, i) in store.logs" :key="i" :class="['log-entry', log.type]">
              <span class="log-timestamp">{{ log.timestamp }}</span>
              <span class="log-message">{{ log.message }}</span>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, inject, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '../stores/app'
import { useI18n } from '../i18n'
import { GetConfig, StartUnlock, GetTaskStatus } from '../../wailsjs/go/main/App'
import { EventsOn, EventsOff } from '../../wailsjs/runtime/runtime'

const store = useAppStore()
const { t } = useI18n()
const router = useRouter()
const isDark = inject<any>('isDark')
const toggleTheme = inject<any>('toggleTheme')
const showSnackbar = inject<any>('showSnackbar')

const appId = ref('')
const includeDLC = ref(false)
const configLoading = ref(true)
const configData = ref({ steam_path: '', debug_mode: false })
const logContainer = ref<HTMLElement>()

let pollTimer: ReturnType<typeof setInterval> | null = null

onMounted(async () => {
  // Check config & redirect to OOBE if needed
  try {
    const resp = await GetConfig()
    if (resp.success) {
      configData.value = resp.config
      store.config = resp.config
    }
  } catch (e) {
    showSnackbar(t('home.cannot_connect'), 'error')
  }
  configLoading.value = false

  // Listen for task progress events from Go
  EventsOn('task_progress', (data: any) => {
    store.addLog(data.type, data.message)
    nextTick(() => {
      if (logContainer.value) {
        logContainer.value.scrollTop = logContainer.value.scrollHeight
      }
    })
  })

  EventsOn('task_done', (result: any) => {
    if (result && result.success) {
      store.setTaskStatus('completed')
      showSnackbar(result.message, 'success')
    } else if (result) {
      store.setTaskStatus('error')
      showSnackbar(result.message, 'error')
    }
    store.setTaskStatus('idle')
  })
})

onUnmounted(() => {
  EventsOff('task_progress')
  EventsOff('task_done')
  if (pollTimer) clearInterval(pollTimer)
})

async function startUnlock() {
  if (store.isRunning) {
    showSnackbar(t('home.task_running'), 'warning')
    return
  }

  const id = appId.value.trim()
  if (!id) {
    showSnackbar(t('home.enter_appid'), 'error')
    return
  }
  if (!/^[\d-]+$/.test(id)) {
    showSnackbar(t('home.invalid_appid'), 'error')
    return
  }

  store.setTaskStatus('running')
  store.clearLogs()
  store.addLog('info', `开始处理游戏 ${id}...`)

  try {
    const resp = await StartUnlock(id, includeDLC.value)
    if (resp.success) {
      showSnackbar(t('home.task_started'), 'success')
    } else {
      store.setTaskStatus('idle')
      showSnackbar(resp.message, 'error')
      store.addLog('error', resp.message)
    }
  } catch (e: any) {
    store.setTaskStatus('idle')
    showSnackbar(t('home.task_failed'), 'error')
    store.addLog('error', e.message || t('home.task_failed'))
  }
}

function resetForm() {
  if (store.isRunning) {
    showSnackbar(t('home.cannot_reset_running'), 'warning')
    return
  }
  appId.value = ''
  includeDLC.value = false
  store.clearLogs()
  showSnackbar(t('home.form_reset'), 'success')
}
</script>
