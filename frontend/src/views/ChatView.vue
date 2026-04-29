<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useChatStore } from '@/stores/chat'
import { useAuthStore } from '@/stores/auth'
import Sidebar from '@/components/layout/Sidebar.vue'
import MessageBubble from '@/components/chat/MessageBubble.vue'
import StreamingBubble from '@/components/chat/StreamingBubble.vue'
import TypingIndicator from '@/components/chat/TypingIndicator.vue'
import ChatInput from '@/components/input/ChatInput.vue'
import BaseModal from '@/components/shared/BaseModal.vue'

const chat = useChatStore()
const auth = useAuthStore()
const { currentCharacter, messages, isStreaming, streamingContent } = storeToRefs(chat)

const showSettings = ref(false)
const showCharModal = ref(false)
const showPainting = ref(false)
const paintingPrompt = ref('')
const paintingUrl = ref('')
const paintingLoading = ref(false)
const sidebarOpen = ref(false)

// Settings form
const settingApiKey = ref('')
const settingBaseUrl = ref('https://api.deepseek.com')
const settingModel = ref('deepseek-chat')

onMounted(async () => {
  await auth.fetchUser()
  chat.connectWebSocket()
  await chat.loadCharacters()
})

function onSend(text: string, image: string | null) {
  chat.sendMessage(text, image)
}

