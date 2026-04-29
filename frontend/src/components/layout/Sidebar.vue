<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { useChatStore } from '@/stores/chat'
import { useAuthStore } from '@/stores/auth'
import type { Character } from '@/types/models'

const chat = useChatStore()
const auth = useAuthStore()
const { characters, currentCharacter } = storeToRefs(chat)

defineEmits<{
  newCharacter: []
  openSettings: []
  openPainting: []
}>()

function select(char: Character) {
  chat.selectCharacter(char)
}
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar-brand">
      <span class="logo">💕 虚拟女友</span>
    </div>

    <div class="sidebar-section">
      <div class="section-label">我的角色</div>
      <ul class="char-list">
        <li
          v-for="c in characters"
          :key="c.id"
          :class="{ active: currentCharacter?.id === c.id }"
          @click="select(c)"
        >
          <div class="char-avatar">{{ c.name[0] }}</div>
          <div class="char-info">
            <div class="char-name">{{ c.name }}</div>
            <div class="char-desc">{{ c.description || '' }}</div>
          </div>
        </li>
      </ul>
      <button class="btn btn-outline btn-sm" style="width:100%;margin-top:8px" @click="$emit('newCharacter')">
        + 创建角色
      </button>
    </div>

    <div class="sidebar-spacer" />

    <div class="sidebar-actions">
      <button class="side-btn" @click="$emit('openPainting')">🖼️ AI 绘画</button>
      <button class="side-btn" @click="$emit('openSettings')">⚙️ 设置</button>
    </div>

    <div class="sidebar-user" v-if="auth.user">
      <div class="user-avatar">{{ auth.user.username[0] }}</div>
      <div class="user-info">
        <div class="user-name">{{ auth.user.username }}</div>
        <div class="user-tier">{{ auth.user.membership_tier }}</div>
      </div>
      <button class="logout-btn" @click="auth.logout()" title="退出登录">↪</button>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: var(--sidebar-w); height: 100%;
  background: var(--color-sidebar);
  border-right: 1px solid var(--color-border);
  display: flex; flex-direction: column;
  padding: 0 16px; flex-shrink: 0;
}
.sidebar-brand { padding: 18px 0 14px; border-bottom: 1px solid var(--color-border); }
.logo { font-size: 20px; font-weight: 700; color: var(--color-primary); letter-spacing: 1px; }
.sidebar-section { padding: 12px 0; }
.section-label {
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  color: var(--color-text-muted); letter-spacing: 1.5px; margin-bottom: 8px;
}
.char-list { list-style: none; display: flex; flex-direction: column; gap: 2px; }
.char-list li {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 12px; border-radius: var(--radius-sm); cursor: pointer;
  transition: all var(--duration-fast); font-size: 14px; font-weight: 500;
}
.char-list li:hover { background: rgba(255,107,157,0.06); }
.char-list li.active { background: rgba(255,107,157,0.12); color: var(--color-primary); font-weight: 600; }
.char-avatar {
  width: 36px; height: 36px; border-radius: 50%;
  background: linear-gradient(135deg, var(--color-primary), var(--color-accent));
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 16px; flex-shrink: 0;
}
.char-info { flex: 1; min-width: 0; }
.char-name { font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.char-desc { font-size: 11px; color: var(--color-text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.sidebar-spacer { flex: 1; }

.sidebar-actions { padding: 8px 0; border-top: 1px solid var(--color-border); display: flex; flex-direction: column; gap: 4px; }
.side-btn {
  width: 100%; padding: 8px 12px; border-radius: var(--radius-sm);
  font-size: 13px; color: var(--color-text-secondary);
  display: flex; align-items: center; gap: 8px;
  transition: all var(--duration-fast);
}
.side-btn:hover { background: rgba(0,0,0,0.04); color: var(--color-text); }

.sidebar-user {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 0; border-top: 1px solid var(--color-border);
}
.user-avatar {
  width: 32px; height: 32px; border-radius: 50%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 14px; flex-shrink: 0;
}
.user-info { flex: 1; min-width: 0; }
.user-name { font-size: 13px; font-weight: 500; }
.user-tier {
  font-size: 11px; color: var(--color-primary);
  text-transform: uppercase; font-weight: 600;
}
.logout-btn {
  width: 28px; height: 28px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; color: var(--color-text-muted);
  transition: all var(--duration-fast);
}
.logout-btn:hover { background: rgba(0,0,0,0.08); color: var(--color-error); }
</style>
