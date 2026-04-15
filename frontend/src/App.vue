<template>
  <n-config-provider :theme="theme" :theme-overrides="themeOverrides">
    <n-message-provider>
      <n-dialog-provider>
        <!-- OOBE: full-screen, no sidebar -->
        <template v-if="route.name === 'oobe'">
          <div class="titlebar" style="--wails-draggable: drag;">
            <div class="titlebar-drag"></div>
            <div class="titlebar-controls">
              <button class="titlebar-btn" @click="WindowMinimise">&#x2013;</button>
              <button class="titlebar-btn" @click="WindowToggleMaximise">&#9633;</button>
              <button class="titlebar-btn titlebar-close" @click="Quit">&#10005;</button>
            </div>
          </div>
          <router-view style="height: calc(100vh - 32px);" />
        </template>

        <!-- Main layout with sidebar -->
        <template v-else>
          <n-layout has-sider style="height: 100vh">
            <n-layout-sider
              bordered
              collapse-mode="width"
              :collapsed-width="64"
              :width="220"
              :collapsed="collapsed"
              show-trigger
              @collapse="collapsed = true"
              @expand="collapsed = false"
            >
              <div class="sider-content">
                <div class="sider-top">
                  <div class="sider-logo" v-if="!collapsed">
                    <n-text strong style="font-size: 18px;">Onekey</n-text>
                  </div>
                  <n-menu
                    :collapsed="collapsed"
                    :collapsed-width="64"
                    :collapsed-icon-size="22"
                    :options="menuOptions"
                    :value="activeKey"
                    @update:value="handleMenuSelect"
                  />
                </div>
                <div class="sider-actions">
                  <n-divider style="margin: 8px 0" />
                  <n-button quaternary block size="small" @click="showAnnouncementModal">
                    <template #icon><n-icon :component="MegaphoneOutline" /></template>
                    <span v-if="!collapsed">{{ t('sidebar.announcements') }}</span>
                  </n-button>
                  <n-button quaternary block size="small" @click="handleLoadKernel">
                    <template #icon><n-icon :component="DownloadOutline" /></template>
                    <span v-if="!collapsed">{{ t('sidebar.load_kernel') }}</span>
                  </n-button>
                  <n-button quaternary block size="small" @click="showKernelSettingsModal">
                    <template #icon><n-icon :component="CogOutline" /></template>
                    <span v-if="!collapsed">{{ t('kernel_settings.title') }}</span>
                  </n-button>
                  <n-button quaternary block size="small" @click="handlePatchVDF">
                    <template #icon><n-icon :component="BuildOutline" /></template>
                    <span v-if="!collapsed">{{ t('sidebar.patch_vdf') }}</span>
                  </n-button>
                  <n-button quaternary block size="small" @click="handleRestartSteam">
                    <template #icon><n-icon :component="RefreshOutline" /></template>
                    <span v-if="!collapsed">{{ t('sidebar.restart_steam') }}</span>
                  </n-button>
                  <n-button quaternary block size="small" @click="toggleTheme">
                    <template #icon><n-icon :component="isDark ? SunnyOutline : MoonOutline" /></template>
                    <span v-if="!collapsed">{{ isDark ? t('sidebar.light_mode') : t('sidebar.dark_mode') }}</span>
                  </n-button>
                </div>
              </div>
            </n-layout-sider>

            <n-layout>
              <!-- Title bar -->
              <div class="titlebar" style="--wails-draggable: drag;">
                <div class="titlebar-drag"></div>
                <div class="titlebar-controls">
                  <button class="titlebar-btn" @click="WindowMinimise">&#x2013;</button>
                  <button class="titlebar-btn" @click="WindowToggleMaximise">&#9633;</button>
                  <button class="titlebar-btn titlebar-close" @click="Quit">&#10005;</button>
                </div>
              </div>
              <n-layout-content content-style="padding: 24px;" style="height: calc(100vh - 32px);" :native-scrollbar="false">
                <router-view />
              </n-layout-content>
            </n-layout>
          </n-layout>
        </template>
        <!-- Announcement Modal -->
        <n-modal v-model:show="annModalVisible" preset="card" :title="t('announcement.title')" style="max-width: 600px;" :bordered="false" :segmented="{ content: true }">
          <div v-if="annList.length === 0" style="text-align: center; padding: 24px;">
            <n-text depth="3">{{ t('announcement.empty') }}</n-text>
          </div>
          <n-space v-else vertical :size="16">
            <n-card v-for="ann in annList" :key="ann.id" size="small" :bordered="true">
              <template #header>
                <n-space align="center" :size="8">
                  <span>{{ ann.title }}</span>
                  <n-tag size="tiny" :bordered="false">{{ ann.author }}</n-tag>
                </n-space>
              </template>
              <template #header-extra>
                <n-text depth="3" style="font-size: 12px;">{{ formatDate(ann.createdAt) }}</n-text>
              </template>
              <div class="md-content" v-html="renderMarkdown(ann.content)"></div>
            </n-card>
          </n-space>
        </n-modal>
        <!-- Kernel Settings Modal -->
        <n-modal v-model:show="kernelSettingsVisible" preset="card" :title="t('kernel_settings.title')" style="max-width: 420px;" :bordered="false">
          <n-spin :show="kernelSettingsLoading">
            <n-space vertical :size="16">
              <n-space align="center" justify="space-between">
                <n-text>{{ t('kernel_settings.activate_unlock_mode') }}</n-text>
                <n-switch v-model:value="kernelSettings.activate_unlock_mode" @update:value="saveKernelSettings" />
              </n-space>
              <n-space align="center" justify="space-between">
                <n-text>{{ t('kernel_settings.always_stay_unlocked') }}</n-text>
                <n-switch v-model:value="kernelSettings.always_stay_unlocked" @update:value="saveKernelSettings" />
              </n-space>
              <n-space align="center" justify="space-between">
                <n-text>{{ t('kernel_settings.not_unlock_depot') }}</n-text>
                <n-switch v-model:value="kernelSettings.not_unlock_depot" @update:value="saveKernelSettings" />
              </n-space>
            </n-space>
          </n-spin>
        </n-modal>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { ref, computed, h, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { darkTheme, type GlobalThemeOverrides, type MenuOption } from 'naive-ui'
import { createDiscreteApi } from 'naive-ui'
import {
  HomeOutline,
  GameControllerOutline,
  SettingsOutline,
  DownloadOutline,
  BuildOutline,
  RefreshOutline,
  SunnyOutline,
  MoonOutline,
  MegaphoneOutline,
  CogOutline,
} from '@vicons/ionicons5'
import { NIcon } from 'naive-ui'
import { useI18n } from './i18n'
import { useAppStore } from './stores/app'
import { RestartSteam, LoadKernel, PatchVDF, GetAnnouncements, GetKernelSettings, SetKernelSettings, CheckUpdate, GetDetailedConfig } from '../wailsjs/go/main/App'
import { WindowMinimise, WindowToggleMaximise, Quit, EventsOn, BrowserOpenURL } from '../wailsjs/runtime/runtime'
import { marked } from 'marked'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const store = useAppStore()

// Theme
const isDark = ref(localStorage.getItem('theme') === 'dark')
const theme = computed(() => isDark.value ? darkTheme : null)
const themeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#6750a4',
    primaryColorHover: '#7c6bb5',
    primaryColorPressed: '#5a3f96',
    fontFamily: '"LXGW WenKai Mono", sans-serif',
  },
}

