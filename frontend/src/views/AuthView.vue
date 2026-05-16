<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Sparkles, RefreshCw } from 'lucide-vue-next'
import api from '@/utils/http'

const router = useRouter()
const auth = useAuthStore()

const tab = ref<'login' | 'register'>('login')
const loading = ref(false)
const error = ref('')

// 验证码
const captchaId = ref('')
const captchaCode = ref('')
const captchaImage = ref('')

async function loadCaptcha() {
  try {
    const res = await api.get<{ captcha_id: string; captcha_image: string }>('/auth/captcha')
    captchaId.value = res.data.captcha_id
    captchaImage.value = res.data.captcha_image
    captchaCode.value = ''
  } catch {
    // ignore
  }
}

onMounted(loadCaptcha)

// 登录表单
const loginEmail = ref('')
const loginPassword = ref('')

// 注册表单
const regEmail = ref('')
const regUsername = ref('')
const regPassword = ref('')
const regConfirm = ref('')

const canLogin = computed(() => loginEmail.value.trim() && loginPassword.value.trim())
const canRegister = computed(() => {
  return regEmail.value.trim() && regUsername.value.trim() &&
    regPassword.value.length >= 6 && regConfirm.value === regPassword.value
})

function switchTab(t: 'login' | 'register') {
  tab.value = t
  error.value = ''
}

async function doLogin() {
  if (!canLogin.value) return
  error.value = ''
  loading.value = true
  try {
    await auth.login(loginEmail.value.trim(), loginPassword.value, captchaId.value, captchaCode.value)
    router.replace('/')
  } catch (e: any) {
    error.value = e?.response?.data?.detail || e?.message || '登录失败，请重试'
    loadCaptcha()
  } finally {
    loading.value = false
  }
}

async function doRegister() {
  if (!canRegister.value) return
  error.value = ''
  loading.value = true
  try {
    await auth.register(regEmail.value.trim(), regUsername.value.trim(), regPassword.value)
    router.replace('/')
  } catch (e: any) {
    error.value = e?.response?.data?.detail || e?.message || '注册失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-view">
    <div class="auth-card">
      <!-- Header -->
      <div class="auth-header">
        <span class="brand-icon">🌸</span>
        <h1 class="brand-text">恋爱对话模拟器</h1>
      </div>


      <!-- Login Form -->
      <form v-if="tab === 'login'" class="auth-form" @submit.prevent="doLogin">
        <div class="form-group">
          <label class="form-label">邮箱</label>
          <input
            v-model="loginEmail"
            type="email"
            class="form-input"
            placeholder="请输入邮箱"
            autocomplete="email"
          />
        </div>
        <div class="form-group">
          <label class="form-label">密码</label>
          <input
            v-model="loginPassword"
            type="password"
            class="form-input"
            placeholder="请输入密码"
            autocomplete="current-password"
          />
        </div>

        <div class="form-group">
          <label class="form-label">验证码</label>
          <div class="captcha-row">
            <img v-if="captchaImage" :src="captchaImage" class="captcha-img" alt="验证码" @click="loadCaptcha" title="点击刷新" />
            <input
              v-model="captchaCode"
              type="text"
              class="form-input captcha-input"
              placeholder="输入验证码"
              maxlength="4"
              autocomplete="off"
              @keyup.enter="doLogin"
            />
            <button type="button" class="captcha-refresh" @click="loadCaptcha" title="刷新验证码">
              <RefreshCw :size="14" />
            </button>
          </div>
        </div>

        <p v-if="error" class="error-msg">{{ error }}</p>

        <button type="submit" class="btn-submit" :disabled="loading || !canLogin">
          <Sparkles v-if="!loading" :size="16" />
          <span v-if="loading" class="spinner" />
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>

      <!-- Register Form -->
      <form v-if="tab === 'register'" class="auth-form" @submit.prevent="doRegister">
        <div class="form-group">
          <label class="form-label">邮箱</label>
          <input
            v-model="regEmail"
            type="email"
            class="form-input"
            placeholder="请输入邮箱"
            autocomplete="email"
          />
        </div>
        <div class="form-group">
          <label class="form-label">用户名</label>
          <input
            v-model="regUsername"
            type="text"
            class="form-input"
            placeholder="给自己取个名字吧"
            maxlength="12"
            autocomplete="username"
          />
        </div>
        <div class="form-group">
          <label class="form-label">密码</label>
          <input
            v-model="regPassword"
            type="password"
            class="form-input"
            placeholder="至少 6 位密码"
            autocomplete="new-password"
          />
        </div>
        <div class="form-group">
          <label class="form-label">确认密码</label>
          <input
            v-model="regConfirm"
            type="password"
            class="form-input"
            placeholder="再次输入密码"
            autocomplete="new-password"
            @keyup.enter="doRegister"
          />
        </div>

        <p v-if="error" class="error-msg">{{ error }}</p>

        <button type="submit" class="btn-submit" :disabled="loading || !canRegister">
          <Sparkles v-if="!loading" :size="16" />
          <span v-if="loading" class="spinner" />
          {{ loading ? '注册中...' : '注册' }}
        </button>
      </form>

      <!-- Footer -->
      <p class="auth-footer">
        {{ tab === 'login' ? '还没有账号？' : '已有账号？' }}
        <button type="button" class="link-btn" @click="switchTab(tab === 'login' ? 'register' : 'login')">
          {{ tab === 'login' ? '立即注册' : '去登录' }}
        </button>
      </p>
    </div>
  </div>
</template>

<style scoped>
.auth-view {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background:
    linear-gradient(rgba(255, 240, 245, 0.88), rgba(255, 220, 235, 0.9)),
    url('/bg.png') center / cover no-repeat;
  padding: 24px;
}

.auth-card {
  width: 380px;
  max-width: 100%;
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  padding: 32px 28px 24px;
  box-shadow: var(--shadow-sm);
}

/* Header */
.auth-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 20px;
}
.brand-icon { font-size: 24px; }
.brand-text {
  font-family: var(--font-heading);
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--color-primary-dark);
  letter-spacing: 2px;
}

