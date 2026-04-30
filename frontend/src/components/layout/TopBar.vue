<script setup lang="ts">
import { ArrowLeft, LogOut } from 'lucide-vue-next'

defineProps<{
  title?: string
  showBack?: boolean
  username?: string
}>()

defineEmits<{
  back: []
  logout: []
}>()
</script>

<template>
  <header class="top-bar">
    <div class="top-bar-left">
      <button v-if="showBack" class="back-btn" @click="$emit('back')">
        <ArrowLeft :size="20" />
      </button>
      <div class="brand" v-else>
        <span class="brand-icon">🌸</span>
        <span class="brand-text">千恋万花</span>
      </div>
      <h1 class="page-title" v-if="title">{{ title }}</h1>
    </div>

    <div class="top-bar-center">
      <slot name="actions" />
    </div>

    <div class="top-bar-right">
      <span class="user-name" v-if="username">{{ username }}</span>
      <div class="user-avatar" v-if="username">{{ username[0] }}</div>
      <button class="logout-btn" @click="$emit('logout')" title="退出登录">
        <LogOut :size="18" />
      </button>
    </div>
  </header>
</template>

<style scoped>
.top-bar {
  height: var(--header-h);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background: var(--header-gradient);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.top-bar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 8px;
}
.brand-icon {
  font-size: 20px;
}
.brand-text {
  font-family: var(--font-heading);
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--color-primary-dark);
  letter-spacing: 2px;
}

.back-btn {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-secondary);
  transition: all var(--duration-fast) var(--ease-smooth);
}
.back-btn:hover {
  background: var(--color-sakura);
  color: var(--color-primary);
}

.page-title {
  font-family: var(--font-heading);
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text);
}

.top-bar-center {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  justify-content: center;
}

.top-bar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-name {
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text-secondary);
}

.user-avatar {
  width: 34px;
  height: 34px;
  border-radius: var(--radius-sm);
  background: var(--avatar-gradient-1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
}

.logout-btn {
  width: 34px;
  height: 34px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
  transition: all var(--duration-fast) var(--ease-smooth);
}
.logout-btn:hover {
  background: rgba(232,128,138,0.1);
  color: var(--color-error);
}
</style>
