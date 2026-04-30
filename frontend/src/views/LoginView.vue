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
const confirmPassword = ref('')
const agreeTerms = ref(false)
const error = ref('')
const loading = ref(false)

async function onSubmit() {
  error.value = ''
  if (isRegister.value && password.value !== confirmPassword.value) {
    error.value = '两次输入的密码不一致'
    return
  }
  if (isRegister.value && !agreeTerms.value) {
    error.value = '请同意用户协议和隐私政策'
    return
  }
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
    <!-- 樱花飘落背景 -->
    <div class="sakura-bg" aria-hidden="true">
      <span
        v-for="i in 24"
        :key="i"
        class="petal"
        :style="{
          left: `${(i * 17 + 3) % 100}%`,
          animationDelay: `${(i * 1.7) % 12}s`,
          animationDuration: `${8 + (i % 5) * 2}s`,
          fontSize: `${8 + (i % 3) * 4}px`,
          opacity: 0.15 + (i % 5) * 0.05,
        }"
      >🌸</span>
    </div>

    <div class="login-container">
      <!-- Logo区域 -->
      <div class="logo-section">
        <div class="logo-main">千恋万花</div>
        <div class="logo-decoration">
          <span>♦</span><span>♦</span><span>♦</span><span>♦</span><span>♦</span>
        </div>
        <div class="logo-decoration-2">
          <span>♦</span><span>♦</span><span>♦</span><span>♦</span><span>♦</span><span>♦</span>
        </div>
        <p class="logo-subtitle">虚拟女友陪伴系统</p>
        <p class="logo-quote">"愿此花，常在你心"</p>
      </div>

      <!-- 表单区域 -->
      <div class="form-section">
        <div class="form-card">
          <h2 class="form-title">{{ isRegister ? '创建新账号' : '登录' }}</h2>

          <form @submit.prevent="onSubmit" class="auth-form">
            <div class="form-group">
              <label class="form-label">
                <svg class="form-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M2 8l10 6 10-6"/></svg>
                邮箱地址
              </label>
              <input
                v-model="email"
                type="email"
                class="form-input"
                required
                placeholder="请输入邮箱"
              />
            </div>

            <div class="form-group" v-if="isRegister">
              <label class="form-label">
                <svg class="form-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                昵称
              </label>
              <input
                v-model="username"
                type="text"
                class="form-input"
                required
                placeholder="请输入昵称"
              />
            </div>

            <div class="form-group">
              <label class="form-label">
                <svg class="form-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
                密码
              </label>
              <input
                v-model="password"
                type="password"
                class="form-input"
                required
                placeholder="请输入密码"
                minlength="6"
              />
            </div>

            <div class="form-group" v-if="isRegister">
              <label class="form-label">
                <svg class="form-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
                确认密码
              </label>
              <input
                v-model="confirmPassword"
                type="password"
                class="form-input"
                required
                placeholder="请再次输入密码"
                minlength="6"
              />
            </div>

            <div class="form-group checkbox-group" v-if="isRegister">
              <label class="checkbox-label">
                <input type="checkbox" v-model="agreeTerms" />
                <span class="checkmark" />
                <span class="checkbox-text">我已阅读并同意 <a href="#">《用户协议》</a> 和 <a href="#">《隐私政策》</a></span>
              </label>
            </div>

            <div v-if="error" class="error-msg">{{ error }}</div>

            <button type="submit" class="submit-btn" :disabled="loading">
              <span v-if="loading" class="btn-loading">
                <span class="dot-pulse" />
                处理中...
              </span>
              <span v-else>{{ isRegister ? '🌸 注册' : '登录' }}</span>
            </button>
          </form>

          <div class="form-footer">
            <span v-if="!isRegister" class="forgot-link">
              <a href="#">忘记密码？</a>
            </span>
            <p class="switch-mode">
              {{ isRegister ? '已有账号？' : '还没有账号？' }}
              <a href="#" @click.prevent="isRegister = !isRegister; error = ''">
                {{ isRegister ? '去登录' : '立即注册' }}
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(180deg, #FFF5F8 0%, #FFE8ED 50%, #F5E8F5 100%);
  position: relative;
  overflow: hidden;
}

/* ── 樱花飘落 ── */
.sakura-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
  z-index: 0;
}
.petal {
  position: absolute;
  top: -5%;
  animation: petalFall linear infinite;
  user-select: none;
}
@keyframes petalFall {
  0%   { transform: translateY(-10vh) rotate(0deg) translateX(0); opacity: 0; }
  10%  { opacity: 0.3; }
  90%  { opacity: 0.15; }
  100% { transform: translateY(105vh) rotate(720deg) translateX(60px); opacity: 0; }
}

/* ── 主容器 ── */
.login-container {
  display: flex;
  width: 900px;
  max-width: 95vw;
  height: 560px;
  background: rgba(255,255,255,0.95);
  border-radius: 24px;
  box-shadow: 0 16px 48px rgba(240,140,160,0.16), 0 0 60px rgba(240,140,160,0.1);
  overflow: hidden;
  position: relative;
  z-index: 1;
}

