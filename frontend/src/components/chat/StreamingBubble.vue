<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  content: string
  avatarName?: string
  avatarUrl?: string | null
}>()

const filtered = computed(() => {
  return props.content.replace(/\[image[:：].*?\]/gis, '')
})
</script>

<template>
  <div class="message assistant">
    <div class="msg-avatar">
      <img v-if="avatarUrl" :src="avatarUrl" class="avatar-img" alt="" />
      <span v-else>{{ avatarName || '?' }}</span>
    </div>
    <div class="msg-content">
      <div class="msg-bubble">
        {{ filtered }}<span class="cursor">|</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.message {
  display: flex;
  gap: 10px;
  max-width: 72%;
  align-self: flex-start;
  animation: msgIn 0.3s var(--ease-bounce);
}
.msg-avatar {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 700;
  font-family: var(--font-heading);
  color: #fff;
  margin-top: 2px;
  background: var(--avatar-gradient-1);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}
.avatar-img {
  width: 100%;
  height: 100%;
  border-radius: inherit;
  object-fit: cover;
}
.msg-bubble {
  padding: 10px 14px;
  border-radius: 8px;
  background: var(--color-bubble-ai);
  color: var(--color-text);
  font-size: 15px;
  line-height: 1.7;
  word-break: break-word;
  font-family: var(--font-body);
  position: relative;
}
.msg-bubble::after {
  content: '';
  position: absolute;
  top: 12px;
  left: -6px;
  width: 0;
  height: 0;
  border: 6px solid transparent;
  border-right-color: var(--color-bubble-ai);
  border-left: 0;
}
.cursor {
  display: inline-block;
  animation: blink 1s step-end infinite;
  color: var(--color-primary);
  font-weight: 300;
}
@keyframes blink {
  50% { opacity: 0; }
}
@keyframes msgIn {
  from { opacity: 0; transform: translateY(8px) scale(0.98); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}
</style>
