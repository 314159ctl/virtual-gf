<script setup lang="ts">
import { computed, ref } from 'vue'
import { RotateCcw, Trash2 } from 'lucide-vue-next'

const props = defineProps<{
  role: 'user' | 'assistant'
  content: string
  time?: string
  avatarName?: string
  avatarUrl?: string | null
  userAvatarUrl?: string | null
  contentType?: string
  metadata?: Record<string, any> | null
  messageId?: string
  index?: number
  isLast?: boolean
}>()

const emit = defineEmits<{
  recall: [id: string]
  retry: [id: string]
}>()

const showActions = ref(false)

const cleanContent = computed(() => {
  return props.content?.replace(/\[image[:：].*?\]/gis, '').trim() || ''
})

const hasText = computed(() => {
  return cleanContent.value && cleanContent.value !== '[图片]'
})
</script>

<template>
  <div class="message" :class="role">
    <!-- AI 头像（左，正常 flex） -->
    <div class="msg-avatar ai-avatar" v-if="role === 'assistant'">
      <img v-if="avatarUrl" :src="avatarUrl" class="avatar-img" alt="" />
      <span v-else>{{ avatarName || '?' }}</span>
    </div>

    <!-- 用户头像（row-reverse 反转后会到右边） -->
    <div class="msg-avatar user-avatar" v-if="role === 'user'">
      <img v-if="userAvatarUrl" :src="userAvatarUrl" class="avatar-img" alt="" />
      <span v-else>我</span>
    </div>

    <div class="msg-content" @mouseenter="showActions = true" @mouseleave="showActions = false">
      <div class="msg-bubble" :class="role">
        <img
          v-if="contentType === 'image' && (metadata?.image_base64 || metadata?.image_url)"
          :src="metadata.image_base64 || metadata.image_url"
          class="msg-image"
          alt="generated"
        />
        <span v-if="hasText" class="msg-text">{{ cleanContent }}</span>
      </div>
      <div class="msg-meta" :class="role">
        <span class="msg-time" v-if="time">{{ time }}</span>
        <div v-if="showActions && messageId" class="msg-actions" :class="role">
          <button v-if="role === 'user'" class="act-btn" title="撤回" @click.stop="emit('recall', messageId!)">
            <Trash2 :size="12" />
          </button>
          <button v-if="role === 'assistant' && isLast" class="act-btn retry" title="重发" @click.stop="emit('retry', messageId!)">
            <RotateCcw :size="12" />
          </button>
        </div>
      </div>
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
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}
.ai-avatar {
  background: var(--avatar-gradient-1);
}
.user-avatar {
  background: var(--avatar-gradient-2);
  font-size: 12px;
}
.avatar-img {
  width: 100%;
  height: 100%;
  border-radius: inherit;
  object-fit: cover;
}

/* ── Bubble · 微信风格 ── */
.msg-bubble {
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 15px;
  line-height: 1.6;
  word-break: break-word;
  font-family: var(--font-body);
  display: flex;
  flex-direction: column;
  gap: 6px;
  position: relative;
}
.msg-bubble.user {
  background: var(--color-bubble-user-solid);
  color: #fff;
}
.msg-bubble.user::after {
  content: '';
  position: absolute;
  top: 12px;
  right: -6px;
  width: 0;
  height: 0;
  border: 6px solid transparent;
  border-left-color: var(--color-bubble-user-solid);
  border-right: 0;
}
.msg-bubble.assistant {
  background: var(--color-bubble-ai);
  color: var(--color-text);
}
.msg-bubble.assistant::after {
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
.msg-meta.assistant {
  justify-content: flex-start;
}
.msg-time {
  font-size: 10px;
  font-family: var(--font-body);
  color: var(--color-text-muted);
}

.msg-actions {
  display: flex;
  gap: 2px;
  margin-left: 4px;
}
.msg-actions.user { justify-content: flex-end; }
.act-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px; height: 22px;
  border: none; border-radius: var(--radius-xs);
  background: var(--color-sakura);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all var(--duration-fast);
}
.act-btn:hover { background: var(--color-error); color: #fff; }
.act-btn.retry:hover { background: var(--color-primary); color: #fff; }

@keyframes msgIn {
  from { opacity: 0; transform: translateY(10px) scale(0.97); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}

@media (max-width: 768px) {
  .message {
    max-width: 88%;
  }
  .msg-bubble {
    font-size: 14px;
    padding: 8px 12px;
  }
  .msg-image {
    max-width: 180px;
    max-height: 150px;
  }
}
</style>
