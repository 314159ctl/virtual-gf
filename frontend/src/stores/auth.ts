import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/utils/http'
import type { AuthTokens } from '@/types/models'

export const useAuthStore = defineStore('auth', () => {
  const guestReady = ref(false)
  const guestName = ref('访客')
  const userAvatar = ref<string | null>(null)

  async function initGuest() {
    if (localStorage.getItem('access_token')) {
      guestReady.value = true
      return
    }
    try {
      const res = await api.post<AuthTokens>('/auth/guest')
      localStorage.setItem('access_token', res.data.access_token)
      localStorage.setItem('refresh_token', res.data.refresh_token)
      guestReady.value = true
    } catch {
      localStorage.setItem('access_token', 'guest-fallback-' + Date.now())
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

  return { guestReady, guestName, userAvatar, initGuest, loadUserInfo }
})
