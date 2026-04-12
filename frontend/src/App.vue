<template>
  <div class="app-container" :class="{ dark: isDark }">
    <router-view />
    <!-- Snackbar -->
    <div :class="['snackbar', snackbarType, { show: snackbarVisible }]">
      <div class="snackbar-content">
        <span>{{ snackbarMessage }}</span>
        <button class="snackbar-action" @click="snackbarVisible = false">
          <span class="material-icons">close</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, provide } from 'vue'

const isDark = ref(localStorage.getItem('theme') === 'dark')

function toggleTheme() {
  isDark.value = !isDark.value
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
  document.documentElement.classList.toggle('dark', isDark.value)
}

// Snackbar
const snackbarVisible = ref(false)
const snackbarMessage = ref('')
const snackbarType = ref('info')
let snackbarTimer: ReturnType<typeof setTimeout>

function showSnackbar(message: string, type: string = 'info') {
  snackbarMessage.value = message
  snackbarType.value = type
  snackbarVisible.value = true
  clearTimeout(snackbarTimer)
  snackbarTimer = setTimeout(() => {
    snackbarVisible.value = false
  }, 4000)
}

provide('isDark', isDark)
provide('toggleTheme', toggleTheme)
provide('showSnackbar', showSnackbar)

// Apply saved theme
if (isDark.value) {
  document.documentElement.classList.add('dark')
}
</script>