// Discrete API for message/dialog — App.vue renders the providers itself,
// so useMessage()/useDialog() can't inject from them. createDiscreteApi
// creates standalone instances that work anywhere.
const { message, dialog } = createDiscreteApi(
  ['message', 'dialog'],
  {
    configProviderProps: computed(() => ({
      theme: isDark.value ? darkTheme : undefined,
      themeOverrides,
    })),
  }
)

function toggleTheme() {
  isDark.value = !isDark.value
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}

// Sidebar collapse
const collapsed = ref(false)

// Menu
function renderIcon(icon: any) {
  return () => h(NIcon, null, { default: () => h(icon) })
}

const menuOptions: MenuOption[] = [
  { label: () => t('nav.home'), key: 'home', icon: renderIcon(HomeOutline) },
  { label: () => t('nav.games'), key: 'games', icon: renderIcon(GameControllerOutline) },
  { label: () => t('nav.settings'), key: 'settings', icon: renderIcon(SettingsOutline) },
]

const activeKey = computed(() => {
  const name = route.name as string
  return name || 'home'
})

function handleMenuSelect(key: string) {
  if (key === 'home') router.push('/')
  else router.push(`/${key}`)
}

// Sidebar actions
const kernelLoading = ref(false)

function handleLoadKernel() {
  dialog.warning({
    title: t('kernel.confirm_title'),
    content: t('kernel.confirm_content'),
    positiveText: t('common.confirm'),
    negativeText: t('common.cancel'),
    onPositiveClick: async () => {
      kernelLoading.value = true
      try {
        const result = await LoadKernel()
        if (result.success) {
          message.success(result.message)
        } else {
          message.error(result.message)
        }
      } catch (e: any) {
        message.error(e.message || t('kernel.failed'))
      } finally {
        kernelLoading.value = false
      }
    },
  })
}

