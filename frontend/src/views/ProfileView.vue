<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { ArrowLeft, Camera, Edit3, Check, X, ChevronRight, Brain, Star, Trash2, LogOut, RefreshCw, Key, Eye, EyeOff } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'
import api, { uploadApi } from '@/utils/http'

const router = useRouter()
const auth = useAuthStore()
const chat = useChatStore()
const { guestName, userAvatar, hasApiKey, apiBaseUrl, apiModel } = storeToRefs(auth)
const { characters, memories, consolidating } = storeToRefs(chat)

const editingName = ref(false)
const nameInput = ref('')
const avatarInput = ref<HTMLInputElement | null>(null)
const uploading = ref(false)
const showMemories = ref(false)
const selectedCharId = ref<string | null>(null)
const loadingMemories = ref(false)
const editingMemId = ref<string | null>(null)
const editingMemContent = ref('')
const deletingMemId = ref<string | null>(null)

// API Key
const showApiKey = ref(false)
const editingApiKey = ref(false)
const apiKeyInput = ref('')
const savingApiKey = ref(false)
const showKeyValue = ref(false)
const testing = ref(false)
const testResult = ref<string | null>(null)
const testOk = ref(false)

onMounted(async () => {
  await auth.loadUserInfo()
  await chat.loadCharacters()
})

function goBack() {
  router.back()
}

function triggerAvatar() {
  avatarInput.value?.click()
}

async function uploadAvatar(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  uploading.value = true
  try {
    const form = new FormData()
    form.append('file', file)
    const res = await uploadApi.post<{ avatar_url: string | null }>('/users/me/avatar', form)
    userAvatar.value = res.data.avatar_url
  } catch {
    // silently fail
  } finally {
    uploading.value = false
    target.value = ''
  }
}

function startEditName() {
  nameInput.value = guestName.value
  editingName.value = true
}

async function saveName() {
  if (nameInput.value.trim() && nameInput.value !== guestName.value) {
    await auth.updateProfile({ username: nameInput.value.trim() })
  }
  editingName.value = false
}

function cancelEditName() {
  editingName.value = false
}

async function toggleMemories() {
  showMemories.value = !showMemories.value
  if (showMemories.value && !selectedCharId.value && characters.value.length > 0) {
    selectedCharId.value = characters.value[0].id
    await loadMemForChar(characters.value[0].id)
  }
}

async function onSelectChar(charId: string) {
  selectedCharId.value = charId
  await loadMemForChar(charId)
}

async function loadMemForChar(charId: string) {
  loadingMemories.value = true
  await chat.loadMemories(charId)
  loadingMemories.value = false
}

function startEditMem(m: { id: string; content: string }) {
  editingMemId.value = m.id
  editingMemContent.value = m.content
}

async function saveEditMem(id: string) {
  if (!editingMemContent.value.trim()) return
  await chat.updateMemory(id, { content: editingMemContent.value.trim() })
  editingMemId.value = null
}

async function confirmDeleteMem(id: string) {
  await chat.deleteMemory(id)
  deletingMemId.value = null
}

async function setMemImportance(id: string, importance: number) {
  await chat.updateMemory(id, { importance })
}

