<script setup lang="ts">
import { X } from 'lucide-vue-next'

defineProps<{ url: string }>()
defineEmits<{ remove: [] }>()
</script>

<template>
  <div class="image-preview">
    <img :src="url" alt="preview" />
    <button class="remove-btn" @click="$emit('remove')">
      <X :size="14" />
    </button>
  </div>
</template>

<style scoped>
.image-preview {
  position: relative;
  display: inline-block;
  margin-bottom: 8px;
}
.image-preview img {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: var(--radius-sm);
  border: 2px solid var(--color-border);
}
.remove-btn {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--color-error);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border: 2px solid var(--color-surface);
}
</style>