/* ── Logo区域 ── */
.logo-section {
  width: 45%;
  background: linear-gradient(135deg, rgba(240,140,160,0.08), rgba(201,168,232,0.08));
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  position: relative;
  overflow: hidden;
}
.logo-section::before {
  content: '';
  position: absolute;
  inset: 0;
  background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M30 5c-2 8-8 14-16 16 8 2 14 8 16 16 2-8 8-14 16-16-8-2-14-8-16-16z' fill='%23f08ca0' fill-opacity='0.04'/%3E%3C/svg%3E");
  opacity: 0.6;
}
.logo-main {
  font-family: 'Noto Serif SC', serif;
  font-size: 48px;
  font-weight: 700;
  color: #D96B82;
  letter-spacing: 8px;
  position: relative;
  z-index: 2;
}
.logo-decoration,
.logo-decoration-2 {
  display: flex;
  gap: 6px;
  position: absolute;
}
.logo-decoration {
  top: 30%;
  left: 20%;
}
.logo-decoration-2 {
  bottom: 35%;
  right: 15%;
}
.logo-decoration span,
.logo-decoration-2 span {
  font-size: 12px;
  color: #F08CA0;
  opacity: 0.6;
}
.logo-subtitle {
  font-size: 14px;
  color: #8B6B7A;
  margin-top: 32px;
  position: relative;
  z-index: 2;
}
.logo-quote {
  font-family: 'Noto Serif SC', serif;
  font-size: 13px;
  color: #C4A0B0;
  font-style: italic;
  margin-top: 12px;
  position: relative;
  z-index: 2;
}

/* ── 表单区域 ── */
.form-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}
.form-card {
  width: 100%;
  max-width: 340px;
}
.form-title {
  font-family: 'Noto Serif SC', serif;
  font-size: 22px;
  font-weight: 600;
  color: #5A3A4A;
  text-align: center;
  margin-bottom: 32px;
}

/* ── 表单 ── */
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.form-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 500;
  color: #8B6B7A;
}
.form-icon {
  width: 14px;
  height: 14px;
  color: #C4A0B0;
}
.form-input {
  width: 100%;
  padding: 12px 14px;
  border: 1.5px solid #F5D8E0;
  border-radius: 12px;
  font-size: 14px;
  outline: none;
  transition: all 0.2s ease;
  background: #FFF0F3;
  color: #5A3A4A;
}
.form-input:focus {
  border-color: #F08CA0;
  box-shadow: 0 0 0 3px rgba(240,140,160,0.08);
}
.form-input::placeholder {
  color: #C4A0B0;
}

/* ── 复选框 ── */
.checkbox-group {
  margin-top: -4px;
}
.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  cursor: pointer;
  font-size: 12px;
  color: #8B6B7A;
}
.checkbox-label input {
  display: none;
}
.checkmark {
  width: 16px;
  height: 16px;
  border: 1.5px solid #F5D8E0;
  border-radius: 4px;
  flex-shrink: 0;
  margin-top: 1px;
  transition: all 0.2s;
  position: relative;
}
.checkbox-label input:checked + .checkmark {
  background: #F08CA0;
  border-color: #F08CA0;
}
.checkbox-label input:checked + .checkmark::after {
  content: '';
  position: absolute;
  left: 4px;
  top: 1px;
  width: 5px;
  height: 9px;
  border: solid white;
  border-width: 0 1.5px 1.5px 0;
  transform: rotate(45deg);
}
.checkbox-text a {
  color: #F08CA0;
  text-decoration: underline;
}

/* ── 错误提示 ── */
.error-msg {
  padding: 10px 12px;
  background: rgba(232,128,138,0.1);
  border: 1px solid rgba(232,128,138,0.2);
  border-radius: 8px;
  font-size: 12px;
  color: #E8808A;
  text-align: center;
}

/* ── 提交按钮 ── */
.submit-btn {
  width: 100%;
  padding: 14px;
  border-radius: 20px;
  background: linear-gradient(135deg, #F08CA0, #D96B82);
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 16px rgba(240,140,160,0.25);
  margin-top: 8px;
}
.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(240,140,160,0.35);
}
.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.btn-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.dot-pulse {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #fff;
  animation: bounce 1.4s infinite ease-in-out both;
}
@keyframes bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40%            { transform: scale(1); opacity: 1; }
}

/* ── 底部 ── */
.form-footer {
  margin-top: 24px;
  text-align: center;
}
.forgot-link {
  display: block;
  margin-bottom: 8px;
}
.forgot-link a {
  font-size: 12px;
  color: #C4A0B0;
}
.forgot-link a:hover {
  color: #F08CA0;
}
.switch-mode {
  font-size: 12px;
  color: #8B6B7A;
}
.switch-mode a {
  color: #F08CA0;
  font-weight: 500;
}
.switch-mode a:hover {
  text-decoration: underline;
}

/* ── 移动端适配 ── */
@media (max-width: 768px) {
  .login-container {
    flex-direction: column;
    height: auto;
    max-height: 95vh;
    overflow-y: auto;
  }
  .logo-section {
    width: 100%;
    padding: 24px;
    min-height: 180px;
  }
  .logo-main {
    font-size: 36px;
  }
  .form-section {
    padding: 24px;
  }
}
</style>