function doLogout() {
  auth.logout()
  router.push('/auth')
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

function toggleApiKey() {
  showApiKey.value = !showApiKey.value
  if (!showApiKey.value) {
    editingApiKey.value = false
    apiKeyInput.value = ''
    showKeyValue.value = false
  }
}

function startEditApiKey() {
  apiKeyInput.value = ''
  editingApiKey.value = true
  showKeyValue.value = false
}

async function saveApiKey() {
  if (!apiKeyInput.value.trim()) return
  savingApiKey.value = true
  try {
    await auth.updateProfile({ api_key: apiKeyInput.value.trim() })
    editingApiKey.value = false
    apiKeyInput.value = ''
  } catch {
    // silently fail
  } finally {
    savingApiKey.value = false
  }
}

function cancelEditApiKey() {
  editingApiKey.value = false
  apiKeyInput.value = ''
}

// 厂商预设
const VENDOR_PRESETS = [
  { name: 'DeepSeek', base_url: 'https://api.deepseek.com/v1', model: 'deepseek-chat' },
  { name: '硅基流动 (DeepSeek-V3)', base_url: 'https://api.siliconflow.cn/v1', model: 'deepseek-ai/DeepSeek-V3' },
  { name: '硅基流动 (Qwen2.5)', base_url: 'https://api.siliconflow.cn/v1', model: 'Qwen/Qwen2.5-72B-Instruct' },
  { name: 'OpenAI', base_url: 'https://api.openai.com/v1', model: 'gpt-4o' },
]

const editingConfig = ref(false)
const configBaseUrl = ref('')
const configModel = ref('')
const selectedVendor = ref('')

function startEditConfig() {
  configBaseUrl.value = apiBaseUrl.value || ''
  configModel.value = apiModel.value || ''
  selectedVendor.value = ''
  editingConfig.value = true
}

function selectVendor(preset: typeof VENDOR_PRESETS[number]) {
  configBaseUrl.value = preset.base_url
  configModel.value = preset.model
  selectedVendor.value = preset.name
}

async function saveConfig() {
  savingApiKey.value = true
  try {
    await auth.updateProfile({
      api_base_url: configBaseUrl.value.trim() || undefined,
      api_model: configModel.value.trim() || undefined,
    })
    editingConfig.value = false
  } finally {
    savingApiKey.value = false
  }
}

function cancelEditConfig() {
  editingConfig.value = false
}

async function testConnection() {
  testing.value = true
  testResult.value = null
  try {
    const { data } = await api.post<{ status: string; model: string; base_url: string }>('/users/me/test-api')
    testOk.value = true
    testResult.value = `连接成功 (${data.model})`
    setTimeout(() => { testResult.value = null }, 5000)
    return data
  } catch (e: any) {
    testOk.value = false
    testResult.value = e.response?.data?.detail || '连接失败，请检查配置'
    setTimeout(() => { testResult.value = null }, 8000)
  } finally {
    testing.value = false
  }
}
</script>

<template>
  <div class="profile-view">
    <!-- 顶栏 -->
    <header class="profile-header">
      <button class="back-btn" @click="goBack">
        <ArrowLeft :size="20" />
      </button>
      <h1 class="header-title">个人中心</h1>
      <div class="header-spacer" />
    </header>

    <div class="profile-content">
      <!-- 个人信息卡 -->
      <div class="card profile-card">
        <div class="avatar-section" @click="triggerAvatar" :class="{ uploading }">
          <img v-if="userAvatar" :src="userAvatar" class="profile-avatar-img" alt="" />
          <span v-else class="profile-avatar-text">{{ guestName?.[0] || '?' }}</span>
          <div class="avatar-edit-overlay">
            <Camera :size="16" />
          </div>
        </div>
        <input
          ref="avatarInput"
          type="file"
          accept="image/jpeg,image/png,image/webp,image/gif"
          class="file-input-hidden"
          @change="uploadAvatar"
        />

        <div class="name-row">
          <template v-if="editingName">
            <input
              v-model="nameInput"
              class="name-input"
              maxlength="12"
              @keyup.enter="saveName"
              @keyup.escape="cancelEditName"
            />
            <button class="icon-btn save" @click="saveName"><Check :size="16" /></button>
            <button class="icon-btn" @click="cancelEditName"><X :size="16" /></button>
          </template>
          <template v-else>
            <span class="profile-name">{{ guestName }}</span>
            <button class="edit-btn" @click="startEditName"><Edit3 :size="14" /></button>
          </template>
        </div>

        <p class="profile-hint">点击头像更换照片，点击编辑按钮修改昵称</p>
      </div>

      <!-- API Key -->
      <div class="card api-key-card" @click="!showApiKey && (showApiKey = true)">
        <div class="card-row" @click="toggleApiKey">
          <div class="card-row-left">
            <Key :size="18" />
            <span>API Key</span>
            <span v-if="hasApiKey" class="api-badge">已设置</span>
            <span v-else class="api-badge empty">未设置</span>
          </div>
          <ChevronRight :size="18" class="chevron" :class="{ open: showApiKey }" />
        </div>
        <p class="mem-entry-hint">设置你的 DeepSeek API Key，不设置则无法使用 AI 功能</p>

        <div v-if="showApiKey" class="api-key-panel" @click.stop>
          <!-- Key 设置 -->
          <template v-if="!editingApiKey">
            <div v-if="hasApiKey" class="api-key-row">
              <div class="api-key-display">
                <span v-if="showKeyValue" class="api-key-value">sk-••••••••（已加密存储）</span>
                <span v-else class="api-key-masked">••••••••••••</span>
                <button class="toggle-key-btn" @click="showKeyValue = !showKeyValue">
                  <Eye v-if="!showKeyValue" :size="14" />
                  <EyeOff v-else :size="14" />
                </button>
              </div>
              <button class="change-key-btn" @click="startEditApiKey">更换</button>
            </div>
            <div v-else class="api-key-empty">
              <p>尚未设置 API Key，无法使用 AI 功能</p>
              <button class="set-key-btn" @click="startEditApiKey">立即设置</button>
            </div>
          </template>
          <template v-else>
            <div class="api-key-edit">
              <input
                v-model="apiKeyInput"
                type="password"
                class="api-key-input"
                placeholder="输入 API Key (sk-...)"
                @keyup.enter="saveApiKey"
                @keyup.escape="cancelEditApiKey"
              />
              <div class="api-key-actions">
                <button class="icon-btn save" :disabled="savingApiKey" @click="saveApiKey">
                  <Check :size="16" />
                </button>
                <button class="icon-btn" @click="cancelEditApiKey">
                  <X :size="16" />
                </button>
              </div>
            </div>
            <p class="api-key-hint">Key 将加密存储，不会明文保存</p>
          </template>

          <!-- 模型配置 -->
          <div class="config-divider" />
          <template v-if="!editingConfig">
            <div class="config-display">
              <div class="config-item">
                <span class="config-label">接口地址</span>
                <span class="config-value">{{ apiBaseUrl || '默认' }}</span>
              </div>
              <div class="config-item">
                <span class="config-label">模型</span>
                <span class="config-value">{{ apiModel || '默认' }}</span>
              </div>
              <button class="change-key-btn" @click="startEditConfig">修改</button>
              <button class="test-btn" :disabled="testing" @click="testConnection">
                {{ testing ? '测试中...' : '测试连接' }}
              </button>
            </div>
            <div v-if="testResult" class="test-result" :class="{ ok: testOk, fail: !testOk }">
              {{ testResult }}
            </div>
          </template>
          <template v-else>
            <!-- 厂商快捷选项 -->
            <div class="vendor-presets">
              <span class="config-label">快捷选择</span>
              <div class="vendor-chips">
                <button
                  v-for="p in VENDOR_PRESETS"
                  :key="p.name"
                  class="vendor-chip"
                  :class="{ active: selectedVendor === p.name }"
                  @click="selectVendor(p)"
                >{{ p.name }}</button>
              </div>
            </div>
            <div class="config-edit">
              <div class="config-field">
                <span class="config-label">接口地址</span>
                <input
                  v-model="configBaseUrl"
                  class="config-input"
                  placeholder="https://api.deepseek.com/v1"
                />
              </div>
              <div class="config-field">
                <span class="config-label">模型名</span>
                <input
                  v-model="configModel"
                  class="config-input"
                  placeholder="deepseek-chat"
                />
              </div>
              <div class="config-actions">
                <button class="icon-btn save" :disabled="savingApiKey" @click="saveConfig">
                  <Check :size="16" />
                </button>
                <button class="icon-btn" @click="cancelEditConfig">
                  <X :size="16" />
                </button>
                <button class="test-btn" :disabled="testing" @click="testConnection">
                  {{ testing ? '测试中...' : '测试连接' }}
                </button>
              </div>
              <div v-if="testResult" class="test-result" :class="{ ok: testOk, fail: !testOk }">
                {{ testResult }}
              </div>
            </div>
          </template>
        </div>
      </div>

      <!-- 记忆管理 -->
      <div class="card memory-entry-card" @click="toggleMemories">
        <div class="card-row">
          <div class="card-row-left">
            <Brain :size="18" />
            <span>记忆管理</span>
          </div>
          <ChevronRight :size="18" class="chevron" :class="{ open: showMemories }" />
        </div>
        <p class="mem-entry-hint">查看和管理角色的长期记忆</p>
      </div>

      <div v-if="showMemories" class="card memory-panel">
        <!-- 角色选择 -->
        <div class="char-select">
          <button
            v-for="char in characters"
            :key="char.id"
            class="char-chip"
            :class="{ active: selectedCharId === char.id }"
            @click.stop="onSelectChar(char.id)"
          >
            {{ char.name }}
          </button>
        </div>

        <!-- 记忆操作 -->
        <div class="mem-toolbar">
          <button
            class="consolidate-btn"
            :disabled="consolidating"
            @click.stop="selectedCharId && chat.consolidateMemories(selectedCharId)"
          >
            <RefreshCw :size="13" :class="{ spinning: consolidating }" />
            <span>{{ consolidating ? '合并中...' : '手动合并记忆' }}</span>
          </button>
        </div>

        <!-- 记忆列表 -->
        <div v-if="loadingMemories" class="mem-empty">加载中...</div>
        <div v-else-if="memories.length === 0" class="mem-empty">暂无记忆</div>
        <div v-else class="mem-list">
          <div v-for="m in memories" :key="m.id" class="mem-card">
            <div class="mem-stars">
              <button
                v-for="n in 5" :key="n"
                class="star-btn"
                :class="{ active: n <= m.importance }"
                @click.stop="setMemImportance(m.id, n)"
              >
                <Star :size="12" :fill="n <= m.importance ? 'currentColor' : 'none'" />
              </button>
            </div>
            <div class="mem-content" v-if="editingMemId !== m.id">{{ m.content }}</div>
            <textarea
              v-else v-model="editingMemContent"
              class="mem-edit-input" rows="2"
              @keyup.escape="editingMemId = null"
            />
            <div class="mem-actions">
              <span class="mem-date">{{ formatDate(m.created_at) }}</span>
              <template v-if="editingMemId === m.id">
                <button class="act-btn save" @click.stop="saveEditMem(m.id)"><Check :size="14" /></button>
                <button class="act-btn" @click.stop="editingMemId = null"><X :size="14" /></button>
              </template>
              <template v-else>
                <button class="act-btn" @click.stop="startEditMem(m)"><Edit3 :size="13" /></button>
                <button v-if="deletingMemId === m.id" class="act-btn danger confirm" @click.stop="confirmDeleteMem(m.id)">确认</button>
                <button v-else class="act-btn" @click.stop="deletingMemId = m.id"><Trash2 :size="13" /></button>
              </template>
            </div>
          </div>
        </div>
      </div>

      <!-- 退出 -->
      <div class="card logout-card" @click="doLogout">
        <div class="card-row">
          <div class="card-row-left" style="color: var(--color-error)">
            <LogOut :size="18" />
            <span>退出账号</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.profile-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-bg);
}

