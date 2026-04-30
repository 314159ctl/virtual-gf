<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Sparkles, ChevronRight, ChevronLeft, Upload, FileText, X } from 'lucide-vue-next'
import { useChatStore } from '@/stores/chat'
import { useFileUpload } from '@/composables/useFileUpload'
import type { PersonalityProfile } from '@/types/models'

const emit = defineEmits<{
  submit: [data: { name: string; description: string; system_prompt: string; personality_profile: Record<string, any> | null; files: File[] }]
  cancel: []
}>()

const chat = useChatStore()
const { selectedFiles, filePreviews, fileInput, error: uploadError, selectFiles, onFilesSelected, removeFile, clearFiles } = useFileUpload()

const step = ref(1)
const generating = ref(false)
const error = ref('')

// Step 1 — 用户描述
const userDescription = ref('')

// Step 2 — 结构化人格
const name = ref('')
const description = ref('')
const profile = ref<PersonalityProfile>({})
const useAdvanced = ref(false) // 高级模式：直接写 system_prompt
const systemPrompt = ref('')

// 从 AI 生成结果中提取名字
function extractName(desc: string): string {
  const match = desc.match(/(?:叫|名叫|名字是|名为)\s*[「「]?(\S+?)[」」]?[,，。\s]/)
  return match?.[1] || ''
}

async function onGenerate() {
  if (!userDescription.value.trim()) {
    error.value = '请先描述你想要的角色'
    return
  }
  error.value = ''
  generating.value = true
  try {
    const result = await chat.generateCharacterProfile(userDescription.value)
    profile.value = result
    // 尝试从描述中提取名字
    if (!name.value) {
      name.value = extractName(userDescription.value)
    }
    // 从 personality 中提取简介
    if (!description.value && result.personality) {
      description.value = result.personality.slice(0, 50)
    }
    step.value = 2
  } catch (e: any) {
    error.value = e?.response?.data?.detail || 'AI 生成失败，请重试'
  } finally {
    generating.value = false
  }
}

function onSkipToAdvanced() {
  useAdvanced.value = true
  step.value = 2
}

function onSubmit() {
  error.value = ''
  if (!name.value.trim()) {
    error.value = '请输入角色名字'
    return
  }
  if (useAdvanced.value && !systemPrompt.value.trim()) {
    error.value = '请输入角色人设'
    return
  }
  emit('submit', {
    name: name.value.trim(),
    description: description.value.trim(),
    system_prompt: useAdvanced.value ? systemPrompt.value.trim() : '',
    personality_profile: useAdvanced.value ? null : profile.value,
    files: selectedFiles.value,
  })
}

const expr = computed(() => profile.value.expression_style || {})
</script>