async function onGeneratePaint() {
  if (!paintingPrompt.value.trim()) return
  paintingLoading.value = true
  try {
    const { default: api } = await import('@/utils/http')
    const res = await api.post('/images/generate', {
      prompt: paintingPrompt.value,
    })
    paintingUrl.value = res.data.url
  } catch (e: any) {
    console.error(e)
  } finally {
    paintingLoading.value = false
  }
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div class="app-shell">
    <Sidebar
      @new-character="showCharModal = true"
      @open-settings="showSettings = true"
      @open-painting="showPainting = true"
    />

    <main class="main-panel">
      <!-- Mobile hamburger -->
      <header class="chat-header" v-if="currentCharacter">
        <button class="hamburger" @click="sidebarOpen = !sidebarOpen">☰</button>
        <div class="header-avatar">{{ currentCharacter.name[0] }}</div>
        <div class="header-info">
          <div class="header-name">{{ currentCharacter.name }}</div>
          <div class="header-desc">{{ currentCharacter.description }}</div>
        </div>
      </header>

      <!-- Messages -->
      <div class="chat-messages" ref="msgContainer">
        <div v-if="messages.length === 0 && !isStreaming" class="welcome">
          <div class="welcome-avatar">{{ currentCharacter?.name?.[0] || '?' }}</div>
          <h2>{{ currentCharacter?.name || '虚拟女友' }}</h2>
          <p>{{ currentCharacter?.description || '发一条消息开始聊天吧~' }}</p>
        </div>

        <template v-for="m in messages" :key="m.id">
          <MessageBubble
            :role="m.role as 'user' | 'assistant'"
            :content="m.content"
            :time="formatTime(m.created_at)"
            :avatar-name="currentCharacter?.name?.[0]"
          />
        </template>

        <StreamingBubble
          v-if="isStreaming && streamingContent"
          :content="streamingContent"
          :avatar-name="currentCharacter?.name?.[0]"
        />
        <TypingIndicator v-if="isStreaming && !streamingContent" />
      </div>

      <ChatInput @send="onSend" />
    </main>
  </div>

  <!-- Settings Modal -->
  <BaseModal :show="showSettings" title="⚙️ 设置" @close="showSettings = false">
    <div class="form-group">
      <label>DeepSeek API Key</label>
      <input v-model="settingApiKey" type="password" class="form-input" placeholder="sk-..." />
    </div>
    <div class="form-group">
      <label>Base URL</label>
      <input v-model="settingBaseUrl" type="text" class="form-input" />
    </div>
    <div class="form-group">
      <label>模型</label>
      <input v-model="settingModel" type="text" class="form-input" />
    </div>
    <template #footer>
      <button class="btn btn-outline" @click="showSettings = false">取消</button>
      <button class="btn btn-primary" @click="showSettings = false">保存</button>
    </template>
  </BaseModal>

  <!-- Character Modal -->
  <BaseModal :show="showCharModal" title="创建角色" @close="showCharModal = false">
    <div class="form-group">
      <label>角色名</label>
      <input type="text" class="form-input" placeholder="给角色起个名字" />
    </div>
    <div class="form-group">
      <label>描述</label>
      <input type="text" class="form-input" placeholder="一句话描述" />
    </div>
    <div class="form-group">
      <label>角色设定</label>
      <textarea class="form-input" rows="10" placeholder="详细的角色设定..."></textarea>
    </div>
    <template #footer>
      <button class="btn btn-outline" @click="showCharModal = false">取消</button>
      <button class="btn btn-primary" @click="showCharModal = false">保存</button>
    </template>
  </BaseModal>

  <!-- Painting Modal -->
  <BaseModal :show="showPainting" title="🖼️ AI 绘画" @close="showPainting = false">
    <div class="form-group">
      <label>图片描述</label>
      <textarea v-model="paintingPrompt" class="form-input" rows="3" placeholder="描述你想要的画面..."></textarea>
    </div>
    <div v-if="paintingLoading" class="painting-loading">
      <div class="spinner" />
      <p>AI 正在创作中...</p>
    </div>
    <img v-if="paintingUrl" :src="paintingUrl" class="painting-result" alt="AI 生成" />
    <template #footer>
      <button class="btn btn-outline" @click="showPainting = false">关闭</button>
      <button class="btn btn-primary" @click="onGeneratePaint" :disabled="paintingLoading">生成</button>
    </template>
  </BaseModal>
</template>

<style scoped>
.app-shell {
  display: flex; height: 100%;
}

.main-panel {
  flex: 1; height: 100%; display: flex; flex-direction: column;
  min-width: 0; background: var(--color-bg);
}

.chat-header {
  height: var(--header-h); flex-shrink: 0;
  display: flex; align-items: center; gap: 12px;
  padding: 0 20px;
  background: var(--color-surface); border-bottom: 1px solid var(--color-border);
}
.hamburger { display: none; font-size: 20px; padding: 8px; color: var(--color-text-secondary); }
.header-avatar {
  width: 40px; height: 40px; border-radius: 50%;
  background: linear-gradient(135deg, var(--color-primary), var(--color-accent));
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 20px; flex-shrink: 0;
}
.header-info { flex: 1; min-width: 0; }
.header-name { font-size: 16px; font-weight: 600; }
.header-desc { font-size: 12px; color: var(--color-text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.chat-messages {
  flex: 1; overflow-y: auto; padding: 20px 40px;
  display: flex; flex-direction: column; gap: 4px;
  scroll-behavior: smooth;
}

.welcome {
  text-align: center; padding: 80px 20px;
  animation: fadeInUp 0.6s var(--ease-out);
}
.welcome-avatar {
  width: 96px; height: 96px; border-radius: 50%;
  background: linear-gradient(135deg, var(--color-primary), var(--color-accent));
  margin: 0 auto 16px; display: flex; align-items: center; justify-content: center;
  font-size: 48px; color: #fff;
  box-shadow: 0 8px 32px rgba(255,107,157,0.2);
}
.welcome h2 { font-size: 24px; margin-bottom: 4px; }
.welcome p { color: var(--color-text-secondary); }

/* Form */
.form-group { margin-bottom: 14px; }
.form-group label {
  display: block; font-size: 13px; font-weight: 600;
  color: var(--color-text-secondary); margin-bottom: 6px;
}
.form-input {
  width: 100%; padding: 10px 14px; border: 1.5px solid var(--color-border);
  border-radius: var(--radius-xs); font-size: 14px;
  font-family: inherit; outline: none; transition: border-color var(--duration-fast);
  background: var(--color-bg); color: var(--color-text);
}
.form-input:focus {
  border-color: var(--color-primary-light);
  box-shadow: 0 0 0 3px rgba(255,107,157,0.06);
}

/* Painting */
.painting-loading { text-align: center; padding: 24px; }
.spinner {
  width: 36px; height: 36px; border: 3px solid var(--color-border);
  border-top-color: var(--color-primary); border-radius: 50%;
  animation: spin 0.8s linear infinite; margin: 0 auto;
}
@keyframes spin { to { transform: rotate(360deg); } }
.painting-loading p { color: var(--color-text-muted); margin-top: 8px; font-size: 14px; }
.painting-result { width: 100%; border-radius: var(--radius-sm); margin-top: 8px; }

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 768px) {
  .chat-messages { padding: 12px 16px; }
  .hamburger { display: block; }
}
</style>