/* ── Header ── */
.profile-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: var(--header-h);
  background: var(--header-gradient);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}
.header-title {
  font-family: var(--font-heading);
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--color-text);
}
.header-spacer { width: 36px; }
.back-btn {
  width: 36px; height: 36px;
  border-radius: var(--radius-sm);
  display: flex; align-items: center; justify-content: center;
  color: var(--color-text-secondary);
  border: none; background: transparent; cursor: pointer;
  transition: all var(--duration-fast) var(--ease-smooth);
}
.back-btn:hover { background: var(--color-sakura); color: var(--color-primary); }

/* ── Content ── */
.profile-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* ── Card ── */
.card {
  background: var(--color-surface);
  border-radius: var(--radius);
  padding: 20px;
  border: 1px solid var(--color-border);
}
.card-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
}
.card-row-left {
  display: flex; align-items: center; gap: 10px;
  font-size: var(--text-sm); font-weight: 500; color: var(--color-text);
}

/* ── Profile Card ── */
.profile-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 28px 20px;
}
.avatar-section {
  width: 72px; height: 72px;
  border-radius: var(--radius-full);
  background: var(--avatar-gradient-2);
  display: flex; align-items: center; justify-content: center;
  position: relative; cursor: pointer; overflow: hidden;
  flex-shrink: 0;
}
.avatar-section.uploading { opacity: 0.6; pointer-events: none; }
.profile-avatar-img {
  width: 100%; height: 100%;
  border-radius: inherit; object-fit: cover;
}
.profile-avatar-text {
  font-size: 28px; font-weight: 700; color: #fff; font-family: var(--font-heading);
}
.avatar-edit-overlay {
  position: absolute; inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center;
  opacity: 0; transition: opacity var(--duration-fast);
  border-radius: inherit; color: #fff;
}
.avatar-section:hover .avatar-edit-overlay { opacity: 1; }
.file-input-hidden { display: none; }