function handlePatchVDF() {
  dialog.warning({
    title: t('patch.confirm_title'),
    content: t('patch.confirm_content'),
    positiveText: t('common.confirm'),
    negativeText: t('common.cancel'),
    onPositiveClick: async () => {
      try {
        const result = await PatchVDF()
        if (result.success) {
          message.success(result.message)
        } else {
          message.error(result.message)
        }
      } catch (e: any) {
        message.error(e.message || t('patch.failed'))
      }
    },
  })
}

function handleRestartSteam() {
  dialog.warning({
    title: t('sidebar.restart_confirm_title'),
    content: t('sidebar.restart_confirm'),
    positiveText: t('common.confirm'),
    negativeText: t('common.cancel'),
    onPositiveClick: async () => {
      try {
        const result = await RestartSteam()
        if (result.success) {
          message.success(result.message)
        } else {
          message.error(result.message)
        }
      } catch (e: any) {
        message.error(e.message || 'Failed')
      }
    },
  })
}

// --- Announcements ---
const annModalVisible = ref(false)
const annList = ref<any[]>([])

function renderMarkdown(content: string): string {
  return marked.parse(content, { async: false }) as string
}

function formatDate(iso: string): string {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleDateString()
}

async function fetchAnnouncements() {
  try {
    const resp = await GetAnnouncements()
    if (resp.success && resp.announcements) {
      annList.value = resp.announcements
    }
  } catch (e) {}
}

function showAnnouncementModal() {
  fetchAnnouncements()
  annModalVisible.value = true
}

// --- Kernel Settings ---
const kernelSettingsVisible = ref(false)
const kernelSettingsLoading = ref(false)
const kernelSettings = ref({
  activate_unlock_mode: false,
  always_stay_unlocked: false,
  not_unlock_depot: false,
})

async function showKernelSettingsModal() {
  kernelSettingsVisible.value = true
  kernelSettingsLoading.value = true
  try {
    const resp = await GetKernelSettings()
    if (resp.success) {
      kernelSettings.value = resp.settings
    } else {
      message.error(resp.message || t('kernel_settings.load_failed'))
    }
  } catch (e) {
    message.error(t('kernel_settings.load_failed'))
  } finally {
    kernelSettingsLoading.value = false
  }
}

async function saveKernelSettings() {
  try {
    const resp = await SetKernelSettings(kernelSettings.value)
    if (!resp.success) {
      message.error(resp.message)
    }
  } catch (e: any) {
    message.error(e.message || 'Error')
  }
}

