<template>
  <div class="typing">
    <span></span><span></span><span></span>
  </div>
</template>

<style scoped>
.typing {
  display: flex; gap: 4px; padding: 14px 18px;
  align-self: flex-start; align-items: center;
}
.typing span {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--color-primary);
  animation: bounce 1.4s infinite ease-in-out both;
}
.typing span:nth-child(1) { animation-delay: -0.32s; }
.typing span:nth-child(2) { animation-delay: -0.16s; }
@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}
</style>