.name-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding-left: 28px; /* 补偿编辑按钮宽度，让文字视觉居中 */
}
.profile-name {
  font-family: var(--font-heading);
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--color-text);
}
.edit-btn {
  width: 24px; height: 24px;
  border: none; border-radius: var(--radius-xs);
  display: flex; align-items: center; justify-content: center;
  background: transparent; color: var(--color-text-muted); cursor: pointer;
  transition: all var(--duration-fast);
  flex-shrink: 0;
}
.edit-btn:hover { background: var(--color-sakura-light); color: var(--color-text); }
.name-input {
  padding: 4px 10px;
  border: 1.5px solid var(--color-primary);
  border-radius: var(--radius-xs);
  font-size: var(--text-base);
  font-family: var(--font-body);
  color: var(--color-text);
  background: var(--color-bg);
  outline: none;
  width: 160px;
}
.profile-hint {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}
.icon-btn {
  width: 28px; height: 28px;
  border: none; border-radius: var(--radius-xs);
  display: flex; align-items: center; justify-content: center;
  background: transparent; color: var(--color-text-muted); cursor: pointer;
  transition: all var(--duration-fast);
}
.icon-btn:hover { background: var(--color-sakura-light); color: var(--color-text); }
.icon-btn.save { color: var(--color-success); }

