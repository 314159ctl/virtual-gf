<template>
  <div class="typing">
    <span></span><span></span><span></span>
  </div>
</template>

<style scoped>
.typing {
  display: flex;
  gap: 5px;
  padding: 14px 18px;
  align-self: flex-start;
  align-items: center;
  background: var(--color-bubble-ai);
  border-radius: var(--radius);
  border-bottom-left-radius: var(--radius-xs);
  box-shadow: 0 1px 4px rgba(0,0,0,0.03);
  border: 1px solid rgba(255,125,175,0.06);
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
