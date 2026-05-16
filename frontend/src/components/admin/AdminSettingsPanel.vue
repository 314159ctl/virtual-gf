<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { Palette, Eye, Save, EyeOff } from 'lucide-vue-next'

export interface SystemSettings {
  painting_enabled: boolean; painting_api_key: string; painting_base_url: string
  painting_model: string; painting_size: string
  vision_enabled: boolean; vision_api_key: string; vision_base_url: string; vision_model: string
}

const props = defineProps<{
  settings: SystemSettings
  saving: boolean
  saved: boolean
}>()

const emit = defineEmits<{
  save: [data: SystemSettings]
}>()

const local = reactive<SystemSettings>({ ...props.settings })
watch(() => props.settings, (v) => Object.assign(local, v))

const showPaintingKeys = ref(false)
const showVisionKeys = ref(false)

function emitToggle(key: 'painting_enabled' | 'vision_enabled') {
  local[key] = !local[key]
  emit('save', { ...local })
}
</script>

<template>
  <div class="panel settings-panel">
    <div class="panel-header">
      <Palette :size="18" class="panel-icon" />
      <h3 class="panel-title">系统 API 配置</h3>
      <button class="save-btn" :disabled="saving" @click="emit('save', { ...local })">
        <Save :size="14" />
        {{ saving ? '保存中...' : '保存配置' }}
      </button>
      <span v-if="saved" class="saved-tag">✓ 已保存</span>
    </div>

    <div class="settings-grid">
      <div class="settings-card">
        <div class="settings-card-header">
          <Palette :size="16" />
          <span>绘画 API（豆包 Seedream）</span>
          <label class="toggle-switch">
            <input type="checkbox" :checked="local.painting_enabled" @change="emitToggle('painting_enabled')" />
            <span class="toggle-slider" />
          </label>
        </div>
        <div class="settings-body">
          <div class="field">
            <label>API Key</label>
            <div class="key-row">
              <input :type="showPaintingKeys ? 'text' : 'password'" v-model="local.painting_api_key" placeholder="输入绘画 API Key" />
              <button class="eye-btn" @click="showPaintingKeys = !showPaintingKeys">
                <EyeOff v-if="showPaintingKeys" :size="14" />
                <Eye v-else :size="14" />
              </button>
            </div>
          </div>
          <div class="field">
            <label>Base URL</label>
            <input type="text" v-model="local.painting_base_url" placeholder="https://ark.cn-beijing.volces.com/api/v3" />
          </div>
          <div class="field-row">
            <div class="field" style="flex:1">
              <label>Model</label>
              <input type="text" v-model="local.painting_model" placeholder="doubao-seedream-4-5-251128" />
            </div>
            <div class="field" style="width:120px">
              <label>尺寸</label>
              <select v-model="local.painting_size">
                <option value="2048x2048">2048</option>
                <option value="2304x1728">2304</option>
                <option value="2496x1664">2496</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <div class="settings-card">
        <div class="settings-card-header">
          <Eye :size="16" />
          <span>识图 API（豆包 Seed-2.0 Pro）</span>
          <label class="toggle-switch">
            <input type="checkbox" :checked="local.vision_enabled" @change="emitToggle('vision_enabled')" />
            <span class="toggle-slider" />
          </label>
        </div>
        <div class="settings-body">
          <div class="field">
            <label>API Key</label>
            <div class="key-row">
              <input :type="showVisionKeys ? 'text' : 'password'" v-model="local.vision_api_key" placeholder="输入识图 API Key" />
              <button class="eye-btn" @click="showVisionKeys = !showVisionKeys">
                <EyeOff v-if="showVisionKeys" :size="14" />
                <Eye v-else :size="14" />
              </button>
            </div>
          </div>
          <div class="field">
            <label>Base URL</label>
            <input type="text" v-model="local.vision_base_url" placeholder="https://ark.cn-beijing.volces.com/api/v3" />
          </div>
          <div class="field">
            <label>Model</label>
            <input type="text" v-model="local.vision_model" placeholder="doubao-seed-2-0-pro" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.panel {
  background: var(--color-surface);
  border-radius: 16px;
  border: 1px solid var(--color-border);
  overflow: hidden;
  margin-bottom: 20px;
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

.save-btn {
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
.save-btn:hover:not(:disabled) { background: var(--color-primary-dark); }
.save-btn:disabled { opacity: 0.5; cursor: not-allowed; }

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

.field-row { display: flex; gap: 12px; }

.key-row { display: flex; gap: 0; }
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

@media (max-width: 768px) {
  .settings-grid { grid-template-columns: 1fr; }
  .settings-card { border-right: none; border-bottom: 1px solid var(--color-border); }
  .settings-card:last-child { border-bottom: none; }
}
</style>
