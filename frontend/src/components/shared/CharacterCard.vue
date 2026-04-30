<script setup lang="ts">
import { computed } from 'vue'
import type { Character } from '@/types/models'

const props = defineProps<{
  character: Character
}>()

defineEmits<{
  select: []
}>()

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
    // 提取前两个性格关键词
    const keywords = profile.personality.split(/[，,、。]/).filter(Boolean).slice(0, 2)
    result.push(...keywords)
  }
  if (profile.expression_style?.emoji?.length) {
    result.push(profile.expression_style.emoji.slice(0, 3).join(''))
  }
  return result.slice(0, 3)
})
</script>

<template>
  <div class="char-card" @click="$emit('select')">
    <div
      class="card-avatar"
      :style="{ background: gradients[Math.abs(character.name.charCodeAt(0)) % gradients.length] }"
    >
      <span class="avatar-text">{{ character.name[0] }}</span>
    </div>
    <div class="card-info">
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
</style>