/* ── Chevron ── */
.chevron {
  color: var(--color-text-muted);
  transition: transform var(--duration) var(--ease-smooth);
}
.chevron.open { transform: rotate(90deg); }

/* ── Memory Entry ── */
.memory-entry-card {
  border: 1.5px solid var(--color-primary-light);
  background: var(--color-sakura-light);
}
.mem-entry-hint {
  margin-top: 6px;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  padding-left: 28px;
}

/* ── Memory Panel ── */
.memory-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.char-select {
  display: flex; gap: 8px; flex-wrap: wrap;
}
.char-chip {
  padding: 4px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-family: var(--font-body);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--duration-fast);
}
.char-chip.active,
.char-chip:hover {
  border-color: var(--color-primary);
  background: var(--color-sakura-light);
  color: var(--color-primary);
}

.mem-toolbar {
  display: flex; justify-content: flex-end;
}
.consolidate-btn {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 14px;
  border: 1.5px solid var(--color-primary-light);
  border-radius: var(--radius-full);
  background: var(--color-sakura);
  color: var(--color-primary-dark);
  font-size: var(--text-xs);
  font-family: var(--font-body);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-smooth);
}
.consolidate-btn:hover:not(:disabled) {
  background: var(--color-primary-light);
  color: #fff;
}
.consolidate-btn:disabled {
  opacity: 0.6; cursor: not-allowed;
}
.spinning { animation: spin 1s linear infinite; }

@keyframes spin {
  to { transform: rotate(360deg); }
}

.mem-empty {
  text-align: center; padding: 24px;
  font-size: var(--text-sm); color: var(--color-text-muted);
}

.mem-list {
  display: flex; flex-direction: column; gap: 8px;
}
.mem-card {
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 10px 12px;
}
.mem-stars {
  display: flex; gap: 2px; margin-bottom: 4px;
}
.star-btn {
  display: flex; padding: 0; border: none; background: none;
  color: var(--color-border); cursor: pointer;
  transition: all var(--duration-fast) var(--ease-bounce);
}
.star-btn.active { color: var(--color-gold); }
.star-btn:hover { transform: scale(1.2); color: var(--color-gold); }

.mem-content {
  font-size: var(--text-sm); color: var(--color-text); line-height: 1.5;
}
.mem-edit-input {
  width: 100%; padding: 6px 8px;
  border: 1.5px solid var(--color-primary);
  border-radius: var(--radius-xs);
  font-size: var(--text-sm); font-family: var(--font-body);
  line-height: 1.5; outline: none; resize: vertical;
  box-sizing: border-box; background: var(--color-bg); color: var(--color-text);
}
.mem-actions {
  display: flex; align-items: center; gap: 4px; margin-top: 6px;
}
.mem-date {
  font-size: 10px; color: var(--color-text-muted); flex: 1;
}
.act-btn {
  display: flex; align-items: center; justify-content: center;
  width: 24px; height: 24px;
  border: none; border-radius: var(--radius-xs);
  background: transparent; color: var(--color-text-muted); cursor: pointer;
}
.act-btn:hover { background: var(--color-sakura-light); color: var(--color-text); }
.act-btn.save { color: var(--color-success); }
.act-btn.danger { color: var(--color-error); }
.act-btn.confirm { font-size: 10px; width: auto; padding: 0 6px; font-family: var(--font-body); font-weight: 600; }

