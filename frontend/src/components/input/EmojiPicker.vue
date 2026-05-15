<script setup lang="ts">
const emit = defineEmits<{ select: [emoji: string] }>()

const categories: { name: string; emojis: string[] }[] = [
  { name: '表情', emojis: ['😀', '😃', '😄', '😁', '😂', '🤣', '😊', '😇', '😍', '🥰', '😘', '😋', '😜', '🤪', '😎', '🤩', '🥳', '😭', '😤', '🥺'] },
  { name: '手势', emojis: ['👍', '👎', '👏', '🙌', '🤝', '✌️', '🤟', '👌', '✊', '👊', '🤞', '🙏', '💪', '🫶', '🤏', '👋'] },
  { name: '爱心', emojis: ['❤️', '🧡', '💛', '💚', '💙', '💜', '🩷', '🤎', '💕', '💗', '💓', '💖', '💘', '💝', '💞', '💟'] },
  { name: '食物', emojis: ['🍰', '🎂', '🧁', '🍪', '🍩', '🍫', '🍬', '🍓', '🍒', '🍑', '🍉', '🍇', '🥐', '🍿', '🧋', '🍜'] },
  { name: '动物', emojis: ['🐱', '🐶', '🐰', '🐻', '🐼', '🐨', '🐯', '🦁', '🐮', '🐷', '🐸', '🐧', '🦊', '🐹', '🐥', '🦄'] },
  { name: '植物', emojis: ['🌸', '🌺', '🌻', '🌹', '🌷', '💐', '🌼', '🍀', '🌿', '🌱', '🌳', '🌴', '🍂', '🍁', '🪷', '💮'] },
  { name: '物品', emojis: ['⭐', '🌟', '✨', '💫', '🎀', '🎁', '🎈', '🎉', '🎊', '💎', '🔔', '💡', '📌', '🕯️', '🎵', '🎶'] },
  { name: '符号', emojis: ['✅', '❌', '❓', '❗', '💯', '🔥', '💧', '🌈', '☀️', '🌙', '⚡', '💤', '♾️', '💢', '💦', '🫧'] },
]
</script>

<template>
  <div class="emoji-picker">
    <div class="emoji-grid" v-for="cat in categories" :key="cat.name">
      <div class="cat-label">{{ cat.name }}</div>
      <div class="cat-row">
        <button
          v-for="e in cat.emojis"
          :key="e"
          class="emoji-btn"
          @click="emit('select', e)"
        >{{ e }}</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.emoji-picker {
  width: 320px;
  max-height: 320px;
  overflow-y: auto;
  background: var(--color-surface);
  border: 1.5px solid var(--color-border);
  border-radius: var(--radius);
  padding: 12px;
  box-shadow: var(--shadow-lg);
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.emoji-picker::-webkit-scrollbar { width: 4px; }
.emoji-picker::-webkit-scrollbar-thumb { background: var(--color-border); border-radius: 2px; }

.emoji-grid {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.cat-label {
  font-size: 10px;
  font-family: var(--font-body);
  color: var(--color-text-muted);
  padding: 0 2px;
}

.cat-row {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
}

.emoji-btn {
  width: 34px;
  height: 34px;
  border: none;
  background: transparent;
  font-size: 20px;
  cursor: pointer;
  border-radius: var(--radius-xs);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background var(--duration-fast);
  line-height: 1;
  padding: 0;
}
.emoji-btn:hover {
  background: var(--color-sakura-light);
}
</style>
