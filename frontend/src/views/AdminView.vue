<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Users, MessageCircle, Sparkles, Crown, Search, ChevronLeft, ChevronRight, TrendingUp, Zap, Activity, Palette, Eye, Save, EyeOff } from 'lucide-vue-next'
import TopBar from '@/components/layout/TopBar.vue'
import api from '@/utils/http'

const router = useRouter()

// ── 类型 ──
interface Stats {
  total_users: number; vip_users: number; total_characters: number
  total_conversations: number; total_messages: number
  today_messages: number; today_users: number; active_users_today: number
}
interface TrendDay { date: string; label: string; count: number }
interface UserItem {
  id: string; email: string; username: string; membership_tier: string
  is_active: boolean; is_admin: boolean; created_at: string
}

// ── 状态 ──
const stats = ref<Stats>({
  total_users: 0, vip_users: 0, total_characters: 0,
  total_conversations: 0, total_messages: 0,
  today_messages: 0, today_users: 0, active_users_today: 0,
})
const trend = ref<TrendDay[]>([])
const trendMax = ref(1)
const displayStats = ref({ ...stats.value })

const users = ref<UserItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 15
const search = ref('')
const searchInput = ref('')
const loading = ref(false)
const error = ref('')

// ── 数字跳动动画 ──
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

onMounted(() => { loadStats(); loadUsers(); loadSettings() })

function doSearch() { page.value = 1; search.value = searchInput.value; loadUsers() }
function prevPage() { if (page.value > 1) { page.value--; loadUsers() } }
function nextPage() { if (page.value * pageSize < total.value) { page.value++; loadUsers() } }

async function toggleActive(user: UserItem) {
  try {
    await api.patch(`/admin/users/${user.id}`, { is_active: !user.is_active })
    user.is_active = !user.is_active
  } catch { /* ignore */ }
}

async function setTier(user: UserItem, tier: string) {
  try {
    await api.patch(`/admin/users/${user.id}`, { membership_tier: tier })
    user.membership_tier = tier
  } catch { /* ignore */ }
}

const totalPages = computed(() => Math.ceil(total.value / pageSize) || 1)

// ── 系统 API 配置 ──
interface SystemSettings {
  painting_enabled: boolean; painting_api_key: string; painting_base_url: string
  painting_model: string; painting_size: string
  vision_enabled: boolean; vision_api_key: string; vision_base_url: string; vision_model: string
}
const sysSettings = ref<SystemSettings>({
  painting_enabled: true, painting_api_key: '', painting_base_url: '', painting_model: '', painting_size: '2048x2048',
  vision_enabled: true, vision_api_key: '', vision_base_url: '', vision_model: '',
})
const showPaintingKeys = ref(false)
const showVisionKeys = ref(false)
const settingsSaving = ref(false)
const settingsSaved = ref(false)

async function loadSettings() {
  try {
    const r = await api.get<SystemSettings>('/admin/settings')
    sysSettings.value = r.data
  } catch { /* ignore */ }
}

async function saveSettings() {
  settingsSaving.value = true; settingsSaved.value = false
  try {
    const r = await api.put<SystemSettings>('/admin/settings', {
      painting_enabled: sysSettings.value.painting_enabled,
      painting_api_key: sysSettings.value.painting_api_key,
      painting_base_url: sysSettings.value.painting_base_url,
      painting_model: sysSettings.value.painting_model,
      painting_size: sysSettings.value.painting_size,
      vision_enabled: sysSettings.value.vision_enabled,
      vision_api_key: sysSettings.value.vision_api_key,
      vision_base_url: sysSettings.value.vision_base_url,
      vision_model: sysSettings.value.vision_model,
    })
    sysSettings.value = r.data
    settingsSaved.value = true
    setTimeout(() => { settingsSaved.value = false }, 2000)
  } catch { /* ignore */ }
  finally { settingsSaving.value = false }
}

// ── 柱状图 bar hover ──
const hoveredBar = ref<number | null>(null)
</script>

