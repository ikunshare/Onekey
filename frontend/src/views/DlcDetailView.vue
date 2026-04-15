<template>
  <div>
    <n-page-header @back="router.back()">
      <template #title>
        <n-space :size="8" align="center">
          <span>{{ game?.name || 'DLC' }}</span>
          <n-tag v-if="game?.unlocked" size="small" type="success">{{ t('games.unlocked') }}</n-tag>
        </n-space>
      </template>
      <template #subtitle>
        {{ t('dlc.subtitle', {count: String(dlcList.length)}) }}
      </template>
    </n-page-header>

    <n-spin :show="loading" style="margin-top: 16px;">
      <n-empty v-if="!loading && dlcList.length === 0" :description="t('games.no_dlc_data')" style="margin-top: 48px"/>

      <n-collapse v-else style="margin-top: 16px;">
        <n-collapse-item v-for="dlc in groupedDLCs" :key="dlc.appId" :name="dlc.appId">
          <template #header>
            <n-space :size="8" align="center">
              <n-text strong>App {{ dlc.appId }}</n-text>
              <n-tag :bordered="false" size="tiny">{{ dlc.depots.length }} depots</n-tag>
            </n-space>
          </template>
          <n-table :bordered="false" :single-line="false" size="small">
            <thead>
            <tr>
              <th>Depot ID</th>
              <th>Manifest ID</th>
              <th>Depot Key</th>
            </tr>
            </thead>
            <tbody>
            <tr v-for="d in dlc.depots" :key="d.depot_id">
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
        </n-collapse-item>
      </n-collapse>
    </n-spin>
  </div>
</template>

<script lang="ts" setup>
import {computed, onMounted, ref} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {useI18n} from '../i18n'
import {GetGameDetail} from '../../wailsjs/go/main/App'

const {t} = useI18n()
const route = useRoute()
const router = useRouter()

const game = ref<any>(null)
const loading = ref(true)

const dlcList = computed(() => game.value?.dlcs || [])

const groupedDLCs = computed(() => {
  const map = new Map<string, any[]>()
  for (const d of dlcList.value) {
    const key = d.app_id || 'unknown'
    if (!map.has(key)) map.set(key, [])
    map.get(key)!.push(d)
  }
  return Array.from(map.entries()).map(([appId, depots]) => ({appId, depots}))
})

onMounted(async () => {
  const appId = Number(route.params.appId)
  if (!appId) {
    router.back()
    return
  }
  try {
    game.value = await GetGameDetail(appId)
  } catch {
    // ignore
  } finally {
    loading.value = false
  }
})
</script>
