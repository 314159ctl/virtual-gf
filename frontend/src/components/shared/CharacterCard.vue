<script setup lang="ts">
import { computed, ref } from 'vue'
import { Camera, Trash2 } from 'lucide-vue-next'
import type { Character } from '@/types/models'
import { useChatStore } from '@/stores/chat'

const props = defineProps<{
  character: Character
}>()

const emit = defineEmits<{
  select: []
  deleteRequest: []
}>()

const chat = useChatStore()
const fileInput = ref<HTMLInputElement | null>(null)
const uploading = ref(false)

const gradients = [
  'linear-gradient(135deg, #FF7DAF, #C4A1FF)',
  'linear-gradient(135deg, #FFB8D4, #FFD4A8)',
  'linear-gradient(135deg, #C4A1FF, #A8D8F0)',
  'linear-gradient(135deg, #FF7DAF, #FFD4A8)',
]

const tags = computed(() => {
  const profile = props.character.personality_profile
  if (!profile) return []
  const result: string[] = []
  if (profile.personality) {
    const keywords = profile.personality.split(/[，,、。]/).filter(Boolean).slice(0, 2)
    result.push(...keywords)
  }
  if (profile.expression_style?.emoji?.length) {
    result.push(profile.expression_style.emoji.slice(0, 3).join(''))
  }
  return result.slice(0, 3)
})

function triggerUpload() {
  fileInput.value?.click()
}

async function onFileChange(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  uploading.value = true
  try {
    await chat.uploadAvatar(props.character.id, file)
  } catch {
    // silently fail
  } finally {
    uploading.value = false
    target.value = ''
  }
}
</script>

<template>
  <div class="char-card">
    <div
      class="card-avatar"
      :style="character.avatar_url ? {} : { background: gradients[Math.abs(character.name.charCodeAt(0)) % gradients.length] }"
      @click="emit('select')"
    >
      <img v-if="character.avatar_url" :src="character.avatar_url" class="avatar-img" alt="" />
      <span v-else class="avatar-text">{{ character.name[0] }}</span>
      <!-- 换头像按钮 -->
      <div class="avatar-edit" @click.stop="triggerUpload" :class="{ uploading }" title="更换头像">
        <Camera :size="18" />
      </div>
      <!-- 删除角色按钮（仅非模板角色） -->
      <div
        v-if="!character.is_template"
        class="avatar-delete"
        @click.stop="emit('deleteRequest')"
        title="删除角色"
      >
        <Trash2 :size="16" />
      </div>
      <input
        ref="fileInput"
        type="file"
        accept="image/jpeg,image/png,image/webp,image/gif"
        class="file-input"
        @click.stop
        @change="onFileChange"
      />
    </div>
    <div class="card-info" @click="emit('select')">
      <h3 class="card-name">{{ character.name }}</h3>
      <p class="card-desc">{{ character.description || '等待与你相遇...' }}</p>
      <div v-if="tags.length" class="card-tags">
        <span v-for="tag in tags" :key="tag" class="tag">{{ tag }}</span>
      </div>
    </div>
    <div class="card-overlay">
      <span class="enter-text">开始对话</span>
    </div>
  </div>
</template>

<style scoped>
.char-card {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  border: 1.5px solid var(--color-border);
  overflow: hidden;
  cursor: pointer;
  transition: all var(--duration) var(--ease-bounce);
  position: relative;
}
.char-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: var(--color-primary-light);
}

.card-avatar {
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  cursor: pointer;
}
.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: opacity var(--duration-fast);
}
.avatar-edit {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
  background: rgba(0,0,0,0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  opacity: 0;
  transform: translateY(-4px);
  transition: all var(--duration-fast) var(--ease-smooth);
  cursor: pointer;
  z-index: 2;
}
.avatar-edit:hover {
  background: rgba(0,0,0,0.65);
  transform: translateY(0);
}
.avatar-edit.uploading {
  opacity: 1;
  animation: spin 1s linear infinite;
}
.card-avatar:hover .avatar-edit {
  opacity: 1;
  transform: translateY(0);
}

.avatar-delete {
  position: absolute;
  top: 8px;
  left: 8px;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
  background: rgba(0,0,0,0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  opacity: 0;
  transform: translateY(-4px);
  transition: all var(--duration-fast) var(--ease-smooth);
  cursor: pointer;
  z-index: 2;
}
.avatar-delete:hover {
  background: var(--color-error);
  transform: translateY(0);
}
.card-avatar:hover .avatar-delete {
  opacity: 1;
  transform: translateY(0);
}
.file-input {
  display: none;
}
.avatar-text {
  font-family: var(--font-heading);
  font-size: 64px;
  font-weight: 700;
  color: rgba(255,255,255,0.9);
  text-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.card-info {
  padding: 14px 16px;
  cursor: pointer;
}
.card-name {
  font-family: var(--font-heading);
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 4px;
}
.card-desc {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 8px;
}
.tag {
  display: inline-block;
  padding: 2px 8px;
  background: var(--color-sakura);
  color: var(--color-primary-dark);
  font-size: 10px;
  font-family: var(--font-body);
  border-radius: var(--radius-full);
  line-height: 1.4;
}

.card-overlay {
  position: absolute;
  inset: 0;
  background: rgba(255,125,175,0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity var(--duration) var(--ease-smooth);
  border-radius: var(--radius-lg);
  pointer-events: none;
}
.char-card:hover .card-overlay {
  opacity: 1;
}
.enter-text {
  font-family: var(--font-heading);
  font-size: var(--text-lg);
  font-weight: 600;
  color: #fff;
  letter-spacing: 2px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
