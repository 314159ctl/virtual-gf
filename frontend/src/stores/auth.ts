import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/utils/http'
import type { AuthTokens } from '@/types/models'

const GUEST_EMAIL = 'system_guest@virtual-gf.local'

export const useAuthStore = defineStore('auth', () => {
  const guestReady = ref(false)
  const guestName = ref('访客')
  const userAvatar = ref<string | null>(null)
  const userEmail = ref('')

  const isLoggedIn = computed(() => !!userEmail.value && userEmail.value !== GUEST_EMAIL)

  async function initGuest() {
    // 如果已有 token，先尝试加载用户信息
    const token = localStorage.getItem('access_token')
    if (token) {
      try {
        await loadUserInfo()
        guestReady.value = true
        return
      } catch {
        // token 失效，继续走 guest 流程
      }
    }
    try {
      const res = await api.post<AuthTokens>('/auth/guest')
      localStorage.setItem('access_token', res.data.access_token)
      localStorage.setItem('refresh_token', res.data.refresh_token)
      guestReady.value = true
    } catch {
      if (!localStorage.getItem('access_token')) {
        localStorage.setItem('access_token', 'guest-fallback-' + Date.now())
      }
      guestReady.value = true
    }
  }

  async function loadUserInfo() {
    const res = await api.get<{ email: string; username: string; avatar_url: string | null }>('/users/me')
    guestName.value = res.data.username || '访客'
    userAvatar.value = res.data.avatar_url
    userEmail.value = res.data.email || ''
  }

  async function updateProfile(data: { username?: string; avatar_url?: string }) {
    const res = await api.patch<{ username: string; avatar_url: string | null }>('/users/me', data)
    guestName.value = res.data.username || '访客'
    userAvatar.value = res.data.avatar_url
  }

  async function login(email: string, password: string) {
    const res = await api.post<AuthTokens>('/auth/login', { email, password })
    localStorage.setItem('access_token', res.data.access_token)
    localStorage.setItem('refresh_token', res.data.refresh_token)
    await loadUserInfo()
    guestReady.value = true
  }

  async function register(email: string, username: string, password: string) {
    await api.post('/auth/register', { email, username, password })
    // 注册成功后自动登录
    await login(email, password)
  }

  function logout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    guestName.value = '访客'
    userAvatar.value = null
    userEmail.value = ''
    guestReady.value = false
  }

  return { guestReady, guestName, userAvatar, userEmail, isLoggedIn, initGuest, loadUserInfo, updateProfile, login, register, logout }
})
