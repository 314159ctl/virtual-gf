<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { Plus } from 'lucide-vue-next'
import { useChatStore } from '@/stores/chat'
import { useAuthStore } from '@/stores/auth'
import TopBar from '@/components/layout/TopBar.vue'
import CharacterCard from '@/components/shared/CharacterCard.vue'
import CreateCharacterForm from '@/components/shared/CreateCharacterForm.vue'
import BaseModal from '@/components/shared/BaseModal.vue'

const router = useRouter()
const chat = useChatStore()
const auth = useAuthStore()
const { characters } = storeToRefs(chat)

const showCreateModal = ref(false)
const creating = ref(false)

onMounted(async () => {
  await auth.fetchUser()
  await chat.loadCharacters()
})

async function onSelectCharacter(characterId: string) {
  router.push(`/chat/${characterId}`)
}

async function onCreateCharacter(data: { name: string; description: string; system_prompt: string; personality_profile: Record<string, any> | null; files: File[] }) {
  creating.value = true
  try {
    const char = await chat.createCharacter({
      name: data.name,
      description: data.description,
      system_prompt: data.system_prompt,
      personality_profile: data.personality_profile,
    })
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

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="home-view">
    <TopBar
      :username="auth.user?.username"
      @logout="logout"
    />

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
    <BaseModal :show="showCreateModal" title="创建新角色" @close="showCreateModal = false">
      <CreateCharacterForm
        :disabled="creating"
        @submit="onCreateCharacter"
        @cancel="showCreateModal = false"
      />
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

@media (max-width: 768px) {
  .home-content {
    padding: 16px;
  }
  .char-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 12px;
  }
}
</style>
