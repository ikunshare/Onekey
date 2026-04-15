<template>
  <div>
    <n-page-header :subtitle="t('games.subtitle')" :title="t('games.title')">
      <template #extra>
        <n-button :loading="gamesStore.loading" size="small" @click="fetchGames">
          {{ t('games.refresh') }}
        </n-button>
      </template>
    </n-page-header>

    <n-spin :show="gamesStore.loading" style="margin-top: 16px">
      <n-empty v-if="games.length === 0 && !gamesStore.loading" :description="t('games.empty')"
               style="margin-top: 48px"/>

      <n-grid v-else :cols="'1 600:2 900:3'" :x-gap="12" :y-gap="12" style="margin-top: 16px">
        <n-gi v-for="game in games" :key="game.app_id">
          <n-card hoverable size="small">
            <template #cover>
              <img
                  v-if="game.tiny_image"
                  :alt="game.name"
                  :src="game.tiny_image"
                  loading="lazy"
                  style="width: 100%; display: block;"
              />
            </template>
            <n-space :size="8" vertical>
              <n-text strong>{{ game.name }}</n-text>
              <n-space :size="8" align="center">
                <n-tag v-if="game.unlocked" size="small" type="success">{{ t('games.unlocked') }}</n-tag>
                <n-tag v-else size="small">{{ t('games.not_unlocked') }}</n-tag>
                <n-text v-if="game.depot_count" depth="3" style="font-size: 12px;">
                  {{ game.depot_count }} depots
                </n-text>
                <n-text v-if="game.dlc_count" depth="3" style="font-size: 12px;">
                  {{ game.dlc_count }} DLCs
                </n-text>
              </n-space>
              <n-space :size="8">
                <n-button :disabled="appStore.isRunning" size="small" type="primary" @click="unlockGame(game)">
                  {{ game.unlocked ? t('games.re_unlock') : t('games.unlock') }}
                </n-button>
                <n-button size="small" @click="showDepots(game)">
                  {{ t('games.depots') }}
                </n-button>
                <n-button v-if="game.dlc_count > 0" size="small" @click="goToDLC(game)">
                  DLC ({{ game.dlc_count }})
                </n-button>
                <n-popconfirm @positive-click="removeGame(game.app_id)">
                  <template #trigger>
                    <n-button quaternary size="small" type="error">
                      {{ t('games.remove') }}
                    </n-button>
                  </template>
                  {{ t('games.remove_confirm') }}
                </n-popconfirm>
              </n-space>
            </n-space>
          </n-card>
        </n-gi>
      </n-grid>
    </n-spin>

    <!-- Depot Drawer -->
    <n-drawer v-model:show="depotDrawerVisible" :width="480" placement="right">
      <n-drawer-content :title="depotGameName + ' - Depots'">
        <n-spin :show="depotLoading">
          <n-empty v-if="!depotLoading && depotList.length === 0" :description="t('games.no_depot_data')"/>
          <n-table v-else :bordered="false" :single-line="false" size="small">
            <thead>
            <tr>
              <th>Depot ID</th>
              <th>Manifest ID</th>
              <th>Depot Key</th>
            </tr>
            </thead>
            <tbody>
            <tr v-for="d in depotList" :key="d.depot_id">
              <td>
                <n-text code>{{ d.depot_id }}</n-text>
              </td>
              <td>
                <n-text depth="3" style="font-size: 12px;">{{ d.manifest_id || '-' }}</n-text>
              </td>
              <td>
                <n-text depth="3" style="font-size: 12px; word-break: break-all;">{{ d.depot_key || '-' }}</n-text>
              </td>
            </tr>
            </tbody>
          </n-table>
        </n-spin>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script lang="ts" setup>
import {computed, onMounted, ref} from 'vue'
import {useRouter} from 'vue-router'
import {useMessage} from 'naive-ui'
import {useI18n} from '../i18n'
import {useGamesStore} from '../stores/games'
import {useAppStore} from '../stores/app'
import {GetGameDetail, StartUnlock} from '../../wailsjs/go/main/App'

const {t} = useI18n()
const message = useMessage()
const router = useRouter()
const gamesStore = useGamesStore()
const appStore = useAppStore()

const games = computed(() => gamesStore.games)

// Depot drawer state
const depotDrawerVisible = ref(false)
const depotGameName = ref('')
const depotList = ref<any[]>([])
const depotLoading = ref(false)

onMounted(() => {
  fetchGames()
})

async function fetchGames() {
  await gamesStore.fetchGames()
}

async function showDepots(game: any) {
  depotGameName.value = game.name
  depotList.value = []
  depotDrawerVisible.value = true
  depotLoading.value = true
  try {
    const detail = await GetGameDetail(game.app_id)
    depotList.value = detail?.depots || []
  } catch {
    depotList.value = []
  } finally {
    depotLoading.value = false
  }
}

function goToDLC(game: any) {
  router.push(`/games/${game.app_id}/dlc`)
}

async function removeGame(appID: number) {
  await gamesStore.removeGame(appID)
  message.success(t('games.removed'))
}

async function unlockGame(game: any) {
  if (appStore.isRunning) {
    message.warning(t('home.task_running'))
    return
  }
  appStore.setTaskStatus('running')
  appStore.clearLogs()
  try {
    const resp = await StartUnlock(String(game.app_id))
    if (resp.success) {
      message.success(t('home.task_started'))
    } else {
      appStore.setTaskStatus('idle')
      message.error(resp.message)
    }
  } catch (e: any) {
    appStore.setTaskStatus('idle')
    message.error(e.message || t('home.task_failed'))
  }
}
</script>