<template>
  <form class="wizard" @submit.prevent="onSubmit">
    <!-- Step indicator -->
    <div class="steps">
      <div class="step-dot" :class="{ active: step >= 1, done: step > 1 }">1</div>
      <div class="step-line" :class="{ active: step > 1 }" />
      <div class="step-dot" :class="{ active: step >= 2 }">2</div>
    </div>

    <!-- Step 1: 描述角色 -->
    <div v-if="step === 1" class="step-content">
      <h3 class="step-title">描述你想要的角色</h3>
      <p class="step-desc">告诉 AI 你想要什么样的角色，越详细越好。包含年龄、性格、关系、背景等。</p>

      <textarea
        v-model="userDescription"
        class="desc-textarea"
        rows="5"
        placeholder="例如：一个20岁的大学女生，温柔可爱，是我的女朋友。喜欢做饭和看动漫，说话软软的，会撒娇。我们是大学同学，在一起两年了..."
        maxlength="500"
      />
      <div class="char-count">{{ userDescription.length }} / 500</div>

      <div v-if="error" class="error-msg">{{ error }}</div>

      <div class="step-actions">
        <button type="button" class="btn btn-outline" @click="onSkipToAdvanced">
          跳过，手写设定
        </button>
        <button
          type="button"
          class="btn btn-primary"
          :disabled="generating || !userDescription.trim()"
          @click="onGenerate"
        >
          <Sparkles v-if="!generating" :size="16" />
          <span v-if="generating" class="spinner" />
          {{ generating ? '正在生成...' : 'AI 一键生成' }}
        </button>
      </div>
    </div>

    <!-- Step 2: 精细调整 -->
    <div v-if="step === 2" class="step-content">
      <h3 class="step-title">{{ useAdvanced ? '编写角色设定' : '调整角色设定' }}</h3>

      <!-- 基本信息 -->
      <div class="form-row">
        <div class="form-group">
          <label class="form-label">角色名字 *</label>
          <input v-model="name" type="text" class="form-input" placeholder="例如：小暖" maxlength="20" />
        </div>
        <div class="form-group">
          <label class="form-label">简短描述</label>
          <input v-model="description" type="text" class="form-input" placeholder="一句话描述" maxlength="50" />
        </div>
      </div>

      <!-- 高级模式：直接写 system_prompt -->
      <template v-if="useAdvanced">
        <div class="form-group">
          <label class="form-label">角色人设（系统提示词）</label>
          <textarea
            v-model="systemPrompt"
            class="form-textarea"
            rows="8"
            placeholder="描述角色的性格、说话风格、背景故事等..."
            maxlength="5000"
          />
        </div>
      </template>

      <!-- 结构化模式 -->
      <template v-else>
        <div class="form-group">
          <label class="form-label">外貌描写</label>
          <textarea v-model="profile.appearance" class="form-textarea" rows="2" placeholder="描述角色的外貌特征..." />
        </div>

        <div class="form-group">
          <label class="form-label">背景经历</label>
          <textarea v-model="profile.background" class="form-textarea" rows="3" placeholder="角色的成长经历、与用户的关系..." />
        </div>

        <div class="form-group">
          <label class="form-label">性格特点</label>
          <textarea v-model="profile.personality" class="form-textarea" rows="3" placeholder="性格的多个层面..." />
        </div>

        <div class="form-group">
          <label class="form-label">说话风格</label>
          <textarea v-model="profile.speaking_style" class="form-textarea" rows="2" placeholder="语气、用词习惯..." />
        </div>

        <!-- 表达风格 -->
        <div class="form-group">
          <label class="form-label">表达风格</label>
          <div class="expr-grid">
            <div class="expr-item">
              <span class="expr-label">确认用语</span>
              <input
                :value="(expr.confirm || []).join('、')"
                @input="profile.expression_style = { ...expr, confirm: ($event.target as HTMLInputElement).value.split('、').filter(Boolean) }"
                class="form-input"
                placeholder="好的呀、嗯嗯"
              />
            </div>
            <div class="expr-item">
              <span class="expr-label">道歉用语</span>
              <input
                :value="(expr.apologize || []).join('、')"
                @input="profile.expression_style = { ...expr, apologize: ($event.target as HTMLInputElement).value.split('、').filter(Boolean) }"
                class="form-input"
                placeholder="对不起嘛"
              />
            </div>
            <div class="expr-item">
              <span class="expr-label">感谢用语</span>
              <input
                :value="(expr.thanks || []).join('、')"
                @input="profile.expression_style = { ...expr, thanks: ($event.target as HTMLInputElement).value.split('、').filter(Boolean) }"
                class="form-input"
                placeholder="谢谢你呀"
              />
            </div>
            <div class="expr-item">
              <span class="expr-label">对用户称呼</span>
              <input
                :value="(expr.pet_names || []).join('、')"
                @input="profile.expression_style = { ...expr, pet_names: ($event.target as HTMLInputElement).value.split('、').filter(Boolean) }"
                class="form-input"
                placeholder="宝贝、亲爱的"
              />
            </div>
            <div class="expr-item">
              <span class="expr-label">常用 emoji</span>
              <input
                :value="(expr.emoji || []).join('')"
                @input="profile.expression_style = { ...expr, emoji: Array.from(($event.target as HTMLInputElement).value).filter(c => /\p{Emoji}/u.test(c)) }"
                class="form-input"
                placeholder="🥰💕😊"
              />
            </div>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">兴趣爱好</label>
          <textarea v-model="profile.preferences" class="form-textarea" rows="2" placeholder="喜欢什么、讨厌什么..." />
        </div>

        <div class="form-group">
          <label class="form-label">输出示例</label>
          <textarea
            v-model="profile.output_examples"
            class="form-textarea"
            rows="3"
            placeholder="用 \ 分隔不同示例回复&#10;例如：在想你呀～🥰\\今天工作辛苦了\\晚安呀✨"
          />
        </div>

        <div class="form-group">
          <label class="form-label">行为规则</label>
          <textarea v-model="profile.behavioral_rules" class="form-textarea" rows="2" placeholder="回复长度、语言要求、特殊约束..." />
        </div>
      </template>

      <!-- 参考资料上传 -->
      <div class="form-group">
        <label class="form-label">参考资料（可选）</label>
        <p class="field-hint">上传角色相关的文本资料，让角色更鲜活。支持 .txt .md .pdf .docx</p>

        <input
          ref="fileInput"
          type="file"
          accept=".txt,.md,.pdf,.docx"
          multiple
          class="file-input-hidden"
          @change="onFilesSelected"
        />

        <button type="button" class="upload-btn" @click="selectFiles">
          <Upload :size="16" />
          选择文件
        </button>

        <div v-if="uploadError" class="error-msg">{{ uploadError }}</div>

        <div v-if="filePreviews.length > 0" class="file-list">
          <div v-for="(f, i) in filePreviews" :key="i" class="file-chip">
            <FileText :size="14" class="file-icon" />
            <span class="file-name">{{ f.name }}</span>
            <span class="file-size">{{ (f.size / 1024).toFixed(1) }}KB</span>
            <button type="button" class="file-remove" @click="removeFile(i)">
              <X :size="12" />
            </button>
          </div>
        </div>
      </div>

      <div v-if="error" class="error-msg">{{ error }}</div>

      <div class="step-actions">
        <button type="button" class="btn btn-outline" @click="step = 1">
          <ChevronLeft :size="16" /> 上一步
        </button>
        <button type="submit" class="btn btn-primary">
          创建角色
        </button>
      </div>
    </div>
  </form>
