<script setup lang="ts">
import { ref, computed } from 'vue'
import { Search, ChevronLeft, ChevronRight, KeyRound } from 'lucide-vue-next'

export interface UserItem {
  id: string; email: string; username: string; membership_tier: string
  is_active: boolean; is_admin: boolean; created_at: string
}

const props = defineProps<{
  users: UserItem[]
  total: number
  page: number
  pageSize: number
  loading: boolean
  error: string
  resettingUserId: string | null
}>()

const emit = defineEmits<{
  search: [q: string]
  'update:page': [p: number]
  toggleActive: [user: UserItem]
  setTier: [user: UserItem, tier: string]
  resetPassword: [user: UserItem]
}>()

const searchInput = ref('')

const totalPages = computed(() => Math.ceil(props.total / props.pageSize) || 1)

function doSearch() { emit('search', searchInput.value) }
function prevPage() { if (props.page > 1) emit('update:page', props.page - 1) }
function nextPage() { if (props.page * props.pageSize < props.total) emit('update:page', props.page + 1) }
</script>

<template>
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
              <button class="act-btn" :class="{ danger: u.is_active }" @click="emit('toggleActive', u)">
                {{ u.is_active ? '禁用' : '启用' }}
              </button>
              <button class="act-btn" @click="emit('setTier', u, u.membership_tier === 'vip' ? 'free' : 'vip')">
                {{ u.membership_tier === 'vip' ? '降级' : '升 VIP' }}
              </button>
              <button
                class="act-btn reset-btn"
                :disabled="resettingUserId === u.id"
                @click="emit('resetPassword', u)"
              >
                <KeyRound v-if="resettingUserId !== u.id" :size="13" />
                <span v-else class="spinner-sm" />
                {{ resettingUserId === u.id ? '重置中' : '重置密码' }}
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

    <div class="pagination" v-if="total > pageSize">
      <button :disabled="page <= 1" @click="prevPage"><ChevronLeft :size="16" /></button>
      <span class="page-info">{{ page }} / {{ totalPages }} 页（共 {{ total }} 条）</span>
      <button :disabled="page * pageSize >= total" @click="nextPage"><ChevronRight :size="16" /></button>
    </div>
  </div>
</template>

<style scoped>
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
  flex-wrap: wrap;
}

.panel-icon { color: var(--color-primary); flex-shrink: 0; }

.panel-title {
  font-family: var(--font-heading);
  font-size: 15px;
  font-weight: 700;
  color: var(--color-text);
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

.table-wrap { overflow-x: auto; }

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

.user-table tbody tr { transition: background 0.15s; }
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
.tier-chip.vip { background: #fef3c7; color: #92400e; }

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
.reset-btn {
  display: inline-flex; align-items: center; gap: 4px;
}
.spinner-sm {
  width: 12px; height: 12px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  display: inline-block;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
.self-tag { color: var(--color-text-muted); font-size: 12px; }

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

@media (max-width: 768px) {
  .search-box { margin-left: 0; width: 100%; }
  .search-input { flex: 1; }
}
</style>