<template>
  <div class="admin-view">
    <TopBar title="管理面板" show-back @back="router.push('/')" />

    <div class="admin-content">
      <!-- ══════ 统计卡片 ══════ -->
      <div class="stats-grid">
        <!-- 用户总数 -->
        <div class="stat-card card-pink">
          <div class="card-glow" />
          <div class="card-body">
            <div class="card-icon-box">
              <Users :size="22" />
            </div>
            <div class="card-info">
              <span class="card-value">{{ displayStats.total_users.toLocaleString() }}</span>
              <span class="card-label">总用户</span>
            </div>
          </div>
          <div class="card-footer">
            <span class="card-sub">+{{ displayStats.today_users }} 今日新增</span>
          </div>
        </div>

        <!-- VIP 用户 -->
        <div class="stat-card card-amber">
          <div class="card-glow" />
          <div class="card-body">
            <div class="card-icon-box">
              <Crown :size="22" />
            </div>
            <div class="card-info">
              <span class="card-value">{{ displayStats.vip_users.toLocaleString() }}</span>
              <span class="card-label">VIP 会员</span>
            </div>
          </div>
          <div class="card-footer">
            <span class="card-sub">{{ stats.total_users > 0 ? Math.round(stats.vip_users / stats.total_users * 100) : 0 }}% 占比</span>
          </div>
        </div>

        <!-- 总消息 -->
        <div class="stat-card card-purple">
          <div class="card-glow" />
          <div class="card-body">
            <div class="card-icon-box">
              <MessageCircle :size="22" />
            </div>
            <div class="card-info">
              <span class="card-value">{{ displayStats.total_messages.toLocaleString() }}</span>
              <span class="card-label">总消息</span>
            </div>
          </div>
          <div class="card-footer">
            <span class="card-sub">{{ displayStats.total_conversations }} 个会话</span>
          </div>
        </div>

        <!-- 今日消息 -->
        <div class="stat-card card-rose">
          <div class="card-glow" />
          <div class="card-body">
            <div class="card-icon-box">
              <Zap :size="22" />
            </div>
            <div class="card-info">
              <span class="card-value">{{ displayStats.today_messages.toLocaleString() }}</span>
              <span class="card-label">今日消息</span>
            </div>
          </div>
          <div class="card-footer">
            <span class="card-sub">{{ displayStats.active_users_today }} 人活跃</span>
          </div>
        </div>

        <!-- 角色 -->
        <div class="stat-card card-teal">
          <div class="card-glow" />
          <div class="card-body">
            <div class="card-icon-box">
              <Sparkles :size="22" />
            </div>
            <div class="card-info">
              <span class="card-value">{{ displayStats.total_characters.toLocaleString() }}</span>
              <span class="card-label">角色总数</span>
            </div>
          </div>
          <div class="card-footer">
            <span class="card-sub">AI 虚拟女友</span>
          </div>
        </div>
      </div>

      <!-- ══════ 图表 + 快捷信息 ══════ -->
      <div class="middle-row">
        <!-- 7 天消息趋势图 -->
        <div class="panel chart-panel">
          <div class="panel-header">
            <TrendingUp :size="18" class="panel-icon" />
            <h3 class="panel-title">近 7 天消息趋势</h3>
          </div>
          <div class="chart-body">
            <svg class="chart-svg" viewBox="0 0 600 200" preserveAspectRatio="xMidYMid meet">
              <!-- 网格线 -->
              <line v-for="i in 4" :key="'gl'+i"
                :x1="60" :x2="580" :y1="20 + (i-1) * 40" :y2="20 + (i-1) * 40"
                stroke="var(--color-border)" stroke-width="1" stroke-dasharray="4,4" opacity="0.4"
              />
              <!-- Y 轴标签 -->
              <text v-for="i in 5" :key="'yl'+i"
                :x="52" :y="23 + (4-i) * 40"
                text-anchor="end" font-size="11" fill="var(--color-text-muted)"
              >{{ Math.round(trendMax * (5-i) / 4) }}</text>
              <!-- 柱状图 -->
              <g v-for="(d, i) in trend" :key="d.date">
                <rect
                  :x="72 + i * 76"
                  :y="180 - (d.count / trendMax) * 160"
                  width="44" :height="(d.count / trendMax) * 160"
                  rx="6"
                  :fill="hoveredBar === i ? `url(#barGradHover)` : `url(#barGrad)`"
                  @mouseenter="hoveredBar = i"
                  @mouseleave="hoveredBar = null"
                  style="cursor: pointer; transition: fill 0.2s;"
                />
                <!-- 数值悬浮 -->
                <text
                  v-if="hoveredBar === i"
                  :x="72 + i * 76 + 22" :y="176 - (d.count / trendMax) * 160"
                  text-anchor="middle" font-size="12" font-weight="700"
                  fill="var(--color-primary)"
                >{{ d.count }}</text>
                <!-- 日期标签 -->
                <text
                  :x="72 + i * 76 + 22" y="195"
                  text-anchor="middle" font-size="11"
                  :fill="hoveredBar === i ? 'var(--color-primary-dark)' : 'var(--color-text-muted)'"
                >{{ d.label }}</text>
              </g>
              <defs>
                <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="#f598a5" />
                  <stop offset="100%" stop-color="#f598a520" />
                </linearGradient>
                <linearGradient id="barGradHover" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="#e87d8a" />
                  <stop offset="100%" stop-color="#e87d8a40" />
                </linearGradient>
              </defs>
            </svg>
          </div>
        </div>

        <!-- 快捷信息 -->
        <div class="panel info-panel">
          <div class="panel-header">
            <Activity :size="18" class="panel-icon" />
            <h3 class="panel-title">概览</h3>
          </div>
          <div class="info-list">
            <div class="info-item">
              <span class="info-dot active" />
              <div>
                <span class="info-val">{{ displayStats.active_users_today }}</span>
                <span class="info-hint">今日活跃用户</span>
              </div>
            </div>
            <div class="info-item">
              <span class="info-dot new" />
              <div>
                <span class="info-val">{{ displayStats.today_users }}</span>
                <span class="info-hint">今日新注册</span>
              </div>
            </div>
            <div class="info-item">
              <span class="info-dot" />
              <div>
                <span class="info-val">{{ displayStats.total_conversations }}</span>
                <span class="info-hint">总会话数</span>
              </div>
            </div>
            <div class="info-item">
              <span class="info-dot" />
              <div>
                <span class="info-val">{{ stats.total_users > 0 ? (stats.total_messages / stats.total_users).toFixed(1) : '0' }}</span>
                <span class="info-hint">人均消息</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ══════ 系统 API 配置 ══════ -->
      <div class="panel settings-panel">
        <div class="panel-header">
          <Palette :size="18" class="panel-icon" />
          <h3 class="panel-title">系统 API 配置</h3>
          <button class="save-settings-btn" :disabled="settingsSaving" @click="saveSettings">
            <Save :size="14" />
            {{ settingsSaving ? '保存中...' : '保存配置' }}
          </button>
          <span v-if="settingsSaved" class="saved-tag">✓ 已保存</span>
        </div>

        <div class="settings-grid">
          <!-- 绘画 API -->
          <div class="settings-card">
            <div class="settings-card-header">
              <Palette :size="16" />
              <span>绘画 API（豆包 Seedream）</span>
              <label class="toggle-switch">
                <input type="checkbox" v-model="sysSettings.painting_enabled" />
                <span class="toggle-slider" />
              </label>
            </div>
            <div class="settings-body">
              <div class="field">
                <label>API Key</label>
                <div class="key-row">
                  <input :type="showPaintingKeys ? 'text' : 'password'" v-model="sysSettings.painting_api_key" placeholder="输入绘画 API Key" />
                  <button class="eye-btn" @click="showPaintingKeys = !showPaintingKeys">
                    <EyeOff v-if="showPaintingKeys" :size="14" />
                    <Eye v-else :size="14" />
                  </button>
                </div>
              </div>
              <div class="field">
                <label>Base URL</label>
                <input type="text" v-model="sysSettings.painting_base_url" placeholder="https://ark.cn-beijing.volces.com/api/v3" />
              </div>
              <div class="field-row">
                <div class="field" style="flex:1">
                  <label>Model</label>
                  <input type="text" v-model="sysSettings.painting_model" placeholder="doubao-seedream-4-5-251128" />
                </div>
                <div class="field" style="width:120px">
                  <label>尺寸</label>
                  <select v-model="sysSettings.painting_size">
                    <option value="2048x2048">2048</option>
                    <option value="2304x1728">2304</option>
                    <option value="2496x1664">2496</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          <!-- 识图 API -->
          <div class="settings-card">
            <div class="settings-card-header">
              <Eye :size="16" />
              <span>识图 API（豆包 Seed-2.0 Pro）</span>
              <label class="toggle-switch">
                <input type="checkbox" v-model="sysSettings.vision_enabled" />
                <span class="toggle-slider" />
              </label>
            </div>
            <div class="settings-body">
              <div class="field">
                <label>API Key</label>
                <div class="key-row">
                  <input :type="showVisionKeys ? 'text' : 'password'" v-model="sysSettings.vision_api_key" placeholder="输入识图 API Key" />
                  <button class="eye-btn" @click="showVisionKeys = !showVisionKeys">
                    <EyeOff v-if="showVisionKeys" :size="14" />
                    <Eye v-else :size="14" />
                  </button>
                </div>
              </div>
              <div class="field">
                <label>Base URL</label>
                <input type="text" v-model="sysSettings.vision_base_url" placeholder="https://ark.cn-beijing.volces.com/api/v3" />
              </div>
              <div class="field">
                <label>Model</label>
                <input type="text" v-model="sysSettings.vision_model" placeholder="doubao-seed-2-0-pro" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ══════ 用户管理 ══════ -->
      <div class="panel user-panel">
        <div class="panel-header">
          <Search :size="18" class="panel-icon" />
          <h3 class="panel-title">用户管理</h3>
          <div class="search-box">
            <input
              v-model="searchInput"
              type="text"
              class="search-input"
              placeholder="搜索邮箱或用户名..."
              @keyup.enter="doSearch"
            />
            <button class="search-btn" @click="doSearch">搜索</button>
          </div>
        </div>

        <p v-if="error" class="error-msg">{{ error }}</p>

        <div class="table-wrap" v-if="users.length">
          <table class="user-table">
            <thead>
              <tr>
                <th style="width:40px"></th>
                <th>用户</th>
                <th>会员</th>
                <th>状态</th>
                <th>角色</th>
                <th>注册时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="u in users" :key="u.id" :class="{ inactive: !u.is_active }">
                <td>
                  <div class="user-avatar-circle" :class="u.membership_tier">
                    {{ u.username[0]?.toUpperCase() || '?' }}
                  </div>
                </td>
                <td>
                  <div class="user-cell">
                    <span class="user-name">{{ u.username }}</span>
                    <span class="user-email">{{ u.email }}</span>
                  </div>
                </td>
                <td>
                  <span class="tier-chip" :class="u.membership_tier">
                    {{ u.membership_tier === 'vip' ? '⭐ VIP' : '免费' }}
                  </span>
                </td>
                <td>
                  <span class="status-chip" :class="{ active: u.is_active }">
                    {{ u.is_active ? '正常' : '已禁用' }}
                  </span>
                </td>
                <td>
                  <span v-if="u.is_admin" class="role-chip admin">管理员</span>
                  <span v-else class="role-chip user">用户</span>
                </td>
                <td class="date-cell">{{ new Date(u.created_at).toLocaleDateString('zh-CN') }}</td>
                <td class="actions-cell" v-if="!u.is_admin">
                  <button class="act-btn" :class="{ danger: u.is_active }" @click="toggleActive(u)">
                    {{ u.is_active ? '禁用' : '启用' }}
                  </button>
                  <button class="act-btn" @click="setTier(u, u.membership_tier === 'vip' ? 'free' : 'vip')">
                    {{ u.membership_tier === 'vip' ? '降级' : '升 VIP' }}
                  </button>
                </td>
                <td v-else class="actions-cell">
                  <span class="self-tag">—</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <p v-if="!loading && !users.length && !error" class="empty-msg">暂无用户数据</p>
        <p v-if="loading" class="loading-msg">加载中...</p>

        <!-- 分页 -->
        <div class="pagination" v-if="total > pageSize">
          <button :disabled="page <= 1" @click="prevPage"><ChevronLeft :size="16" /></button>
          <span class="page-info">{{ page }} / {{ totalPages }} 页（共 {{ total }} 条）</span>
          <button :disabled="page * pageSize >= total" @click="nextPage"><ChevronRight :size="16" /></button>
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

