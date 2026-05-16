<script setup lang="ts">
import { computed, onMounted, onUnmounted, watch, ref, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useChatStore } from '@/stores/chat'
import { useAuthStore } from '@/stores/auth'
import { useAutoScroll } from '@/composables/useAutoScroll'
import TopBar from '@/components/layout/TopBar.vue'
import MessageBubble from '@/components/chat/MessageBubble.vue'
import StreamingBubble from '@/components/chat/StreamingBubble.vue'
import TypingIndicator from '@/components/chat/TypingIndicator.vue'
import ChatInput from '@/components/input/ChatInput.vue'
import EmotionBadge from '@/components/chat/EmotionBadge.vue'

const props = defineProps<{ characterId: string }>()

const router = useRouter()
const chat = useChatStore()
const auth = useAuthStore()
const { currentCharacter, messages, isStreaming, streamingContent } = storeToRefs(chat)
const { userAvatar, showApiKeyWarning } = storeToRefs(auth)

const displayMessages = computed(() =>
  messages.value.filter((m): m is typeof m & { role: 'user' | 'assistant' } =>
    m.role === 'user' || m.role === 'assistant'
  )
)

const messageContainer = ref<HTMLElement | null>(null)
const { onNewContent, scrollToBottom, checkScrollPosition } = useAutoScroll(messageContainer)

const loading = ref(true)
const loadError = ref('')

onMounted(async () => {
  try {
    await chat.selectCharacter(props.characterId)
    await auth.loadUserInfo()
  } catch (e: any) {
    loadError.value = e?.response?.data?.detail || '加载角色失败'
  } finally {
    loading.value = false
    await nextTick()
    scrollToBottom(false)
  }
})

onUnmounted(() => {
  chat.disconnectWebSocket()
})

watch(
  () => [messages.value.length, streamingContent.value],
  () => onNewContent(),
)

function onSend(text: string, image: string | null) {
  chat.sendMessage(text, image)
}

function goBack() {
  router.push({ name: 'home' })
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function formatDate() {
  const d = new Date()
  const weekdays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日 ${weekdays[d.getDay()]}`
}
</script>

<template>
  <div class="chat-view">
    <TopBar
      :title="currentCharacter?.name"
      :show-back="true"
      @back="goBack"
    >
      <template #actions>
      </template>
    </TopBar>

    <!-- Loading -->
    <div v-if="loading" class="chat-status">
      <div class="status-spinner" />
      <span>正在加载...</span>
    </div>

    <!-- Error -->
    <div v-else-if="loadError" class="chat-status">
      <span class="status-error">{{ loadError }}</span>
      <button class="status-btn" @click="goBack">返回首页</button>
    </div>

    <!-- Chat -->
    <template v-else>
      <main
        class="chat-messages"
        ref="messageContainer"
        @scroll="checkScrollPosition"
      >
        <div class="date-divider">{{ formatDate() }}</div>

        <MessageBubble
          v-for="m in displayMessages"
          :key="m.id"
          :role="m.role"
          :content="m.content"
          :time="formatTime(m.created_at)"
          :content-type="m.content_type"
          :metadata="m.metadata"
          :avatar-name="m.role === 'assistant' ? currentCharacter?.name?.[0] : undefined"
          :avatar-url="m.role === 'assistant' ? currentCharacter?.avatar_url : undefined"
          :user-avatar-url="m.role === 'user' ? userAvatar : undefined"
        />

        <StreamingBubble
          v-if="isStreaming && streamingContent"
          :content="streamingContent"
          :avatar-name="currentCharacter?.name?.[0]"
          :avatar-url="currentCharacter?.avatar_url"
        />

        <TypingIndicator v-if="isStreaming && !streamingContent" />
      </main>

      <div class="input-area">
        <EmotionBadge />
        <ChatInput @send="onSend" />
      </div>
    </template>

    <!-- API Key 警告弹窗 -->
    <div v-if="showApiKeyWarning" class="api-key-overlay" @click.self="auth.dismissApiKeyWarning()">
      <div class="api-key-dialog">
        <div class="dialog-icon">🔑</div>
        <h3>尚未设置 API Key</h3>
        <p>需要配置自己的 API Key 才能使用 AI 对话、角色生成等功能。</p>
        <div class="dialog-actions">
          <button class="dialog-btn cancel" @click="auth.dismissApiKeyWarning()">稍后再说</button>
          <button class="dialog-btn confirm" @click="auth.dismissApiKeyWarning(); router.push('/profile')">前往设置</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-bg);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px 24px;
}

.date-divider {
  text-align: center;
  font-size: var(--text-xs);
  font-family: var(--font-body);
  color: var(--color-text-muted);
  padding: 8px 0;
  margin-bottom: 4px;
}

/* ── Status (loading / error) ── */
.chat-status {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.status-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.status-error {
  color: var(--color-error);
}

.status-btn {
  padding: 8px 24px;
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius-full);
  font-size: var(--text-sm);
  font-family: var(--font-body);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-smooth);
}
.status-btn:hover {
  background: var(--color-primary-dark);
  box-shadow: var(--shadow-sm);
}

.input-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 20px 8px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .chat-messages {
    padding: 16px;
    gap: 12px;
  }
}

/* ── API Key Warning Dialog ── */
.api-key-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}
.api-key-dialog {
  background: var(--color-bg);
  border-radius: var(--radius-md);
  padding: 32px 28px 24px;
  max-width: 360px;
  width: 90%;
  text-align: center;
  box-shadow: var(--shadow-lg);
  animation: scaleIn 0.25s var(--ease-bounce);
}
.dialog-icon { font-size: 40px; margin-bottom: 12px; }
.api-key-dialog h3 {
  font-size: 18px;
  font-weight: 700;
  font-family: var(--font-heading);
  color: var(--color-text);
  margin: 0 0 8px;
}
.api-key-dialog p {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  margin: 0 0 20px;
  line-height: 1.6;
}
.dialog-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
}
.dialog-btn {
  padding: 8px 20px;
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  font-family: var(--font-body);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--duration-fast);
  border: none;
}
.dialog-btn.cancel {
  background: var(--color-surface);
  color: var(--color-text-secondary);
}
.dialog-btn.cancel:hover { background: var(--color-border); }
.dialog-btn.confirm {
  background: var(--color-primary);
  color: #fff;
}
.dialog-btn.confirm:hover { opacity: 0.9; }

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes scaleIn { from { opacity: 0; transform: scale(0.92); } to { opacity: 1; transform: scale(1); } }
</style>
