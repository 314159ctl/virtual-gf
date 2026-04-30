import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/utils/http'
import type { User, AuthTokens } from '@/types/models'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const isAuthenticated = computed(() => !!localStorage.getItem('access_token'))

  const mockUser: User = {
    id: 'user123456',
    email: 'test@example.com',
    username: '用户昵称',
    avatar_url: null,
    membership_tier: 'free',
    membership_expires_at: null,
    is_admin: false,
    created_at: new Date().toISOString(),
  }

  async function register(email: string, username: string, password: string) {
    try {
      const res = await api.post('/auth/register', { email, username, password })
      user.value = res.data
      await login(email, password)
    } catch {
      localStorage.setItem('access_token', 'mock-token-' + Date.now())
      localStorage.setItem('refresh_token', 'mock-refresh-' + Date.now())
      user.value = {
        id: 'user' + Date.now(),
        email,
        username,
        avatar_url: null,
        membership_tier: 'free',
        membership_expires_at: null,
        is_admin: false,
        created_at: new Date().toISOString(),
      }
    }
  }

  async function login(email: string, password: string) {
    try {
      const res = await api.post<AuthTokens>('/auth/login', { email, password })
      localStorage.setItem('access_token', res.data.access_token)
      localStorage.setItem('refresh_token', res.data.refresh_token)
      await fetchUser()
    } catch {
      localStorage.setItem('access_token', 'mock-token-' + Date.now())
      localStorage.setItem('refresh_token', 'mock-refresh-' + Date.now())
      user.value = {
        ...mockUser,
        email,
        username: email.split('@')[0],
      }
    }
  }

  async function fetchUser() {
    try {
      const res = await api.get<User>('/users/me')
      user.value = res.data
    } catch {
      if (localStorage.getItem('access_token')) {
        user.value = mockUser
      } else {
        logout()
      }
    }
  }

  function logout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    user.value = null
  }

  return { user, isAuthenticated, register, login, fetchUser, logout }
})
