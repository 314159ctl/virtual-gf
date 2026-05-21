<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import TopBar from '@/components/layout/TopBar.vue'
import AdminStatsGrid from '@/components/admin/AdminStatsGrid.vue'
import AdminUserTable from '@/components/admin/AdminUserTable.vue'
import AdminSettingsPanel from '@/components/admin/AdminSettingsPanel.vue'
import type { UserItem } from '@/components/admin/AdminUserTable.vue'
import type { SystemSettings } from '@/components/admin/AdminSettingsPanel.vue'
import api from '@/utils/http'

const router = useRouter()

// ── 类型 ──
interface Stats {
  total_users: number; vip_users: number; total_characters: number
  total_conversations: number; total_messages: number
  today_messages: number; today_users: number; active_users_today: number
}
interface TrendDay { date: string; label: string; count: number }

// ── 仪表盘 ──
const stats = ref<Stats>({
  total_users: 0, vip_users: 0, total_characters: 0,
  total_conversations: 0, total_messages: 0,
  today_messages: 0, today_users: 0, active_users_today: 0,
})
const trend = ref<TrendDay[]>([])
const trendMax = ref(1)
const displayStats = ref({ ...stats.value })

function animateValue(key: keyof Stats, from: number, to: number) {
  if (from === to) return
  const duration = 800
  const start = performance.now()
  function tick(now: number) {
    const elapsed = now - start
    const progress = Math.min(elapsed / duration, 1)
    const eased = 1 - Math.pow(1 - progress, 3)
    displayStats.value[key] = Math.round(from + (to - from) * eased) as any
    if (progress < 1) requestAnimationFrame(tick)
  }
  requestAnimationFrame(tick)
}

async function loadStats() {
  try {
    const [sRes, tRes] = await Promise.all([
      api.get<Stats>('/admin/stats'),
      api.get<{ days: TrendDay[] }>('/admin/stats/trend'),
    ])
    const prev = { ...displayStats.value }
    stats.value = sRes.data
    trend.value = tRes.data.days
    trendMax.value = Math.max(...tRes.data.days.map(d => d.count), 1)
    for (const k of Object.keys(stats.value) as (keyof Stats)[]) {
      animateValue(k, prev[k] || 0, stats.value[k])
    }
  } catch { /* ignore */ }
}

// ── 用户管理 ──
const users = ref<UserItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 15
const search = ref('')
const loading = ref(false)
const error = ref('')

async function loadUsers() {
  loading.value = true; error.value = ''
  try {
    const res = await api.get<{ items: UserItem[]; total: number }>('/admin/users', {
      params: { search: search.value, page: page.value, page_size: pageSize },
    })
    users.value = res.data.items
    total.value = res.data.total
  } catch (e: any) {
    error.value = e?.response?.data?.detail || '加载失败'
  } finally { loading.value = false }
}

function onSearch(q: string) { page.value = 1; search.value = q; loadUsers() }
function onPageChange(p: number) { page.value = p; loadUsers() }

async function onToggleActive(user: UserItem) {
  try {
    await api.patch(`/admin/users/${user.id}`, { is_active: !user.is_active })
    user.is_active = !user.is_active
  } catch { /* ignore */ }
}

async function onSetTier(user: UserItem, tier: string) {
  try {
    await api.patch(`/admin/users/${user.id}`, { membership_tier: tier })
    user.membership_tier = tier
  } catch { /* ignore */ }
}

const resettingUserId = ref<string | null>(null)
const tempPassword = ref('')
const tempPasswordUser = ref('')

async function onResetPassword(user: UserItem) {
  resettingUserId.value = user.id
  try {
    const res = await api.post<{ temp_password: string; username: string }>(`/admin/users/${user.id}/reset-password`)
    tempPassword.value = res.data.temp_password
    tempPasswordUser.value = res.data.username
  } catch { /* ignore */ }
  finally { resettingUserId.value = null }
}

