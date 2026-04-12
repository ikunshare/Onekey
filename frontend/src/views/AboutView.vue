<template>
  <div>
    <header class="app-bar">
      <div class="app-bar-content">
        <button class="btn btn-text" @click="router.push('/')">
          <span class="material-icons">arrow_back</span>
        </button>
        <span class="material-icons app-icon">info</span>
        <h1 class="app-title">{{ t('nav.about') }}</h1>
      </div>
    </header>

    <main class="main-content">
      <!-- Project Info Card -->
      <div class="card project-info-card">
        <div class="project-header" style="display: flex; align-items: center; gap: 16px; margin-bottom: 24px;">
          <div class="project-logo" style="font-size: 48px; color: var(--md-sys-color-primary);">
            <span class="material-icons" style="font-size: inherit">extension</span>
          </div>
          <div class="project-details" style="flex: 1;">
            <h3 style="margin: 0; font-size: 1.5rem;">Onekey</h3>
            <p style="margin: 4px 0 0; opacity: 0.7;">{{ t('about.project_subtitle') }}</p>
          </div>
          <div class="project-version" style="text-align: right;">
            <span class="version-label" style="display: block; font-size: 1.25rem; font-weight: bold; color: var(--md-sys-color-primary);">v3.0.0</span>
            <span class="version-type" style="font-size: 0.8rem; opacity: 0.6;">{{ t('about.version_label') }}</span>
          </div>
        </div>

        <div class="project-links" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px;">
          <a href="https://github.com/ikunshare/Onekey" target="_blank" class="project-link">
            <span class="material-icons">code</span>
            <div class="link-content">
              <span class="link-title">{{ t('about.github') }}</span>
              <span class="link-url">github.com/ikunshare/Onekey</span>
            </div>
          </a>
          <a href="https://github.com/ikunshare/Onekey/releases" target="_blank" class="project-link">
            <span class="material-icons">file_download</span>
            <div class="link-content">
              <span class="link-title">{{ t('about.releases') }}</span>
              <span class="link-url">{{ t('about.releases_desc') }}</span>
            </div>
          </a>
          <a href="https://shop.ikunshare.com" target="_blank" class="project-link">
            <span class="material-icons">shopping_cart</span>
            <div class="link-content">
              <span class="link-title">{{ t('about.buy') }}</span>
              <span class="link-url">{{ t('about.buy_desc') }}</span>
            </div>
          </a>
          <a href="https://github.com/qwq-xinkeng" target="_blank" class="project-link">
            <span class="material-icons">person</span>
            <div class="link-content">
              <span class="link-title">{{ t('about.author') }}</span>
              <span class="link-url">github.com/qwq-xinkeng</span>
            </div>
          </a>
          <a href="https://github.com/ikun0014" target="_blank" class="project-link">
            <span class="material-icons">person</span>
            <div class="link-content">
              <span class="link-title">{{ t('about.author') }}</span>
              <span class="link-url">github.com/ikun0014</span>
            </div>
          </a>
          <a href="https://github.com/ikunshare/Onekey/issues" target="_blank" class="project-link">
            <span class="material-icons">bug_report</span>
            <div class="link-content">
              <span class="link-title">{{ t('about.issues') }}</span>
              <span class="link-url">{{ t('about.issues_desc') }}</span>
            </div>
          </a>
        </div>
      </div>

      <!-- Tech Info -->
      <div class="card">
        <div class="card-header">
          <span class="material-icons">code</span>
          <h2>{{ t('about.tech_title') }}</h2>
        </div>
        <div class="card-content">
          <div class="tech-content" style="display: grid; gap: 12px;">
            <div class="tech-item" style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--md-sys-color-outline-variant);">
              <strong>{{ t('about.tech_backend') }}</strong>
              <span>{{ t('about.tech_backend_val') }}</span>
            </div>
            <div class="tech-item" style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--md-sys-color-outline-variant);">
              <strong>{{ t('about.tech_frontend') }}</strong>
              <span>{{ t('about.tech_frontend_val') }}</span>
            </div>
            <div class="tech-item" style="display: flex; justify-content: space-between; padding: 8px 0;">
              <strong>{{ t('about.tech_tools') }}</strong>
              <span>{{ t('about.tech_tools_val') }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Usage Notice -->
      <div class="card">
        <div class="card-header">
          <span class="material-icons">info</span>
          <h2>{{ t('about.notice_title') }}</h2>
        </div>
        <div class="card-content">
          <div style="display: grid; gap: 12px;">
            <p><strong>{{ t('about.notice_system') }}</strong> - {{ t('about.notice_system_val') }}</p>
            <p><strong>{{ t('about.notice_tool') }}</strong> - {{ t('about.notice_tool_val') }}</p>
            <p><strong>{{ t('about.notice_disclaimer') }}</strong> - {{ t('about.notice_disclaimer_val') }}</p>
            <p><strong>{{ t('about.notice_star') }}</strong> - {{ t('about.notice_star_val') }}</p>
          </div>
        </div>
      </div>

      <!-- Copyright -->
      <div style="text-align: center; padding: 24px; opacity: 0.6;">
        <p>{{ t('about.copyright') }}</p>
        <p>项目地址：<a href="https://github.com/ikunshare/Onekey" target="_blank">https://github.com/ikunshare/Onekey</a></p>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useI18n } from '../i18n'

const router = useRouter()
const { t } = useI18n()
</script>
