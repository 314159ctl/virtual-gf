<script setup lang="ts">
defineProps<{ show: boolean; title?: string }>()
defineEmits<{ close: [] }>()
</script>

<template>
  <Teleport to="body">
    <transition name="modal-fade">
      <div v-if="show" class="modal-overlay" @click.self="$emit('close')">
        <transition name="modal-slide">
          <div v-if="show" class="modal-content">
            <div class="modal-header">
              <h3>{{ title }}</h3>
              <button class="modal-close" @click="$emit('close')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="16" height="16"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
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
  background: rgba(74,37,53,0.3);
}

.modal-content {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl), var(--shadow-glow);
  width: 460px; max-width: 92vw; max-height: 85vh;
  display: flex; flex-direction: column;
}

.modal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 24px;
  border-bottom: 1px solid var(--color-border);
}
.modal-header h3 {
  font-size: var(--text-base);
  font-weight: 600;
  font-family: var(--font-heading);
  color: var(--color-text);
}

.modal-close {
  width: 32px; height: 32px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  color: var(--color-text-muted);
  cursor: pointer; background: transparent; border: none;
  transition: all var(--duration-fast) var(--ease-smooth);
}
.modal-close:hover {
  background: var(--color-sakura);
  color: var(--color-error);
}

.modal-body {
  padding: 20px 24px;
  overflow-y: auto; flex: 1;
  font-family: var(--font-body);
}

.modal-footer {
  display: flex; justify-content: flex-end; gap: 8px;
  padding: 14px 24px;
  border-top: 1px solid var(--color-border);
}

/* ── Transitions ── */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity var(--duration) var(--ease-smooth);
}
.modal-fade-enter-from,
.modal-fade-leave-to { opacity: 0; }

.modal-slide-enter-active {
  transition: all var(--duration) var(--ease-bounce);
}
.modal-slide-leave-active {
  transition: all var(--duration-fast) var(--ease-smooth);
}
.modal-slide-enter-from {
  opacity: 0; transform: translateY(20px) scale(0.95);
}
.modal-slide-leave-to {
  opacity: 0; transform: translateY(-10px) scale(0.98);
}
</style>
