<script setup lang="ts">
defineProps<{ show: boolean; title?: string }>()
defineEmits<{ close: [] }>()
</script>

<template>
  <Teleport to="body">
    <transition name="fade">
      <div v-if="show" class="modal-overlay" @click.self="$emit('close')">
        <transition name="slide-up">
          <div v-if="show" class="modal-content">
            <div class="modal-header">
              <h3>{{ title }}</h3>
              <button class="modal-close" @click="$emit('close')">✕</button>
            </div>
            <div class="modal-body">
              <slot />
            </div>
            <div class="modal-footer" v-if="$slots.footer">
              <slot name="footer" />
            </div>
          </div>
        </transition>
      </div>
    </transition>
  </Teleport>
</template>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0; z-index: 1000;
  display: flex; align-items: center; justify-content: center;
  background: rgba(0,0,0,0.35); backdrop-filter: blur(4px);
}
.modal-content {
  background: var(--color-surface);
  border-radius: var(--radius); box-shadow: var(--shadow-lg);
  width: 460px; max-width: 92vw; max-height: 85vh;
  display: flex; flex-direction: column;
}
.modal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 24px; border-bottom: 1px solid var(--color-border);
}
.modal-header h3 { font-size: 16px; font-weight: 600; }
.modal-close {
  width: 32px; height: 32px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; color: var(--color-text-muted);
  transition: all var(--duration-fast);
}
.modal-close:hover { background: rgba(0,0,0,0.08); color: var(--color-text); }
.modal-body { padding: 20px 24px; overflow-y: auto; flex: 1; }
.modal-footer {
  display: flex; justify-content: flex-end; gap: 8px;
  padding: 14px 24px; border-top: 1px solid var(--color-border);
}
</style>
