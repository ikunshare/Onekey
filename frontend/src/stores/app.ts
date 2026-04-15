import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAppStore = defineStore('app', () => {
  const taskStatus = ref<'idle' | 'running' | 'completed' | 'error'>('idle')
  const logs = ref<Array<{ type: string; message: string; timestamp: string }>>([])
  const config = ref<{
    steam_path: string
    debug_mode: boolean
  }>({ steam_path: '', debug_mode: false })

  // Search state (persists across route changes)
  const searchTerm = ref('')
  const searchResults = ref<any[]>([])
  const searchDone = ref(false)

  const isRunning = computed(() => taskStatus.value === 'running')

  function addLog(type: string, message: string) {
    logs.value.push({
      type,
      message,
      timestamp: new Date().toLocaleTimeString(),
    })
  }

  function clearLogs() {
    logs.value = []
  }

  function setTaskStatus(status: 'idle' | 'running' | 'completed' | 'error') {
    taskStatus.value = status
  }

  return { taskStatus, logs, config, isRunning, addLog, clearLogs, setTaskStatus, searchTerm, searchResults, searchDone }
})
