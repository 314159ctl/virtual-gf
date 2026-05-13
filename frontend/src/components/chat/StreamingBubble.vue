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
        {{ content }}<span class="cursor">|</span>
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
}
.msg-bubble {
  padding: 12px 18px;
  border-radius: var(--radius);
  border-bottom-left-radius: var(--radius-xs);
  background: var(--color-bubble-ai);
  color: var(--color-text);
  font-size: 15px;
  line-height: 1.7;
  word-break: break-word;
  font-family: var(--font-body);
  box-shadow: 0 1px 4px rgba(0,0,0,0.03);
  border: 1px solid rgba(255,125,175,0.06);
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