onMounted(async () => {
  // OOBE check: redirect to setup if no key configured
  if (route.name !== 'oobe') {
    try {
      const cfg = await GetDetailedConfig()
      if (cfg.success && (!cfg.config.key || cfg.config.key === '')) {
        router.push('/oobe')
        return
      }
    } catch (e) {
      router.push('/oobe')
      return
    }
  }

  // Global task event listeners — persist across route changes
  EventsOn('task_progress', (data: any) => {
    store.addLog(data.type, data.message)
  })
  EventsOn('task_done', (result: any) => {
    if (result && result.success) {
      store.setTaskStatus('completed')
      message.success(result.message)
    } else if (result) {
      store.setTaskStatus('error')
      message.error(result.message)
    }
    store.setTaskStatus('idle')
  })

  await fetchAnnouncements()
  if (annList.value.length > 0) {
    // Find the latest announcement (highest id)
    const latest = annList.value.reduce((a, b) => (a.id > b.id ? a : b))
    const lastSeenId = localStorage.getItem('lastSeenAnnouncementId')
    if (String(latest.id) !== lastSeenId) {
      // Only show the latest new one
      annList.value = [latest]
      annModalVisible.value = true
      localStorage.setItem('lastSeenAnnouncementId', String(latest.id))
    }
  }

  // Auto check for updates on startup
  try {
    const info = await CheckUpdate()
    if (info && info.has_update) {
      dialog.info({
        title: t('update.title'),
        content: () =>
          h('div', {}, [
            h('p', {}, `${t('update.current')}: v${info.current_version}`),
            h('p', {}, `${t('update.latest')}: v${info.latest_version}`),
            info.changelog ? h('p', {}, `${t('update.changelog')}: ${info.changelog}`) : null,
          ]),
        positiveText: info.download_url ? t('update.download') : undefined,
        negativeText: t('common.cancel'),
        onPositiveClick: () => {
          if (info.download_url) {
            BrowserOpenURL(info.download_url)
          }
        },
      })
    }
  } catch (e) {}
})
</script>

<style>
body {
  margin: 0;
  padding: 0;
  font-family: 'LXGW WenKai Mono', sans-serif;
  overflow: hidden;
}

.md-content h1, .md-content h2, .md-content h3,
.md-content h4, .md-content h5, .md-content h6 {
  margin: 8px 0 4px;
}
.md-content h1 { font-size: 1.4em; }
.md-content h2 { font-size: 1.2em; }
.md-content h3 { font-size: 1.1em; }
.md-content p { margin: 4px 0; }
.md-content ul, .md-content ol { padding-left: 20px; margin: 4px 0; }
.md-content code {
  background: rgba(128, 128, 128, 0.15);
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 0.9em;
}
.md-content pre {
  background: rgba(128, 128, 128, 0.1);
  padding: 8px 12px;
  border-radius: 6px;
  overflow-x: auto;
}
.md-content pre code {
  background: none;
  padding: 0;
}
.md-content blockquote {
  border-left: 3px solid #6750a4;
  margin: 4px 0;
  padding: 4px 12px;
  opacity: 0.85;
}
.md-content a { color: #6750a4; }
.md-content img { max-width: 100%; border-radius: 6px; }
</style>

<style scoped>
.titlebar {
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  user-select: none;
  flex-shrink: 0;
}

.titlebar-drag {
  flex: 1;
  height: 100%;
}

.titlebar-controls {
  display: flex;
  height: 100%;
  --wails-draggable: none;
}

.titlebar-btn {
  width: 46px;
  height: 100%;
  border: none;
  background: transparent;
  color: inherit;
  font-size: 13px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
}

.titlebar-btn:hover {
  background: rgba(128, 128, 128, 0.2);
}

.titlebar-close:hover {
  background: #e81123;
  color: white;
}

.sider-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.sider-top {
  flex: 1;
}

.sider-logo {
  padding: 16px 20px 8px;
}

.sider-actions {
  padding: 4px 8px 12px;
}
</style>
