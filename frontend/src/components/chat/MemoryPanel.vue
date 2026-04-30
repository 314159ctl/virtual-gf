<script setup lang="ts">
import { ref, watch } from 'vue'
import { Brain, Star, Trash2, Edit3, Check, X } from 'lucide-vue-next'
import { useChatStore } from '@/stores/chat'
import { storeToRefs } from 'pinia'

const props = defineProps<{ show: boolean }>()
const emit = defineEmits<{ close: [] }>()

const chat = useChatStore()
const { memories, currentCharacter } = storeToRefs(chat)

const editingId = ref<string | null>(null)
const editingContent = ref('')
const deletingId = ref<string | null>(null)
const loading = ref(false)

watch(() => props.show, async (v) => {
  if (v && currentCharacter.value) {
    loading.value = true
    await chat.loadMemories(currentCharacter.value.id)
    loading.value = false
  }
})

function startEdit(m: { id: string; content: string }) {
  editingId.value = m.id
  editingContent.value = m.content
}

async function saveEdit(id: string) {
  if (!editingContent.value.trim()) return
  await chat.updateMemory(id, { content: editingContent.value.trim() })
  editingId.value = null
}

function cancelEdit() {
  editingId.value = null
}

async function setImportance(id: string, importance: number) {
  await chat.updateMemory(id, { importance })
}

async function confirmDelete(id: string) {
  await chat.deleteMemory(id)
  deletingId.value = null
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}
</script>

<template>
  <Teleport to="body">
    <Transition name="panel">
      <div v-if="show" class="panel-overlay" @click.self="emit('close')">
        <div class="panel">
          <div class="panel-header">
            <div class="panel-title">
              <Brain :size="18" />
              <span>记忆管理</span>
            </div>
            <button class="panel-close" @click="emit('close')">
              <X :size="18" />
            </button>
          </div>

          <div class="panel-body">
            <p class="panel-desc">
              {{ currentCharacter?.name }}对你的记忆，每 10 条消息自动提取
            </p>

            <div v-if="loading" class="panel-empty">加载中...</div>

            <div v-else-if="memories.length === 0" class="panel-empty">
              暂无记忆，继续聊天以生成记忆
            </div>

            <div v-else class="memory-list">
              <div
                v-for="m in memories"
                :key="m.id"
                class="memory-card"
              >
                <!-- 重要性星级 -->
                <div class="memory-stars">
                  <button
                    v-for="n in 5"
                    :key="n"
                    type="button"
                    class="star-btn"
                    :class="{ active: n <= m.importance }"
                    @click="setImportance(m.id, n)"
                    :title="`重要性 ${n}`"
                  >
                    <Star :size="12" :fill="n <= m.importance ? 'currentColor' : 'none'" />
                  </button>
                </div>

                <!-- 内容 -->
                <div class="memory-content" v-if="editingId !== m.id">
                  {{ m.content }}
                </div>
                <textarea
                  v-else
                  v-model="editingContent"
                  class="memory-edit-input"
                  rows="2"
                />

                <!-- 操作 -->
                <div class="memory-actions">
                  <span class="memory-date">{{ formatDate(m.created_at) }}</span>
                  <template v-if="editingId === m.id">
                    <button class="act-btn save" @click="saveEdit(m.id)" title="保存">
                      <Check :size="14" />
                    </button>
                    <button class="act-btn" @click="cancelEdit" title="取消">
                      <X :size="14" />
                    </button>
                  </template>
                  <template v-else>
                    <button class="act-btn" @click="startEdit(m)" title="编辑">
                      <Edit3 :size="13" />
                    </button>
                    <button
                      v-if="deletingId === m.id"
                      class="act-btn danger confirm"
                      @click="confirmDelete(m.id)"
                      title="确认删除"
                    >
                      确认
                    </button>
                    <button
                      v-else
                      class="act-btn"
                      @click="deletingId = m.id"
                      title="删除"
                    >
                      <Trash2 :size="13" />
                    </button>
                  </template>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.panel-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(74, 37, 53, 0.15);
  display: flex;
  justify-content: flex-end;
}

.panel {
  width: 360px;
  max-width: 90vw;
  height: 100%;
  background: var(--color-bg);
  border-left: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  box-shadow: -4px 0 24px rgba(255, 125, 175, 0.08);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border);
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-heading);
  font-size: var(--text-base);
  font-weight: 700;
  color: var(--color-text);
}

.panel-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: var(--radius-xs);
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
}
.panel-close:hover {
  background: var(--color-sakura-light);
  color: var(--color-text);
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}

.panel-desc {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin-bottom: 16px;
  line-height: 1.5;
}

.panel-empty {
  text-align: center;
  padding: 40px 20px;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.memory-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.memory-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 12px 14px;
  transition: border-color var(--duration-fast);
}
.memory-card:hover {
  border-color: var(--color-border-strong);
}

.memory-stars {
  display: flex;
  gap: 2px;
  margin-bottom: 6px;
}

.star-btn {
  display: flex;
  padding: 0;
  border: none;
  background: none;
  color: var(--color-border);
  cursor: pointer;
  transition: color var(--duration-fast), transform var(--duration-fast) var(--ease-bounce);
}
.star-btn.active {
  color: var(--color-gold);
}
.star-btn:hover {
  transform: scale(1.2);
  color: var(--color-gold);
}

.memory-content {
  font-size: var(--text-sm);
  color: var(--color-text);
  line-height: 1.6;
}

.memory-edit-input {
  width: 100%;
  padding: 6px 8px;
  border: 1.5px solid var(--color-primary);
  border-radius: var(--radius-xs);
  font-size: var(--text-sm);
  font-family: var(--font-body);
  line-height: 1.5;
  outline: none;
  resize: vertical;
  box-sizing: border-box;
  background: var(--color-bg);
  color: var(--color-text);
}

.memory-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
}

.memory-date {
  font-size: 10px;
  color: var(--color-text-muted);
  flex: 1;
}

.act-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  border-radius: var(--radius-xs);
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
}
.act-btn:hover {
  background: var(--color-sakura-light);
  color: var(--color-text);
}
.act-btn.save {
  color: var(--color-success);
}
.act-btn.danger {
  color: var(--color-error);
}
.act-btn.confirm {
  font-size: 10px;
  width: auto;
  padding: 0 6px;
  font-family: var(--font-body);
  font-weight: 600;
}

/* ── Transition ── */
.panel-enter-active, .panel-leave-active {
  transition: opacity var(--duration) var(--ease-smooth);
}
.panel-enter-active .panel, .panel-leave-active .panel {
  transition: transform var(--duration) var(--ease-smooth);
}
.panel-enter-from, .panel-leave-to {
  opacity: 0;
}
.panel-enter-from .panel, .panel-leave-to .panel {
  transform: translateX(100%);
}
</style>
