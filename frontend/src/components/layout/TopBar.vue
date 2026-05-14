<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ArrowLeft } from 'lucide-vue-next'
import { storeToRefs } from 'pinia'
import { useAuthStore } from '@/stores/auth'

defineProps<{
  title?: string
  showBack?: boolean
}>()

defineEmits<{
  back: []
}>()

const router = useRouter()
const auth = useAuthStore()
const { guestName, userAvatar } = storeToRefs(auth)

function goProfile() {
  router.push('/profile')
}
</script>

<template>
  <header class="top-bar">
    <div class="top-bar-left">
      <button v-if="showBack" class="back-btn" @click="$emit('back')">
        <ArrowLeft :size="20" />
      </button>
      <div class="brand" v-else>
        <span class="brand-icon">🌸</span>
        <span class="brand-text">恋爱对话模拟器</span>
      </div>
      <h1 class="page-title" v-if="title">{{ title }}</h1>
    </div>

    <div class="top-bar-center">
      <slot name="actions" />
    </div>

    <div class="top-bar-right">
      <div class="user-avatar" @click="goProfile" title="个人中心">
        <img v-if="userAvatar" :src="userAvatar" class="avatar-img" alt="" />
        <span v-else>{{ guestName?.[0] || '?' }}</span>
      </div>
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
.brand-icon { font-size: 20px; }
.brand-text {
  font-family: var(--font-heading);
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--color-primary-dark);
  letter-spacing: 2px;
}

.back-btn {
  width: 36px; height: 36px;
  border-radius: var(--radius-sm);
  display: flex; align-items: center; justify-content: center;
  color: var(--color-text-secondary);
  border: none; background: transparent; cursor: pointer;
  transition: all var(--duration-fast) var(--ease-smooth);
}
.back-btn:hover { background: var(--color-sakura); color: var(--color-primary); }

.page-title {
  font-family: var(--font-heading);
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text);
}

.top-bar-center {
  display: flex; align-items: center; gap: 8px;
  flex: 1; justify-content: center;
}

.top-bar-right {
  display: flex; align-items: center; gap: 8px;
}

.user-avatar {
  width: 34px; height: 34px;
  border-radius: var(--radius-sm);
  background: var(--avatar-gradient-1);
  display: flex; align-items: center; justify-content: center;
  color: #fff;
  font-size: 14px; font-weight: 600;
  cursor: pointer; overflow: hidden;
  transition: transform var(--duration-fast) var(--ease-bounce);
}
.user-avatar:hover { transform: scale(1.08); }
.avatar-img {
  width: 100%; height: 100%;
  border-radius: inherit; object-fit: cover;
}

</style>