/* ── API Key ── */
.api-key-card {
  border: 1.5px solid var(--color-primary-light);
  background: var(--color-sakura-light);
}
.api-badge {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-family: var(--font-body);
  font-weight: 600;
  background: var(--color-success-light, #dcfce7);
  color: var(--color-success, #16a34a);
}
.api-badge.empty {
  background: var(--color-warning-light, #fef3c7);
  color: var(--color-warning, #d97706);
}
.api-key-panel {
  margin-top: 12px;
  padding: 14px;
  background: var(--color-bg);
  border-radius: var(--radius-sm);
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.api-key-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.api-key-display {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
}
.api-key-masked,
.api-key-value {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  font-family: monospace;
}
.toggle-key-btn {
  display: flex;
  align-items: center;
  padding: 2px;
  border: none;
  background: none;
  color: var(--color-text-muted);
  cursor: pointer;
  border-radius: var(--radius-xs);
}
.toggle-key-btn:hover { color: var(--color-text); }
.change-key-btn {
  padding: 4px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xs);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  font-size: var(--text-xs);
  cursor: pointer;
  font-family: var(--font-body);
  transition: all var(--duration-fast);
  flex-shrink: 0;
}
.change-key-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}
.api-key-empty {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-start;
}
.api-key-empty p {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  margin: 0;
}
.set-key-btn {
  padding: 6px 16px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--color-primary);
  color: #fff;
  font-size: var(--text-sm);
  font-family: var(--font-body);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--duration-fast);
}
.set-key-btn:hover { opacity: 0.9; }
.api-key-edit {
  display: flex;
  align-items: center;
  gap: 8px;
}
.api-key-input {
  flex: 1;
  padding: 6px 10px;
  border: 1.5px solid var(--color-primary);
  border-radius: var(--radius-xs);
  font-size: var(--text-sm);
  font-family: monospace;
  color: var(--color-text);
  background: var(--color-bg);
  outline: none;
}
.api-key-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}
.api-key-hint {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin: 0;
}

/* ── Config ── */
.config-divider {
  height: 1px;
  background: var(--color-border);
  margin: 4px 0;
}
.config-display {
  display: flex;
  align-items: center;
  gap: 12px;
}
.config-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}
.config-label {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  font-family: var(--font-body);
}
.config-value {
  font-size: var(--text-sm);
  color: var(--color-text);
  font-family: monospace;
  word-break: break-all;
}
.vendor-presets {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.vendor-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.vendor-chip {
  padding: 3px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  font-size: 11px;
  font-family: var(--font-body);
  cursor: pointer;
  transition: all var(--duration-fast);
}
.vendor-chip:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}
.vendor-chip.active {
  background: var(--color-primary);
  color: #fff;
  border-color: var(--color-primary);
}
.config-edit {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.config-field {
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.config-input {
  padding: 5px 8px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xs);
  font-size: var(--text-sm);
  font-family: monospace;
  color: var(--color-text);
  background: var(--color-bg);
  outline: none;
}
.config-input:focus {
  border-color: var(--color-primary);
}
.config-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
}

.test-btn {
  padding: 4px 12px;
  border: 1px solid var(--color-success, #16a34a);
  border-radius: var(--radius-xs);
  background: var(--color-success-light, #dcfce7);
  color: var(--color-success, #16a34a);
  font-size: var(--text-xs);
  font-family: var(--font-body);
  cursor: pointer;
  transition: all var(--duration-fast);
  margin-left: auto;
}
.test-btn:hover:not(:disabled) {
  background: var(--color-success, #16a34a);
  color: #fff;
}
.test-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.test-result {
  font-size: var(--text-xs);
  padding: 4px 8px;
  border-radius: var(--radius-xs);
  margin-top: 4px;
}
.test-result.ok {
  color: var(--color-success, #16a34a);
  background: var(--color-success-light, #dcfce7);
}
.test-result.fail {
  color: var(--color-error, #dc2626);
  background: #fef2f2;
}

/* ── Logout ── */
.logout-card .card-row { cursor: pointer; }
</style>
