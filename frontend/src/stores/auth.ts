import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/utils/http'
import type { AuthTokens } from '@/types/models'

export const useAuthStore = defineStore('auth', () => {
  const guestReady = ref(false)
  const guestName = ref('访客')
  const userAvatar = ref<string | null>(null)

  async function initGuest() {
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
    try {
      const res = await api.get<{ username: string; avatar_url: string | null }>('/users/me')
      guestName.value = res.data.username || '访客'
      userAvatar.value = res.data.avatar_url
    } catch {
      // ignore
    }
  }

  async function updateProfile(data: { username?: string; avatar_url?: string }) {
    const res = await api.patch<{ username: string; avatar_url: string | null }>('/users/me', data)
    guestName.value = res.data.username || '访客'
    userAvatar.value = res.data.avatar_url
  }

  function logout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    guestName.value = '访客'
    userAvatar.value = null
    guestReady.value = false
  }

  return { guestReady, guestName, userAvatar, initGuest, loadUserInfo, updateProfile, logout }
})
