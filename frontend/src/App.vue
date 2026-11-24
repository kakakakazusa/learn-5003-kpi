<script setup>
import { computed, ref } from 'vue'
import DepartmentBoard from './components/DepartmentBoard.vue'
import ProjectBoard from './components/ProjectBoard.vue'

const activeView = ref('department')

const currentTitle = computed(() => (activeView.value === 'department' ? '部门看板' : '项目看板'))
const currentSubtitle = computed(() =>
  activeView.value === 'department' ? 'PR 项目需求 · EC 故障' : 'PR 项目需求',
)
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <a class="brand" href="#" aria-label="idata数据平台首页">
        <span class="brand-mark"><span></span><span></span><span></span></span>
        <span class="brand-name">idata</span>
      </a>

      <div class="workspace-label">WORKSPACE</div>
      <div class="workspace-switcher">
        <span class="workspace-avatar">S</span>
        <span class="workspace-copy"><strong>idata</strong><small>企业工作空间</small></span>
      </div>

      <div class="nav-label">工作台</div>
      <nav class="navigation" aria-label="主导航">
        <button
          class="nav-item"
          :class="{ active: activeView === 'department' }"
          type="button"
          @click="activeView = 'department'"
        >
          <svg viewBox="0 0 20 20" aria-hidden="true"><rect x="3" y="3" width="5" height="6" rx="1" /><rect x="12" y="3" width="5" height="4" rx="1" /><rect x="12" y="10" width="5" height="7" rx="1" /><rect x="3" y="12" width="5" height="5" rx="1" /></svg>
          <span>部门看板</span>
          <span v-if="activeView === 'department'" class="nav-active-dot"></span>
        </button>
        <button
          class="nav-item"
          :class="{ active: activeView === 'project' }"
          type="button"
          @click="activeView = 'project'"
        >
          <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M3 4h14v12H3zM6 7h8M6 10h5M6 13h3" /></svg>
          <span>项目看板</span>
          <span v-if="activeView === 'project'" class="nav-active-dot"></span>
        </button>
      </nav>
    </aside>

    <main class="main-content">
      <header class="topbar">
        <div class="breadcrumb"><span>工作台</span><span class="breadcrumb-divider">/</span><strong>{{ currentTitle }}</strong></div>
        <div class="topbar-actions">
          <button class="icon-button notification-button" type="button" aria-label="通知">
            <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M15.5 7.5a5.5 5.5 0 0 0-11 0c0 6-2 6.5-2 7.5h15c0-1-2-1.5-2-7.5ZM8 18h4" /></svg>
            <i></i>
          </button>
          <div class="top-avatar">林</div>
        </div>
      </header>

      <div class="page-content">
        <section class="page-heading">
          <div>
            <div class="eyebrow"><span class="eyebrow-line"></span> KPI DASHBOARD</div>
            <h1>{{ currentTitle }}<span class="heading-period">· {{ currentSubtitle }}</span></h1>
            <p>你好，小满。这里是你的关键绩效指标趋势概览。</p>
          </div>
        </section>

        <DepartmentBoard v-if="activeView === 'department'" />
        <ProjectBoard v-else />

        <footer class="page-footer"><span>© 2025 idata</span><span>让每一个数据，都有迹可循。</span></footer>
      </div>
    </main>
  </div>
</template>