</template>

<style scoped>
.wizard {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ── Steps indicator ── */
.steps {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
  margin-bottom: 4px;
}
.step-dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  font-family: var(--font-heading);
  background: var(--color-bg);
  color: var(--color-text-muted);
  border: 2px solid var(--color-border);
  transition: all var(--duration) var(--ease-bounce);
}
.step-dot.active {
  background: var(--color-primary);
  color: #fff;
  border-color: var(--color-primary);
}
.step-dot.done {
  background: var(--color-success);
  border-color: var(--color-success);
}
.step-line {
  width: 60px;
  height: 2px;
  background: var(--color-border);
  transition: background var(--duration);
}
.step-line.active {
  background: var(--color-primary);
}

/* ── Step content ── */
.step-content {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.step-title {
  font-family: var(--font-heading);
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--color-text);
}
.step-desc {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  line-height: 1.5;
}

/* ── Form elements ── */
.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.form-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.form-label {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-text-secondary);
  font-family: var(--font-heading);
}
.form-input {
  width: 100%;
  padding: 9px 12px;
  border: 1.5px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  font-family: var(--font-body);
  outline: none;
  transition: all var(--duration-fast) var(--ease-smooth);
  background: var(--color-bg);
  color: var(--color-text);
  box-sizing: border-box;
}
.form-input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(255,125,175,0.08);
}
.form-textarea {
  width: 100%;
  padding: 9px 12px;
  border: 1.5px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  font-family: var(--font-body);
  outline: none;
  transition: all var(--duration-fast) var(--ease-smooth);
  background: var(--color-bg);
  color: var(--color-text);
  resize: vertical;
  min-height: 60px;
  line-height: 1.6;
  box-sizing: border-box;
}
.form-textarea:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(255,125,175,0.08);
}

.desc-textarea {
  width: 100%;
  padding: 12px 14px;
  border: 1.5px solid var(--color-border);
  border-radius: var(--radius);
  font-size: var(--text-sm);
  font-family: var(--font-body);
  outline: none;
  transition: all var(--duration-fast) var(--ease-smooth);
  background: var(--color-bg);
  color: var(--color-text);
  resize: vertical;
  min-height: 100px;
  line-height: 1.7;
}
.desc-textarea:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(255,125,175,0.08);
}

.char-count {
  text-align: right;
  font-size: 10px;
  color: var(--color-text-muted);
  margin-top: -8px;
}

/* ── Expression style grid ── */
.expr-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.expr-item {
  display: flex;
  align-items: center;
  gap: 8px;
}
.expr-label {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  white-space: nowrap;
  min-width: 60px;
}

/* ── Actions ── */
.step-actions {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-top: 4px;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 20px;
  border: none;
  border-radius: var(--radius-full);
  font-size: var(--text-sm);
  font-family: var(--font-body);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-bounce);
}
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn-primary {
  background: var(--color-primary);
  color: #fff;
}
.btn-primary:hover:not(:disabled) {
  background: var(--color-primary-dark);
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}
.btn-outline {
  background: transparent;
  color: var(--color-text-secondary);
  border: 1.5px solid var(--color-border);
}
.btn-outline:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: var(--color-sakura-light);
}

.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

.error-msg {
  padding: 8px 12px;
  background: rgba(232,128,138,0.1);
  border: 1px solid rgba(232,128,138,0.2);
  border-radius: var(--radius-xs);
  font-size: var(--text-xs);
  color: var(--color-error);
  text-align: center;
}

/* ── File upload ── */
.file-input-hidden {
  display: none;
}

.field-hint {
  font-size: 10px;
  color: var(--color-text-muted);
  margin-top: -2px;
}

.upload-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  background: var(--color-sakura-light);
  border: 1.5px dashed var(--color-border-strong);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-family: var(--font-body);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-smooth);
}
.upload-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: var(--color-sakura);
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.file-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xs);
  font-size: var(--text-xs);
}
.file-icon {
  color: var(--color-primary);
  flex-shrink: 0;
}
.file-name {
  flex: 1;
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.file-size {
  color: var(--color-text-muted);
  flex-shrink: 0;
}
.file-remove {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border: none;
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  border-radius: var(--radius-full);
  flex-shrink: 0;
  padding: 0;
}
.file-remove:hover {
  background: var(--color-error);
  color: #fff;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
