<script setup lang="ts">
defineProps<{
  role: 'user' | 'assistant'
  content: string
  time?: string
  avatarName?: string
}>()
</script>

<template>
  <div class="message" :class="role">
    <div class="msg-avatar">{{ role === 'user' ? '🙂' : (avatarName || '?') }}</div>
    <div class="msg-content">
      <div class="msg-bubble">{{ content }}</div>
      <div class="msg-time" v-if="time">{{ time }}</div>
    </div>
  </div>
</template>

<style scoped>
.message {
  display: flex; gap: 10px; max-width: 72%;
  animation: fadeInUp 0.3s var(--ease-out);
}
.message.user { align-self: flex-end; flex-direction: row-reverse; }
.message.assistant { align-self: flex-start; }
.msg-avatar {
  width: 34px; height: 34px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; color: #fff; margin-top: 2px;
}
.message.user .msg-avatar { background: linear-gradient(135deg, #667eea, #764ba2); }
.message.assistant .msg-avatar { background: linear-gradient(135deg, var(--color-primary), var(--color-accent)); }
.msg-bubble {
  padding: 12px 18px; border-radius: 20px;
  font-size: 15px; line-height: 1.6; word-break: break-word;
}
.message.user .msg-bubble {
  background: var(--color-bubble-user); color: #fff;
  border-bottom-right-radius: 6px;
}
.message.assistant .msg-bubble {
  background: var(--color-bubble-ai); color: var(--color-text);
  border-bottom-left-radius: 6px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.msg-time {
  font-size: 10px; color: var(--color-text-muted);
  margin-top: 2px; padding: 0 4px;
}
.message.user .msg-time { text-align: right; color: rgba(255,255,255,0.7); }

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
