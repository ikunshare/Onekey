<template>
  <div>
    <!-- Search bar -->
    <n-space vertical :size="16">

      <!-- Search bar -->
      <n-input-group>
        <n-input
          v-model:value="store.searchTerm"
          :placeholder="t('home.search_placeholder')"
          clearable
          size="large"
          @keypress.enter="doSearch"
        />
        <n-button type="primary" size="large" @click="doSearch" :loading="searching">
          {{ t('home.search_button') }}
        </n-button>
      </n-input-group>

      <!-- Config alert -->
      <n-alert v-if="!configData.steam_path && !configLoading" type="warning" :title="t('home.steam_path_not_found')">
        {{ t('home.steam_path_hint') }}
      </n-alert>

      <!-- Search results -->
      <n-spin :show="searching">
        <n-empty v-if="!searching && store.searchResults.length === 0 && store.searchDone" :description="t('home.no_results')" />

        <n-grid v-if="store.searchResults.length > 0" :cols="'1 600:2 900:3'" :x-gap="12" :y-gap="12">
          <n-gi v-for="item in store.searchResults" :key="item.id">
            <n-card hoverable size="small">
              <template #cover>
                <img
                  :src="item.tiny_image"
                  :alt="item.name"
                  style="width: 100%; display: block;"
                  loading="lazy"
                />
              </template>
              <n-space vertical :size="8">
                <n-text strong>{{ item.name }}</n-text>
                <n-space :size="8" align="center">
                  <n-tag v-if="item.platforms?.windows" size="small" :bordered="false">Win</n-tag>
                  <n-tag v-if="item.platforms?.mac" size="small" :bordered="false">Mac</n-tag>
                  <n-tag v-if="item.platforms?.linux" size="small" :bordered="false">Linux</n-tag>
                  <n-text v-if="item.price" depth="3" style="font-size: 12px;">
                    <template v-if="item.price.final === 0">{{ t('home.free') }}</template>
                    <template v-else>{{ formatPrice(item.price.final) }}</template>
                  </n-text>
                  <n-text v-else depth="3" style="font-size: 12px;">{{ t('home.free') }}</n-text>
                </n-space>
                <n-space :size="8">
                  <n-button
                    type="primary"
                    size="small"
                    @click="unlockGame(item)"
                    :disabled="store.isRunning"
                  >
                    {{ t('home.unlock') }}
                  </n-button>
                  <n-button
                    size="small"
                    @click="addToLibrary(item)"
                  >
                    {{ t('home.add_to_library') }}
                  </n-button>
                </n-space>
              </n-space>
            </n-card>
          </n-gi>
        </n-grid>
      </n-spin>
    </n-space>

    <!-- Unlock progress drawer -->
    <n-drawer v-model:show="showProgress" :width="400" placement="right">
      <n-drawer-content :title="t('home.unlock_progress')">
        <n-timeline>
          <n-timeline-item
            v-for="(log, i) in store.logs"
            :key="i"
            :type="log.type === 'error' ? 'error' : log.type === 'warning' ? 'warning' : 'success'"
            :title="log.message"
            :time="log.timestamp"
          />
        </n-timeline>
        <n-empty v-if="store.logs.length === 0" :description="t('home.log_placeholder')" />
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { useAppStore } from '../stores/app'
import { useGamesStore } from '../stores/games'
import { useI18n } from '../i18n'
import { GetConfig, StartUnlock, SearchStore } from '../../wailsjs/go/main/App'

const store = useAppStore()
const gamesStore = useGamesStore()
const { t } = useI18n()
const router = useRouter()
const message = useMessage()

const searching = ref(false)
const configLoading = ref(true)
const configData = ref({ steam_path: '', debug_mode: false })
const showProgress = ref(false)

onMounted(async () => {
  try {
    const resp = await GetConfig()
    if (resp.success) {
      configData.value = resp.config
      store.config = resp.config
    }
  } catch (e) {}
  configLoading.value = false
})

async function doSearch() {
  const term = store.searchTerm.trim()
  if (!term) return
  searching.value = true
  store.searchDone = false
  try {
    const result = await SearchStore(term)
    store.searchResults = result.items || []
  } catch (e: any) {
    message.error(e.message || 'Search failed')
    store.searchResults = []
  } finally {
    searching.value = false
    store.searchDone = true
  }
}

function formatPrice(cents: number) {
  return '\u00a5' + (cents / 100).toFixed(2)
}

async function unlockGame(item: any) {
  if (store.isRunning) {
    message.warning(t('home.task_running'))
    return
  }
  // Also add to library
  await gamesStore.addGame(item.id, item.name, item.tiny_image || '', item.type || 'app')
  store.setTaskStatus('running')
  store.clearLogs()
  showProgress.value = true
  try {
    const resp = await StartUnlock(String(item.id))
    if (resp.success) {
      message.success(t('home.task_started'))
    } else {
      store.setTaskStatus('idle')
      message.error(resp.message)
    }
  } catch (e: any) {
    store.setTaskStatus('idle')
    message.error(e.message || t('home.task_failed'))
  }
}

async function addToLibrary(item: any) {
  const result = await gamesStore.addGame(item.id, item.name, item.tiny_image || '', item.type || 'app')
  message.success(result.message || t('home.added_to_library'))
}
</script>
