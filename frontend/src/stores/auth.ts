import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/utils/http'
import type { User, AuthTokens } from '@/types/models'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const isAuthenticated = computed(() => !!localStorage.getItem('access_token'))

  async function register(email: string, username: string, password: string) {
    const res = await api.post('/auth/register', { email, username, password })
    user.value = res.data
    await login(email, password)
  }

  async function login(email: string, password: string) {
    const res = await api.post<AuthTokens>('/auth/login', { email, password })
    localStorage.setItem('access_token', res.data.access_token)
    localStorage.setItem('refresh_token', res.data.refresh_token)
    await fetchUser()
  }

  async function fetchUser() {
    try {
      const res = await api.get<User>('/users/me')
      user.value = res.data
    } catch {
      logout()
    }
  }

  function logout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    user.value = null
  }

  return { user, isAuthenticated, register, login, fetchUser, logout }
})
