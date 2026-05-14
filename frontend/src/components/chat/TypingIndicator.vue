<template>
  <div class="typing">
    <span></span><span></span><span></span>
  </div>
</template>

<style scoped>
.typing {
  display: flex;
  gap: 5px;
  padding: 10px 14px;
  align-self: flex-start;
  align-items: center;
  animation: msgIn 0.3s var(--ease-bounce);
  margin-left: 46px;
}
.typing span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-primary-light);
  animation: bounce 1.4s infinite ease-in-out both;
}
.typing span:nth-child(1) { animation-delay: -0.32s; background: var(--color-primary); }
.typing span:nth-child(2) { animation-delay: -0.16s; background: var(--color-accent); }
.typing span:nth-child(3) { background: var(--color-gold); }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40%            { transform: scale(1); opacity: 1; }
}
@keyframes msgIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>