/* ══════ 统计卡片 ══════ */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  position: relative;
  background: var(--color-surface);
  border-radius: 16px;
  padding: 20px;
  overflow: hidden;
  border: 1px solid var(--color-border);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: default;
}
.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0,0,0,0.08);
}

.card-glow {
  position: absolute;
  top: -40px; right: -40px;
  width: 120px; height: 120px;
  border-radius: 50%;
  opacity: 0.12;
  transition: opacity 0.3s;
}
.stat-card:hover .card-glow { opacity: 0.2; }

/* 各卡片配色 */
.card-pink  .card-glow { background: #f598a5; }
.card-pink  .card-icon-box { background: #fef0f3; color: #e87d8a; }
.card-pink  { border-top: 3px solid #e87d8a; }

.card-amber .card-glow { background: #f59e0b; }
.card-amber .card-icon-box { background: #fffbeb; color: #d97706; }
.card-amber { border-top: 3px solid #f59e0b; }

.card-purple .card-glow { background: #a78bfa; }
.card-purple .card-icon-box { background: #f5f3ff; color: #7c3aed; }
.card-purple { border-top: 3px solid #a78bfa; }

.card-rose .card-glow { background: #fb7185; }
.card-rose .card-icon-box { background: #fff1f2; color: #e11d48; }
.card-rose { border-top: 3px solid #fb7185; }

.card-teal .card-glow { background: #2dd4bf; }
.card-teal .card-icon-box { background: #f0fdfa; color: #0d9488; }
.card-teal { border-top: 3px solid #2dd4bf; }

.card-body {
  display: flex;
  align-items: center;
  gap: 14px;
  position: relative;
  z-index: 1;
}

.card-icon-box {
  width: 46px; height: 46px;
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}

.card-info {
  display: flex; flex-direction: column;
  min-width: 0;
}

.card-value {
  font-family: var(--font-heading);
  font-size: 28px;
  font-weight: 800;
  color: var(--color-text);
  line-height: 1.1;
  letter-spacing: -1px;
}

.card-label {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-top: 2px;
  font-weight: 500;
}

.card-footer {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid var(--color-border);
  position: relative; z-index: 1;
}

.card-sub {
  font-size: 11px;
  color: var(--color-text-muted);
  font-weight: 500;
}

/* ══════ 中间行（图表 + 概览） ══════ */
.middle-row {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}

.panel {
  background: var(--color-surface);
  border-radius: 16px;
  border: 1px solid var(--color-border);
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border);
}

.panel-icon { color: var(--color-primary); flex-shrink: 0; }

.panel-title {
  font-family: var(--font-heading);
  font-size: 15px;
  font-weight: 700;
  color: var(--color-text);
}

/* 图表 */
.chart-body {
  padding: 20px 24px 12px;
}

.chart-svg {
  width: 100%;
  height: 220px;
}

/* 概览列表 */
.info-list {
  padding: 8px 0;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  transition: background 0.15s;
}
.info-item:hover { background: var(--color-sakura-light); }

.info-dot {
  width: 10px; height: 10px;
  border-radius: 50%;
  background: var(--color-border-strong);
  flex-shrink: 0;
}
.info-dot.active { background: #22c55e; box-shadow: 0 0 6px #22c55e60; }
.info-dot.new { background: var(--color-primary); box-shadow: 0 0 6px #f598a560; }

.info-val {
  font-family: var(--font-heading);
  font-size: 20px;
  font-weight: 700;
  color: var(--color-text);
}

.info-hint {
  font-size: 12px;
  color: var(--color-text-muted);
  display: block;
  margin-top: 1px;
}

/* ══════ 用户表格 ══════ */
.user-panel .panel-header {
  flex-wrap: wrap; gap: 12px;
}

.search-box {
  display: flex; align-items: center; gap: 8px;
  margin-left: auto;
}

.search-input {
  width: 200px;
  padding: 7px 12px;
  border: 1.5px solid var(--color-border);
  border-radius: 8px;
  font-size: 13px;
  background: var(--color-bg);
  color: var(--color-text);
  outline: none;
  transition: border-color 0.2s;
}
.search-input:focus { border-color: var(--color-primary); }

.search-btn {
  padding: 7px 14px;
  border: none;
  border-radius: 8px;
  background: var(--color-primary);
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}
.search-btn:hover { background: var(--color-primary-dark); }

.table-wrap {
  overflow-x: auto;
}

.user-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.user-table th {
  text-align: left;
  padding: 12px 16px;
  background: var(--color-bg);
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: nowrap;
}

.user-table td {
  padding: 10px 16px;
  border-top: 1px solid var(--color-border);
  color: var(--color-text);
  vertical-align: middle;
}

.user-table tbody tr {
  transition: background 0.15s;
}
.user-table tbody tr:hover { background: var(--color-sakura-light); }
.user-table tbody tr.inactive { opacity: 0.45; }
.user-table tbody tr.inactive:hover { opacity: 0.65; }

.user-avatar-circle {
  width: 34px; height: 34px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 700;
  color: var(--color-text-secondary);
  background: var(--color-bg);
  border: 2px solid var(--color-border);
}
.user-avatar-circle.vip {
  background: linear-gradient(135deg, #fef3c7, #fde68a);
  border-color: #f59e0b;
  color: #92400e;
}

.user-cell { display: flex; flex-direction: column; gap: 2px; }
.user-name { font-weight: 600; }
.user-email { font-size: 11px; color: var(--color-text-muted); }

.tier-chip {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 11px; font-weight: 600;
  background: var(--color-bg);
  color: var(--color-text-muted);
}
.tier-chip.vip {
  background: #fef3c7; color: #92400e;
}

.status-chip {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 11px; font-weight: 600;
  background: #fef2f2; color: #dc2626;
}
.status-chip::before {
  content: ''; width: 6px; height: 6px;
  border-radius: 50%; background: #dc2626;
}
.status-chip.active {
  background: #f0fdf4; color: #16a34a;
}
.status-chip.active::before { background: #22c55e; }

.role-chip {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 11px; font-weight: 600;
}
.role-chip.admin { background: #fdf2f8; color: #be185d; }
.role-chip.user { background: var(--color-bg); color: var(--color-text-muted); }

.date-cell { white-space: nowrap; font-size: 12px; color: var(--color-text-muted); }

.actions-cell { white-space: nowrap; }
.act-btn {
  padding: 5px 12px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: var(--color-bg);
  color: var(--color-text-secondary);
  font-size: 12px;
  cursor: pointer;
  margin-right: 6px;
  transition: all 0.15s;
  font-weight: 500;
}
.act-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: var(--color-sakura-light);
}
.act-btn.danger:hover {
  border-color: #dc2626;
  color: #dc2626;
  background: #fef2f2;
}
.self-tag { color: var(--color-text-muted); font-size: 12px; }

/* ══════ 分页 ══════ */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  padding: 14px 20px;
  border-top: 1px solid var(--color-border);
}
.pagination button {
  width: 32px; height: 32px;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.15s;
}
.pagination button:hover:not(:disabled) {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: var(--color-sakura-light);
}
.pagination button:disabled { opacity: 0.3; cursor: not-allowed; }
.page-info { font-size: 13px; color: var(--color-text-muted); }

.error-msg {
  padding: 12px 20px; margin: 0;
  color: var(--color-error); font-size: 13px; text-align: center;
}
.empty-msg, .loading-msg {
  padding: 40px 20px; text-align: center;
  color: var(--color-text-muted); font-size: 13px;
}

/* ══════ 系统 API 配置 ══════ */
.settings-panel { margin-bottom: 20px; }

.settings-panel .panel-header {
  justify-content: flex-start; flex-wrap: wrap;
}

.save-settings-btn {
  margin-left: auto;
  display: inline-flex; align-items: center; gap: 6px;
  padding: 7px 16px;
  border: none;
  border-radius: 8px;
  background: var(--color-primary);
  color: #fff;
  font-size: 13px; font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}
.save-settings-btn:hover:not(:disabled) { background: var(--color-primary-dark); }
.save-settings-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.saved-tag {
  font-size: 12px; font-weight: 600; color: #16a34a;
  padding: 4px 10px; background: #f0fdf4;
  border-radius: 6px;
}

.settings-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0;
}

.settings-card {
  padding: 20px;
  border-right: 1px solid var(--color-border);
}
.settings-card:last-child { border-right: none; }

.settings-card-header {
  display: flex; align-items: center; gap: 8px;
  font-size: 14px; font-weight: 600;
  color: var(--color-text);
  margin-bottom: 16px;
}
.settings-card-header svg { color: var(--color-primary); flex-shrink: 0; }

/* 切换开关 */
.toggle-switch {
  margin-left: auto;
  position: relative; width: 40px; height: 22px;
  cursor: pointer;
}
.toggle-switch input { display: none; }
.toggle-slider {
  position: absolute; inset: 0;
  background: var(--color-border-strong);
  border-radius: 22px;
  transition: background 0.2s;
}
.toggle-slider::after {
  content: '';
  position: absolute; top: 2px; left: 2px;
  width: 18px; height: 18px;
  border-radius: 50%;
  background: #fff;
  transition: transform 0.2s;
}
.toggle-switch input:checked + .toggle-slider { background: var(--color-primary); }
.toggle-switch input:checked + .toggle-slider::after { transform: translateX(18px); }

.settings-body {
  display: flex; flex-direction: column; gap: 12px;
}

.field {
  display: flex; flex-direction: column; gap: 4px;
}
.field label {
  font-size: 11px; font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase; letter-spacing: 0.5px;
}
.field input, .field select {
  padding: 8px 12px;
  border: 1.5px solid var(--color-border);
  border-radius: 8px;
  font-size: 13px;
  background: var(--color-bg);
  color: var(--color-text);
  outline: none;
  transition: border-color 0.2s;
  font-family: var(--font-body);
}
.field input:focus, .field select:focus { border-color: var(--color-primary); }
.field select { cursor: pointer; }

.field-row {
  display: flex; gap: 12px;
}

.key-row {
  display: flex; gap: 0;
}
.key-row input {
  flex: 1;
  border-top-right-radius: 0; border-bottom-right-radius: 0;
  border-right: none;
}
.eye-btn {
  width: 36px;
  border: 1.5px solid var(--color-border);
  border-left: none;
  border-radius: 0 8px 8px 0;
  background: var(--color-bg);
  color: var(--color-text-muted);
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.15s;
}
.eye-btn:hover { color: var(--color-primary); background: var(--color-sakura-light); }

/* ══════ 响应式 ══════ */
@media (max-width: 1200px) {
  .stats-grid { grid-template-columns: repeat(3, 1fr); }
  .middle-row { grid-template-columns: 1fr; }
}
@media (max-width: 768px) {
  .admin-content { padding: 16px; }
  .stats-grid { grid-template-columns: repeat(2, 1fr); gap: 10px; }
  .stat-card { padding: 14px; }
  .card-value { font-size: 22px; }
  .search-box { margin-left: 0; width: 100%; }
  .search-input { flex: 1; }
  .settings-grid { grid-template-columns: 1fr; }
  .settings-card { border-right: none; border-bottom: 1px solid var(--color-border); }
  .settings-card:last-child { border-bottom: none; }
}
</style>
