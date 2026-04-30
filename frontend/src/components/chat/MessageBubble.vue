<script setup lang="ts">
defineProps<{
  role: 'user' | 'assistant'
  content: string
  time?: string
  avatarName?: string
  contentType?: string
  metadata?: Record<string, any> | null
}>()
</script>

<template>
  <div class="message" :class="role">
    <div class="msg-avatar" :class="role" v-if="role === 'assistant'">
      {{ avatarName || '?' }}
    </div>
    <div class="msg-content">
      <div class="msg-bubble" :class="role">
        <img
          v-if="contentType === 'image' && metadata?.image_base64"
          :src="metadata.image_base64"
          class="msg-image"
          alt="uploaded"
        />
        <span v-if="content && content !== '[图片]'">{{ content }}</span>
      </div>
      <div class="msg-meta" v-if="time" :class="role">
        <span class="msg-time">{{ time }}</span>
      </div>
    </div>
    <div class="msg-avatar user-avatar" v-if="role === 'user'">
      我
    </div>
  </div>
</template>

<style scoped>
.message {
  display: flex;
  gap: 10px;
  max-width: 75%;
  animation: msgIn 0.35s var(--ease-bounce);
}
.message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}
.message.assistant {
  align-self: flex-start;
}

/* ── Avatar ── */
.msg-avatar {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  font-family: var(--font-heading);
  color: #fff;
  margin-top: 2px;
  box-shadow: var(--shadow-xs);
}
.msg-avatar.assistant {
  background: var(--avatar-gradient-1);
}
.user-avatar {
  background: var(--avatar-gradient-2);
  font-size: 12px;
}

/* ── Bubble ── */
.msg-bubble {
  padding: 12px 18px;
  border-radius: var(--radius);
  font-size: 15px;
  line-height: 1.7;
  word-break: break-word;
  font-family: var(--font-body);
  transition: transform var(--duration-fast) var(--ease-smooth);
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.msg-bubble.user {
  background: var(--color-bubble-user-solid);
  color: #fff;
  border-bottom-right-radius: var(--radius-xs);
  box-shadow: 0 2px 8px rgba(255,125,175,0.18);
}
.msg-bubble.user:hover {
  transform: translateY(-1px);
}
.msg-bubble.assistant {
  background: var(--color-bubble-ai);
  color: var(--color-text);
  border-bottom-left-radius: var(--radius-xs);
  box-shadow: 0 1px 4px rgba(0,0,0,0.03);
  border: 1px solid rgba(255,125,175,0.06);
}
.msg-bubble.assistant:hover {
  background: var(--color-bubble-ai-hover);
}

/* ── Image ── */
.msg-image {
  max-width: 240px;
  max-height: 200px;
  border-radius: var(--radius-sm);
  object-fit: cover;
}

/* ── Meta ── */
.msg-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 3px;
  padding: 0 6px;
}
.msg-meta.user {
  justify-content: flex-end;
}
.msg-time {
  font-size: 10px;
  font-family: var(--font-body);
  color: var(--color-text-muted);
}

@keyframes msgIn {
  from { opacity: 0; transform: translateY(10px) scale(0.97); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}
</style>
