<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const isRegister = ref(false)
const email = ref('')
const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function onSubmit() {
  error.value = ''
  loading.value = true
  try {
    if (isRegister.value) {
      await auth.register(email.value, username.value, password.value)
    } else {
      await auth.login(email.value, password.value)
    }
    router.push('/')
  } catch (e: any) {
    error.value = e.response?.data?.detail || '操作失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-logo">💕</div>
      <h1>虚拟女友</h1>
      <p class="subtitle">AI 聊天伴侣</p>

      <form @submit.prevent="onSubmit" class="login-form">
        <div class="form-group">
          <label>邮箱</label>
          <input v-model="email" type="email" class="form-input" required placeholder="your@email.com" />
        </div>
        <div class="form-group" v-if="isRegister">
          <label>用户名</label>
          <input v-model="username" type="text" class="form-input" required placeholder="你的昵称" />
        </div>
        <div class="form-group">
          <label>密码</label>
          <input v-model="password" type="password" class="form-input" required placeholder="至少 6 位" minlength="6" />
        </div>

        <div v-if="error" class="error-msg">{{ error }}</div>

        <button type="submit" class="btn btn-primary login-btn" :disabled="loading">
          {{ loading ? '处理中...' : (isRegister ? '注册' : '登录') }}
        </button>
      </form>

      <p class="switch-mode">
        {{ isRegister ? '已有账号？' : '没有账号？' }}
        <a href="#" @click.prevent="isRegister = !isRegister; error = ''">
          {{ isRegister ? '去登录' : '去注册' }}
        </a>
      </p>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  height: 100%; display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #fdf2f7 0%, #fff5f8 50%, #f8e8f0 100%);
}
.login-card {
  background: var(--color-surface); border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg); padding: 48px 40px; width: 400px; max-width: 92vw;
  text-align: center;
}
.login-logo { font-size: 48px; margin-bottom: 8px; }
h1 { font-size: 24px; font-weight: 700; color: var(--color-primary); }
.subtitle { color: var(--color-text-muted); font-size: 14px; margin: 4px 0 24px; }

.login-form { text-align: left; }
.form-group { margin-bottom: 16px; }
.form-group label {
  display: block; font-size: 13px; font-weight: 600;
  color: var(--color-text-secondary); margin-bottom: 6px;
}
.form-input {
  width: 100%; padding: 12px 16px; border: 1.5px solid var(--color-border);
  border-radius: var(--radius-sm); font-size: 15px;
  font-family: inherit; outline: none;
  transition: border-color var(--duration-fast);
  background: var(--color-bg); color: var(--color-text);
}
.form-input:focus {
  border-color: var(--color-primary-light);
  box-shadow: 0 0 0 3px rgba(255,107,157,0.08);
}

.error-msg {
  background: #fde8ec; color: var(--color-error);
  padding: 10px 14px; border-radius: var(--radius-xs);
  font-size: 13px; margin-bottom: 12px;
}

.login-btn { width: 100%; padding: 12px; font-size: 16px; }

.switch-mode { margin-top: 20px; font-size: 14px; color: var(--color-text-secondary); }
.switch-mode a { color: var(--color-primary); font-weight: 600; }
.switch-mode a:hover { text-decoration: underline; }
</style>
