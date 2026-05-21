import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/utils/http'
import type { AuthTokens } from '@/types/models'

const GUEST_EMAIL = 'system_guest@virtual-gf.local'

export const useAuthStore = defineStore('auth', () => {
  const guestName = ref('')
  const userAvatar = ref<string | null>(null)
  const userEmail = ref('')
  const authChecked = ref(false) // 启动时的 token 校验是否完成

  const isLoggedIn = computed(() => !!userEmail.value && userEmail.value !== GUEST_EMAIL)
  const hasToken = () => !!localStorage.getItem('access_token')

  async function checkAuth(): Promise<boolean> {
    const token = localStorage.getItem('access_token')
    if (!token) {
      authChecked.value = true
      return false
    }
    try {
      await loadUserInfo()
      if (userEmail.value === GUEST_EMAIL) {
        // 清除游客 token，要求正式登录
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        authChecked.value = true
        return false
      }
      authChecked.value = true
      return true
    } catch {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      authChecked.value = true
      return false
    }
  }

  const isAdmin = ref(false)
  const hasApiKey = ref(false)
  const apiBaseUrl = ref<string | null>(null)
  const apiModel = ref<string | null>(null)
  const showApiKeyWarning = ref(false)
  const userAvatarVersion = ref(0)

  function getUserAvatarUrl(): string {
    if (!userAvatar.value) return ''
    return userAvatarVersion.value > 0 ? `${userAvatar.value}?v=${userAvatarVersion.value}` : userAvatar.value
  }

  async function loadUserInfo() {
    const res = await api.get<{ email: string; username: string; avatar_url: string | null; is_admin: boolean; has_api_key: boolean; api_base_url: string | null; api_model: string | null }>('/users/me')
    guestName.value = res.data.username || ''
    userAvatar.value = res.data.avatar_url
    userEmail.value = res.data.email || ''
    isAdmin.value = res.data.is_admin || false
    localStorage.setItem('is_admin', isAdmin.value ? '1' : '0')
    hasApiKey.value = res.data.has_api_key || false
    apiBaseUrl.value = res.data.api_base_url || null
    apiModel.value = res.data.api_model || null
  }

  async function updateProfile(data: { username?: string; avatar_url?: string; api_key?: string; api_base_url?: string; api_model?: string }) {
    const res = await api.patch<{ username: string; avatar_url: string | null; has_api_key: boolean; api_base_url: string | null; api_model: string | null }>('/users/me', data)
    guestName.value = res.data.username || ''
    userAvatar.value = res.data.avatar_url
    hasApiKey.value = res.data.has_api_key || false
    apiBaseUrl.value = res.data.api_base_url || null
    apiModel.value = res.data.api_model || null
  }

  async function login(email: string, password: string, captchaId?: string, captchaCode?: string) {
    const res = await api.post<AuthTokens>('/auth/login', { email, password, captcha_id: captchaId, captcha_code: captchaCode })
    localStorage.setItem('access_token', res.data.access_token)
    localStorage.setItem('refresh_token', res.data.refresh_token)
    await loadUserInfo()
    return res.data.must_change_password || false
  }

  async function register(email: string, username: string, password: string, captchaId?: string, captchaCode?: string) {
    const res = await api.post<AuthTokens>('/auth/register', { email, username, password, captcha_id: captchaId, captcha_code: captchaCode })
    localStorage.setItem('access_token', res.data.access_token)
    localStorage.setItem('refresh_token', res.data.refresh_token)
    localStorage.removeItem('guide_read') // 新用户注册后强制弹出使用指南
    await loadUserInfo()
  }

  function logout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('is_admin')
    guestName.value = ''
    userAvatar.value = null
    userEmail.value = ''
    isAdmin.value = false
  }

  function promptApiKey() {
    showApiKeyWarning.value = true
  }

  function dismissApiKeyWarning() {
    showApiKeyWarning.value = false
  }

  return { guestName, userAvatar, userEmail, authChecked, isLoggedIn, isAdmin, hasToken, hasApiKey, apiBaseUrl, apiModel, showApiKeyWarning, userAvatarVersion, getUserAvatarUrl, checkAuth, loadUserInfo, updateProfile, login, register, logout, promptApiKey, dismissApiKeyWarning }
})