/* Form */
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.form-label {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-text-secondary);
  font-family: var(--font-heading);
}
.form-input {
  width: 100%;
  padding: 10px 14px;
  border: 1.5px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  font-family: var(--font-body);
  background: var(--color-bg);
  color: var(--color-text);
  outline: none;
  transition: border-color var(--duration-fast);
  box-sizing: border-box;
}
.form-input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(255,125,175,0.08);
}

.btn-submit {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 0;
  border: none;
  border-radius: var(--radius-full);
  font-size: var(--text-sm);
  font-family: var(--font-body);
  font-weight: 600;
  color: #fff;
  background: var(--color-primary);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-bounce);
  margin-top: 4px;
}
.btn-submit:hover:not(:disabled) {
  background: var(--color-primary-dark);
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}
.btn-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error-msg {
  padding: 8px 12px;
  background: rgba(232,128,138,0.1);
  border: 1px solid rgba(232,128,138,0.2);
  border-radius: var(--radius-xs);
  font-size: var(--text-xs);
  color: var(--color-error);
  text-align: center;
}

.spinner {
  width: 14px; height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Footer */
.auth-footer {
  text-align: center;
  margin-top: 18px;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}
.link-btn {
  border: none;
  background: transparent;
  color: var(--color-primary);
  font-size: var(--text-xs);
  font-family: var(--font-body);
  cursor: pointer;
  font-weight: 500;
  padding: 0;
}
.link-btn:hover {
  text-decoration: underline;
}

/* ── Captcha ── */
.captcha-row {
  display: flex;
  gap: 8px;
  align-items: center;
}
.captcha-img {
  height: 40px;
  width: 110px;
  border-radius: var(--radius-xs);
  border: 1.5px solid var(--color-border);
  cursor: pointer;
  flex-shrink: 0;
}
.captcha-input {
  flex: 1;
  min-width: 0;
}
.captcha-refresh {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-xs);
  border: 1.5px solid var(--color-border);
  background: var(--color-bg);
  color: var(--color-text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: all var(--duration-fast);
}
.captcha-refresh:hover {
  border-color: var(--color-primary-light);
  color: var(--color-primary);
}

@media (max-width: 480px) {
  .auth-view {
    padding: 16px;
  }
  .auth-card {
    padding: 24px 18px 18px;
  }
  .brand-text {
    font-size: var(--text-base);
    letter-spacing: 1px;
  }
  .form-input {
    padding: 8px 12px;
  }
}
</style>
