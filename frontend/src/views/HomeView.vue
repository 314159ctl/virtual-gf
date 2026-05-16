<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { Plus } from 'lucide-vue-next'
import { useChatStore } from '@/stores/chat'
import { useAuthStore } from '@/stores/auth'
import TopBar from '@/components/layout/TopBar.vue'
import CharacterCard from '@/components/shared/CharacterCard.vue'
import CreateCharacterForm from '@/components/shared/CreateCharacterForm.vue'
import BaseModal from '@/components/shared/BaseModal.vue'
import type { Character } from '@/types/models'

const router = useRouter()
const chat = useChatStore()
const auth = useAuthStore()
const { characters } = storeToRefs(chat)

const showCreateModal = ref(false)
const creating = ref(false)

// 删除确认
const charToDelete = ref<Character | null>(null)
const showDeleteModal = computed(() => charToDelete.value !== null)
const deleting = ref(false)
const deleteError = ref('')

onMounted(async () => {
  await chat.loadCharacters()
  await auth.loadUserInfo()
})

async function onSelectCharacter(characterId: string) {
  router.push(`/chat/${characterId}`)
}

function onDeleteRequest(char: Character) {
  charToDelete.value = char
  deleteError.value = ''
}

async function confirmDelete() {
  if (!charToDelete.value) return
  deleting.value = true
  deleteError.value = ''
  try {
    await chat.deleteCharacter(charToDelete.value.id)
    charToDelete.value = null
  } catch (e: any) {
    deleteError.value = e?.response?.data?.detail || e?.message || '删除失败，请重试'
  } finally {
    deleting.value = false
  }
}

function cancelDelete() {
  charToDelete.value = null
  deleteError.value = ''
}

async function onCreateCharacter(data: { name: string; description: string; system_prompt: string; personality_profile: Record<string, any> | null; files: File[]; avatarFile: File | null }) {
  creating.value = true
  try {
    const char = await chat.createCharacter({
      name: data.name,
      description: data.description,
      system_prompt: data.system_prompt,
      personality_profile: data.personality_profile,
    })
    if (data.avatarFile) {
      await chat.uploadAvatar(char.id, data.avatarFile)
    }
    if (data.files.length > 0) {
      await chat.uploadCharacterDocuments(char.id, data.files)
    }
    showCreateModal.value = false
    router.push(`/chat/${char.id}`)
  } catch (e) {
    console.error('创建角色失败:', e)
  } finally {
    creating.value = false
  }
}

</script>

<template>
  <div class="home-view">
    <TopBar />

    <div class="home-content">
      <div class="home-header">
        <h2 class="home-title">选择你的角色</h2>
        <p class="home-subtitle">点击角色卡片开始对话</p>
      </div>

      <div class="char-grid">
        <CharacterCard
          v-for="char in characters"
          :key="char.id"
          :character="char"
          @select="onSelectCharacter(char.id)"
          @delete-request="onDeleteRequest(char)"
        />

        <!-- 创建角色卡片 -->
        <div class="create-card" @click="showCreateModal = true">
          <div class="create-icon">
            <Plus :size="32" />
          </div>
          <span class="create-text">创建新角色</span>
        </div>
      </div>
    </div>

    <!-- 创建角色弹窗 -->
    <BaseModal :show="showCreateModal" title="创建新角色" :closeOnOverlay="false" @close="showCreateModal = false">
      <CreateCharacterForm
        :disabled="creating"
        @submit="onCreateCharacter"
        @cancel="showCreateModal = false"
      />
    </BaseModal>

    <!-- 删除确认弹窗 -->
    <BaseModal :show="showDeleteModal" title="删除角色" @close="cancelDelete">
      <p class="delete-confirm-text">
        真的要抛弃<strong>{{ charToDelete?.name }}</strong>吗 (´；ω；`)
      </p>
      <p class="delete-confirm-hint">删掉的话…就再也见不到了哦…那些回忆也会一起消失的…求求你不要丢下我嘛 (⋟﹏⋞)</p>
      <p v-if="deleteError" class="delete-error">{{ deleteError }}</p>
      <template #footer>
        <button class="btn btn-cancel" @click="cancelDelete" :disabled="deleting">取消</button>
        <button class="btn btn-delete" @click="confirmDelete" :disabled="deleting">
          {{ deleting ? '删除中...' : '确认删除' }}
        </button>
      </template>
    </BaseModal>
  </div>
</template>

<style scoped>
.home-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-bg);
}

.home-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;
}

.home-header {
  margin-bottom: 28px;
}

.home-title {
  font-family: var(--font-heading);
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: 6px;
}

.home-subtitle {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.char-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
}

/* 创建角色卡片 */
.create-card {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  border: 2px dashed var(--color-border-strong);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  min-height: 260px;
  cursor: pointer;
  transition: all var(--duration) var(--ease-bounce);
}
.create-card:hover {
  border-color: var(--color-primary);
  background: var(--color-sakura-light);
  transform: translateY(-2px);
}

.create-icon {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-full);
  background: var(--color-sakura);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-primary);
  transition: all var(--duration-fast);
}
.create-card:hover .create-icon {
  background: var(--color-primary);
  color: #fff;
}

.create-text {
  font-family: var(--font-heading);
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  font-weight: 500;
}
.create-card:hover .create-text {
  color: var(--color-primary);
}

/* ── 删除确认弹窗 ── */
.delete-confirm-text {
  font-size: var(--text-sm);
  color: var(--color-text);
  line-height: 1.6;
  margin-bottom: 8px;
}
.delete-confirm-hint {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}
.delete-error {
  margin-top: 10px;
  padding: 8px 12px;
  background: rgba(232,128,138,0.1);
  border: 1px solid rgba(232,128,138,0.2);
  border-radius: var(--radius-xs);
  font-size: var(--text-xs);
  color: var(--color-error);
}

.btn {
  padding: 8px 20px;
  border: none;
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  font-family: var(--font-body);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-smooth);
}
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn-cancel {
  background: var(--color-bg);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border);
}
.btn-cancel:hover:not(:disabled) {
  background: var(--color-sakura-light);
}
.btn-delete {
  background: var(--color-error);
  color: #fff;
}
.btn-delete:hover:not(:disabled) {
  background: #c0392b;
}

@media (max-width: 768px) {
  .home-content {
    padding: 16px;
  }
  .char-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 12px;
  }
  .home-title {
    font-size: var(--text-xl);
  }
}

@media (max-width: 480px) {
  .home-content {
    padding: 12px;
  }
  .char-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }
  .create-card {
    min-height: 200px;
  }
}
</style>