function closePwdDialog() {
  tempPassword.value = ''
  tempPasswordUser.value = ''
}

// ── 系统 API 配置 ──
const sysSettings = ref<SystemSettings>({
  painting_enabled: true, painting_api_key: '', painting_base_url: '', painting_model: '', painting_size: '2048x2048',
  vision_enabled: true, vision_api_key: '', vision_base_url: '', vision_model: '',
})
const settingsSaving = ref(false)
const settingsSaved = ref(false)

async function loadSettings() {
  try {
    const r = await api.get<SystemSettings>('/admin/settings')
    sysSettings.value = r.data
  } catch { /* ignore */ }
}

async function onSaveSettings(data: SystemSettings) {
  settingsSaving.value = true; settingsSaved.value = false
  try {
    const r = await api.put<SystemSettings>('/admin/settings', data)
    sysSettings.value = r.data
    settingsSaved.value = true
    setTimeout(() => { settingsSaved.value = false }, 2000)
  } catch { /* ignore */ }
  finally { settingsSaving.value = false }
}

onMounted(() => { loadStats(); loadUsers(); loadSettings() })
</script>

<template>
  <div class="admin-view">
    <TopBar title="管理面板" show-back @back="router.push('/')" />
    <div class="admin-content">
      <AdminStatsGrid
        :display-stats="displayStats"
        :stats="stats"
        :trend="trend"
        :trend-max="trendMax"
      />
      <AdminSettingsPanel
        :settings="sysSettings"
        :saving="settingsSaving"
        :saved="settingsSaved"
        @save="onSaveSettings"
      />
      <AdminUserTable
        :users="users"
        :total="total"
        :page="page"
        :page-size="pageSize"
        :loading="loading"
        :error="error"
        :resetting-user-id="resettingUserId"
        @search="onSearch"
        @update:page="onPageChange"
        @toggle-active="onToggleActive"
        @set-tier="onSetTier"
        @reset-password="onResetPassword"
      />

      <!-- 临时密码弹窗 -->
      <div v-if="tempPassword" class="pwd-dialog-overlay" @click.self="closePwdDialog">
        <div class="pwd-dialog">
          <h3>密码已重置</h3>
          <p class="pwd-dialog-user">用户：<strong>{{ tempPasswordUser }}</strong></p>
          <div class="temp-pwd-box">
            <code>{{ tempPassword }}</code>
          </div>
          <p class="pwd-dialog-note">请将临时密码发送给用户，首次登录后需要修改密码</p>
          <button class="btn-submit" @click="closePwdDialog">确定</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-bg);
}

.admin-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px 28px 32px;
}

.pwd-dialog-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center;
  z-index: 100;
}
.pwd-dialog {
  background: var(--color-surface);
  border-radius: 16px;
  padding: 28px 24px 20px;
  width: 360px; max-width: 90vw;
  text-align: center;
  box-shadow: var(--shadow-lg);
}
.pwd-dialog h3 {
  font-family: var(--font-heading);
  font-size: 16px; font-weight: 700;
  color: var(--color-text);
  margin-bottom: 8px;
}
.pwd-dialog-user {
  font-size: 13px; color: var(--color-text-muted);
  margin-bottom: 14px;
}
.temp-pwd-box {
  background: var(--color-bg);
  border: 1.5px dashed var(--color-primary);
  border-radius: 8px;
  padding: 14px;
  margin-bottom: 10px;
}
.temp-pwd-box code {
  font-size: 18px; font-weight: 700;
  color: var(--color-primary-dark);
  letter-spacing: 1px;
  font-family: 'Courier New', monospace;
  word-break: break-all;
}
.pwd-dialog-note {
  font-size: 12px; color: var(--color-text-muted);
  margin-bottom: 16px;
}
.pwd-dialog .btn-submit {
  width: 100%;
}

@media (max-width: 768px) {
  .admin-content { padding: 16px; }
}
</style>
