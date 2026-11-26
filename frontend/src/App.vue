<script setup>
import { computed, ref } from 'vue'
import DepartmentBoard from './components/DepartmentBoard.vue'
import ProjectBoard from './components/ProjectBoard.vue'

const activeView = ref('department')

const currentTitle = computed(() => (activeView.value === 'department' ? 'Department Board' : 'Project Board'))
const currentSubtitle = computed(() =>
  activeView.value === 'department' ? 'PR Project Requirements · EC Incidents' : 'PR Project Requirements',
)
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <a class="brand" href="#" aria-label="idata home">
        <span class="brand-mark"><span></span><span></span><span></span></span>
        <span class="brand-name">idata</span>
      </a>

      <div class="workspace-label">WORKSPACE</div>
      <div class="workspace-switcher">
        <span class="workspace-avatar">S</span>
        <span class="workspace-copy"><strong>idata</strong><small>Enterprise workspace</small></span>
      </div>

      <div class="nav-label">Workspace</div>
      <nav class="navigation" aria-label="Main navigation">
        <button
          class="nav-item"
          :class="{ active: activeView === 'department' }"
          type="button"
          @click="activeView = 'department'"
        >
          <svg viewBox="0 0 20 20" aria-hidden="true"><rect x="3" y="3" width="5" height="6" rx="1" /><rect x="12" y="3" width="5" height="4" rx="1" /><rect x="12" y="10" width="5" height="7" rx="1" /><rect x="3" y="12" width="5" height="5" rx="1" /></svg>
          <span>Department Board</span>
          <span v-if="activeView === 'department'" class="nav-active-dot"></span>
        </button>
        <button
          class="nav-item"
          :class="{ active: activeView === 'project' }"
          type="button"
          @click="activeView = 'project'"
        >
          <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M3 4h14v12H3zM6 7h8M6 10h5M6 13h3" /></svg>
          <span>Project Board</span>
          <span v-if="activeView === 'project'" class="nav-active-dot"></span>
        </button>
      </nav>
    </aside>

    <main class="main-content">
      <header class="topbar">
        <div class="breadcrumb"><span>Workspace</span><span class="breadcrumb-divider">/</span><strong>{{ currentTitle }}</strong></div>
        <div class="topbar-actions">
          <button class="icon-button notification-button" type="button" aria-label="Notifications">
            <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M15.5 7.5a5.5 5.5 0 0 0-11 0c0 6-2 6.5-2 7.5h15c0-1-2-1.5-2-7.5ZM8 18h4" /></svg>
            <i></i>
          </button>
          <div class="top-avatar">L</div>
        </div>
      </header>

      <div class="page-content">
        <section class="page-heading">
          <div>
            <div class="eyebrow"><span class="eyebrow-line"></span> KPI DASHBOARD</div>
            <h1>{{ currentTitle }}<span class="heading-period">· {{ currentSubtitle }}</span></h1>
          </div>
        </section>

        <DepartmentBoard v-if="activeView === 'department'" />
        <ProjectBoard v-else />

        <footer class="page-footer"><span>© 2025 idata</span><span>Every number has a trail.</span></footer>
      </div>
    </main>
  </div>
</template>
