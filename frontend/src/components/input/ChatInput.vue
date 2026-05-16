<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Send, Image as ImageIcon, Smile } from 'lucide-vue-next'
import { useImageUpload } from '@/composables/useImageUpload'
import EmojiPicker from './EmojiPicker.vue'
import ImagePreviewTag from './ImagePreviewTag.vue'

const emit = defineEmits<{
  send: [message: string, image: string | null]
}>()

const text = ref('')
const { selectedImage, previewUrl, fileInput, selectFile, onFileSelected, onPaste, clearImage } = useImageUpload()

const showQuickActions = ref(false)
const showEmoji = ref(false)
const emojiArea = ref<HTMLElement | null>(null)
const textareaRef = ref<HTMLTextAreaElement | null>(null)

function insertEmoji(emoji: string) {
  const el = textareaRef.value
  if (!el) return
  const start = el.selectionStart
  const end = el.selectionEnd
  text.value = text.value.slice(0, start) + emoji + text.value.slice(end)
  // 恢复光标位置（等 Vue 更新 DOM 后）
  requestAnimationFrame(() => {
    const pos = start + emoji.length
    el.focus()
    el.setSelectionRange(pos, pos)
  })
}

function toggleEmoji() {
  showEmoji.value = !showEmoji.value
}

function onEmojiSelect(emoji: string) {
  insertEmoji(emoji)
}

function onClickOutside(e: MouseEvent) {
  if (emojiArea.value && !emojiArea.value.contains(e.target as Node)) {
    showEmoji.value = false
  }
}

onMounted(() => document.addEventListener('click', onClickOutside))
onUnmounted(() => document.removeEventListener('click', onClickOutside))

const quickActions = ['我好想你呀', '在忙什么呢', '拍张自拍给我看看', '最近有什么开心的事吗']

const canSend = computed(() => text.value.trim().length > 0 || selectedImage.value !== null)

function onQuickAction(msg: string) {
  emit('send', msg, null)
  showQuickActions.value = false
}

function onSubmit() {
  if (!canSend.value) return
  emit('send', text.value.trim(), selectedImage.value)
  text.value = ''
  clearImage()
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    onSubmit()
  }
}
</script>

<template>
  <div class="chat-input-area">
    <!-- 图片预览 -->
    <ImagePreviewTag v-if="previewUrl" :url="previewUrl" @remove="clearImage" />

    <!-- 快速操作 -->
    <div v-if="showQuickActions" class="quick-actions">
      <button
        v-for="qa in quickActions"
        :key="qa"
        type="button"
        class="qa-chip"
        @click="onQuickAction(qa)"
      >
        {{ qa }}
      </button>
    </div>

    <!-- 输入行 -->
    <div class="input-row">
      <div class="emoji-area" ref="emojiArea">
        <button class="tool-btn" @click="toggleEmoji" title="表情">
          <Smile :size="20" />
        </button>
        <EmojiPicker v-if="showEmoji" class="emoji-popover" @select="onEmojiSelect" />
      </div>

      <button class="tool-btn" @click="selectFile" title="发送图片">
        <ImageIcon :size="20" />
      </button>
      <input
        type="file"
        ref="fileInput"
        accept="image/*"
        hidden
        @change="onFileSelected"
      />

      <div class="input-wrapper">
        <textarea
          ref="textareaRef"
          v-model="text"
          class="input-field"
          rows="1"
          placeholder="请输入想要对她说的话..."
          maxlength="2000"
          @keydown="onKeydown"
          @paste="onPaste"
        />
      </div>

      <button
        class="send-btn"
        :class="{ ready: canSend }"
        :disabled="!canSend"
        @click="onSubmit"
      >
        <Send :size="20" />
      </button>
    </div>

    <div class="input-footer">
      <button type="button" class="qa-toggle" @click="showQuickActions = !showQuickActions">
        {{ showQuickActions ? '收起' : '快捷消息' }}
      </button>
      <div class="input-hint">Enter 发送 · Shift + Enter 换行</div>
    </div>
  </div>
</template>

<style scoped>
.chat-input-area {
  flex-shrink: 0;
  padding: 12px 20px 14px;
  background: var(--color-surface);
  border-top: 1px solid var(--color-border);
}

.input-row {
  display: flex;
  align-items: flex-end;
  gap: 8px;
}

.tool-btn {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
  background: var(--color-bg);
  border: 1.5px solid var(--color-border);
  flex-shrink: 0;
  transition: all var(--duration-fast) var(--ease-smooth);
}
.tool-btn:hover {
  border-color: var(--color-primary-light);
  color: var(--color-primary);
  background: var(--color-sakura-light);
}

.input-wrapper {
  flex: 1;
  background: var(--color-bg);
  border: 1.5px solid var(--color-border);
  border-radius: var(--radius);
  transition: all var(--duration-fast) var(--ease-smooth);
  overflow: hidden;
}
.input-wrapper:focus-within {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 4px rgba(255,125,175,0.06);
}

.input-field {
  width: 100%;
  resize: none;
  border: none;
  padding: 11px 16px;
  font-size: 15px;
  font-family: var(--font-body);
  line-height: 1.6;
  outline: none;
  background: transparent;
  color: var(--color-text);
  max-height: 120px;
}
.input-field::placeholder {
  color: var(--color-text-muted);
  font-weight: 400;
}

.send-btn {
  width: 42px;
  height: 42px;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
  background: var(--color-bubble-ai);
  color: var(--color-text-muted);
  border: 1.5px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-bounce);
}
.send-btn:hover:not(:disabled) {
  background: var(--color-sakura);
  color: var(--color-primary);
  border-color: var(--color-primary-light);
}
.send-btn.ready {
  background: var(--avatar-gradient-1);
  color: #fff;
  border-color: transparent;
  box-shadow: var(--shadow-sm);
}
.send-btn.ready:hover {
  transform: scale(1.06);
  box-shadow: var(--shadow-md);
}
.send-btn:disabled {
  cursor: not-allowed;
  transform: none;
}

/* ── Quick actions ── */
.quick-actions {
  display: flex;
  gap: 6px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.qa-chip {
  padding: 4px 12px;
  background: var(--color-sakura-light);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  font-size: 11px;
  font-family: var(--font-body);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-bounce);
}
.qa-chip:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: var(--color-sakura);
  transform: translateY(-1px);
}

.input-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 6px;
  padding-right: 4px;
}

.qa-toggle {
  border: none;
  background: none;
  font-size: 10px;
  font-family: var(--font-body);
  color: var(--color-text-muted);
  cursor: pointer;
  padding: 2px 4px;
  border-radius: var(--radius-xs);
  transition: color var(--duration-fast);
}
.qa-toggle:hover {
  color: var(--color-primary);
}

.input-hint {
  font-size: 10px;
  font-family: var(--font-body);
  color: var(--color-text-muted);
}

/* ── Emoji ── */
.emoji-area {
  position: relative;
}
.emoji-popover {
  position: absolute;
  bottom: 48px;
  left: 0;
  z-index: 100;
}
</style>
