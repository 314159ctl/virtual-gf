<script setup lang="ts">
defineProps<{
  content: string
  avatarName?: string
}>()
</script>

<template>
  <div class="message assistant">
    <div class="msg-avatar">{{ avatarName || '?' }}</div>
    <div class="msg-content">
      <div class="msg-bubble">
        {{ content }}
        <span class="cursor">|</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.message {
  display: flex; gap: 10px; max-width: 72%;
  align-self: flex-start;
}
.msg-avatar {
  width: 34px; height: 34px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; color: #fff; margin-top: 2px;
  background: linear-gradient(135deg, var(--color-primary), var(--color-accent));
}
.msg-bubble {
  padding: 12px 18px; border-radius: 20px;
  border-bottom-left-radius: 6px;
  background: var(--color-bubble-ai); color: var(--color-text);
  font-size: 15px; line-height: 1.6; word-break: break-word;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
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
</style>
