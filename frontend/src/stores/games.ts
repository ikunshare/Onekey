import { defineStore } from 'pinia'
import { ref } from 'vue'
import { GetLibrary, AddToLibrary, RemoveFromLibrary } from '../../wailsjs/go/main/App'

export const useGamesStore = defineStore('games', () => {
  const games = ref<any[]>([])
  const loading = ref(false)

  async function fetchGames() {
    loading.value = true
    try {
      const list = await GetLibrary()
      games.value = list || []
    } catch {
      games.value = []
    } finally {
      loading.value = false
    }
  }

  async function addGame(appID: number, name: string, tinyImage: string, appType: string = 'app') {
    const result = await AddToLibrary(appID, name, tinyImage, appType)
    await fetchGames()
    return result
  }

  async function removeGame(appID: number) {
    await RemoveFromLibrary(appID)
    await fetchGames()
  }

  return { games, loading, fetchGames, addGame, removeGame }
})
