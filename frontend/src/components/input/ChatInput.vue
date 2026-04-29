<script setup lang="ts">
import { ref } from 'vue'

const text = ref('')
const emit = defineEmits<{
  send: [message: string, image: string | null]
}>()

function onSubmit() {
  const msg = text.value.trim()
  if (!msg) return
  emit('send', msg, null)
  text.value = ''
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    onSubmit()
  }
}
</script>

<template>
  <div class="input-area">
    <div class="input-row">
      <textarea
        v-model="text"
        class="input-field"
        rows="1"
        placeholder="输入消息..."
        maxlength="2000"
        @keydown="onKeydown"
      />
      <button class="send-btn" @click="onSubmit" :disabled="!text.trim()">➤</button>
    </div>
    <div class="input-hint">Enter 发送 · Shift+Enter 换行</div>
  </div>
</template>

<style scoped>
.input-area {
  flex-shrink: 0; padding: 12px 20px 16px;
  background: var(--color-surface); border-top: 1px solid var(--color-border);
}
.input-row { display: flex; align-items: flex-end; gap: 6px; }
.input-field {
  flex: 1; resize: none; border: 1.5px solid var(--color-border);
  border-radius: 24px; padding: 11px 18px; font-size: 15px;
  font-family: inherit; line-height: 1.5; outline: none;
  transition: border-color var(--duration-fast);
  background: var(--color-bg); color: var(--color-text);
  max-height: 120px;
}
.input-field:focus {
  border-color: var(--color-primary-light);
  box-shadow: 0 0 0 3px rgba(255,107,157,0.08);
}
.input-field::placeholder { color: var(--color-text-muted); }
.send-btn {
  width: 42px; height: 42px; border-radius: 50%; flex-shrink: 0;
  background: var(--color-primary); color: #fff; font-size: 18px;
  display: flex; align-items: center; justify-content: center;
  transition: all var(--duration-fast);
}
.send-btn:hover { background: var(--color-primary-dark); transform: scale(1.05); }
.send-btn:disabled { background: #ddd; cursor: not-allowed; transform: none; }
.input-hint {
  font-size: 11px; color: var(--color-text-muted);
  text-align: right; margin-top: 6px; padding-right: 52px;
}
</style>
