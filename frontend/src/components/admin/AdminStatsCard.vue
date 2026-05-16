<script setup lang="ts">
import type { Component } from 'vue'

defineProps<{
  icon: Component
  label: string
  value: number
  subtitle: string
  theme: 'pink' | 'amber' | 'purple' | 'rose' | 'teal'
}>()
</script>

<template>
  <div class="stat-card" :class="`card-${theme}`">
    <div class="card-glow" />
    <div class="card-body">
      <div class="card-icon-box">
        <component :is="icon" :size="22" />
      </div>
      <div class="card-info">
        <span class="card-value">{{ value.toLocaleString() }}</span>
        <span class="card-label">{{ label }}</span>
      </div>
    </div>
    <div class="card-footer">
      <span class="card-sub">{{ subtitle }}</span>
    </div>
  </div>
</template>

<style scoped>
.stat-card {
  position: relative;
  background: var(--color-surface);
  border-radius: 16px;
  padding: 20px;
  overflow: hidden;
  border: 1px solid var(--color-border);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: default;
}
.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0,0,0,0.08);
}

.card-glow {
  position: absolute;
  top: -40px; right: -40px;
  width: 120px; height: 120px;
  border-radius: 50%;
  opacity: 0.12;
  transition: opacity 0.3s;
}
.stat-card:hover .card-glow { opacity: 0.2; }

.card-pink  .card-glow { background: #f598a5; }
.card-pink  .card-icon-box { background: #fef0f3; color: #e87d8a; }
.card-pink  { border-top: 3px solid #e87d8a; }

.card-amber .card-glow { background: #f59e0b; }
.card-amber .card-icon-box { background: #fffbeb; color: #d97706; }
.card-amber { border-top: 3px solid #f59e0b; }

.card-purple .card-glow { background: #a78bfa; }
.card-purple .card-icon-box { background: #f5f3ff; color: #7c3aed; }
.card-purple { border-top: 3px solid #a78bfa; }

.card-rose .card-glow { background: #fb7185; }
.card-rose .card-icon-box { background: #fff1f2; color: #e11d48; }
.card-rose { border-top: 3px solid #fb7185; }

.card-teal .card-glow { background: #2dd4bf; }
.card-teal .card-icon-box { background: #f0fdfa; color: #0d9488; }
.card-teal { border-top: 3px solid #2dd4bf; }

.card-body {
  display: flex;
  align-items: center;
  gap: 14px;
  position: relative;
  z-index: 1;
}

.card-icon-box {
  width: 46px; height: 46px;
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}

.card-info {
  display: flex; flex-direction: column;
  min-width: 0;
}

.card-value {
  font-family: var(--font-heading);
  font-size: 28px;
  font-weight: 800;
  color: var(--color-text);
  line-height: 1.1;
  letter-spacing: -1px;
}

.card-label {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-top: 2px;
  font-weight: 500;
}

.card-footer {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid var(--color-border);
  position: relative; z-index: 1;
}

.card-sub {
  font-size: 11px;
  color: var(--color-text-muted);
  font-weight: 500;
}
</style>
