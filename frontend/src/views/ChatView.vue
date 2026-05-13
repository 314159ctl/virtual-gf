<script setup lang="ts">
import { computed, onMounted, watch, ref } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useChatStore } from '@/stores/chat'
import { useAutoScroll } from '@/composables/useAutoScroll'
import TopBar from '@/components/layout/TopBar.vue'
import MessageBubble from '@/components/chat/MessageBubble.vue'
import StreamingBubble from '@/components/chat/StreamingBubble.vue'
import TypingIndicator from '@/components/chat/TypingIndicator.vue'
import ChatInput from '@/components/input/ChatInput.vue'
import MemoryPanel from '@/components/chat/MemoryPanel.vue'
import EmotionBadge from '@/components/chat/EmotionBadge.vue'
import { Brain } from 'lucide-vue-next'

const props = defineProps<{ characterId: string }>()

const router = useRouter()
const chat = useChatStore()
const { currentCharacter, messages, isStreaming, streamingContent } = storeToRefs(chat)

const displayMessages = computed(() =>
  messages.value.filter((m): m is typeof m & { role: 'user' | 'assistant' } =>
    m.role === 'user' || m.role === 'assistant'
  )
)

const messageContainer = ref<HTMLElement | null>(null)
const { onNewContent, checkScrollPosition } = useAutoScroll(messageContainer)

const loading = ref(true)
const loadError = ref('')
const showMemory = ref(false)

onMounted(async () => {
  try {
    await chat.selectCharacter(props.characterId)
  } catch (e: any) {
    loadError.value = e?.response?.data?.detail || '加载角色失败'
  } finally {
    loading.value = false
  }
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
        <button class="memory-btn" @click="showMemory = true" title="记忆管理">
          <Brain :size="18" />
        </button>
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
        />

        <StreamingBubble
          v-if="isStreaming && streamingContent"
          :content="streamingContent"
          :avatar-name="currentCharacter?.name?.[0]"
        />

        <TypingIndicator v-if="isStreaming && !streamingContent" />
      </main>

      <div class="input-area">
        <EmotionBadge />
        <ChatInput @send="onSend" />
      </div>
    </template>

    <MemoryPanel :show="showMemory" @close="showMemory = false" />
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

.memory-btn {
  width: 34px;
  height: 34px;
  border: none;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-smooth);
}
.memory-btn:hover {
  background: var(--color-sakura);
  color: var(--color-accent);
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
</style>
