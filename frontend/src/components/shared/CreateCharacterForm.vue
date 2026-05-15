<script setup lang="ts">
import { ref, computed } from 'vue'
import { Sparkles, ChevronLeft, Brain, MessageSquareText, Camera } from 'lucide-vue-next'
import { useChatStore } from '@/stores/chat'
import { useAuthStore } from '@/stores/auth'
import type { PersonalityProfile } from '@/types/models'

const emit = defineEmits<{
  submit: [data: { name: string; description: string; system_prompt: string; personality_profile: Record<string, any> | null; files: File[]; avatarFile: File | null }]
  cancel: []
}>()

const chat = useChatStore()
const auth = useAuthStore()

// null = 方式选择, 'describe' = 描述生成, 'chat' = 聊天导入
const mode = ref<string | null>(null)
const step = ref(1)
const generating = ref(false)
const analyzing = ref(false)
const error = ref('')

// ── 共享字段 ──
const name = ref('')
const description = ref('')
const profile = ref<PersonalityProfile>({})
const useAdvanced = ref(false)
const systemPrompt = ref('')

// 方式一 — 用户描述
const userDescription = ref('')

// 方式二 — 聊天导入
const chatLogText = ref('')
const avatarInput = ref<HTMLInputElement | null>(null)
const avatarFile = ref<File | null>(null)
const avatarPreview = ref<string | null>(null)

const chatFileInput = ref<HTMLInputElement | null>(null)
const chatFileName = ref('')
const analysisResult = ref<Record<string, any> | null>(null)

function extractName(desc: string): string {
  const match = desc.match(/(?:叫|名叫|名字是|名为)\s*[「「]?(\S+?)[」」]?[,，。\s]/)
  return match?.[1] || ''
}

function smartSlice(text: string, max = 80): string {
  if (text.length <= max) return text
  // 在 max 之前找最近的句子结束符
  const truncated = text.slice(0, max)
  const m = truncated.match(/[。！？\n]/g)
  if (m) {
    const last = truncated.lastIndexOf(m[m.length - 1])
    if (last > max * 0.5) return truncated.slice(0, last + 1)
  }
  // 退而求其次找逗号
  const comma = truncated.lastIndexOf('，')
  if (comma > max * 0.5) return truncated.slice(0, comma + 1)
  return truncated
}

function selectMode(m: string) {
  mode.value = m
  step.value = 1
  error.value = ''
  name.value = ''
  description.value = ''
}

function backToSelect() {
  mode.value = null
  step.value = 1
  error.value = ''
  name.value = ''
  description.value = ''
  profile.value = {}
  userDescription.value = ''
  chatLogText.value = ''
  chatFileName.value = ''
  analysisResult.value = null
  avatarFile.value = null
  avatarPreview.value = null
}

// ── 头像 ──
function triggerAvatar() {
  avatarInput.value?.click()
}

function onAvatarChange(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  avatarFile.value = file
  const reader = new FileReader()
  reader.onload = () => {
    avatarPreview.value = reader.result as string
  }
  reader.readAsDataURL(file)
  target.value = ''
}

// ══════════════════════════════════════════════
// 方式一：描述生成
// ══════════════════════════════════════════════

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
    if (!name.value) {
      name.value = extractName(userDescription.value)
    }
    if (!description.value && result.personality) {
      description.value = smartSlice(result.personality)
    }
    step.value = 2
  } catch (e: any) {
    console.error('AI 生成角色失败:', e)
    error.value = e?.response?.data?.detail || e?.message || 'AI 生成失败，请重试'
  } finally {
    generating.value = false
  }
}

function onSkipToAdvanced() {
  useAdvanced.value = true
  step.value = 2
}

function doSubmitDescribe() {
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
    files: [],
    avatarFile: avatarFile.value,
  })
}

// ══════════════════════════════════════════════
// 方式二：聊天记录导入（ex-skill 风格）
// ══════════════════════════════════════════════

function triggerChatFile() {
  chatFileInput.value?.click()
}

async function onChatFileSelected(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  chatFileName.value = file.name
  const reader = new FileReader()
  reader.onload = () => {
    chatLogText.value = reader.result as string
  }
  reader.readAsText(file, 'UTF-8')
  target.value = ''
}

async function onAnalyzeChat() {
  if (!chatLogText.value.trim()) {
    error.value = '请先粘贴或上传聊天记录'
    return
  }
  if (!auth.hasApiKey) { auth.promptApiKey(); return }
  error.value = ''
  analyzing.value = true
  try {
    // 不传现有 profile，完全从聊天记录蒸馏角色
    const result = await chat.analyzeChatLogs(chatLogText.value, null)
    if (result.enhanced_profile) {
      analysisResult.value = result.enhanced_profile
      profile.value = result.enhanced_profile
      if (!description.value && result.enhanced_profile.personality) {
        description.value = smartSlice(result.enhanced_profile.personality)
      }
      step.value = 2
    }
  } catch (e: any) {
    console.error('聊天分析失败:', e)
    error.value = e?.response?.data?.detail || e?.message || '分析失败，请重试'
  } finally {
    analyzing.value = false
  }
}

function doSubmitChat() {
  error.value = ''
  if (!name.value.trim()) {
    error.value = '请输入角色名字'
    return
  }
  emit('submit', {
    name: name.value.trim(),
    description: description.value.trim(),
    system_prompt: '',
    personality_profile: profile.value,
    files: [],
    avatarFile: avatarFile.value,
  })
}

const expr = computed(() => profile.value.expression_style || {})
</script>

<template>
  <form class="wizard" @submit.prevent>
    <!-- ═══════════════════════════════════════ -->
    <!-- 方式选择页                              -->
    <!-- ═══════════════════════════════════════ -->
    <div v-if="mode === null" class="mode-select">
      <h3 class="step-title" style="text-align:center">选择创建方式</h3>

      <div class="mode-cards">
        <button type="button" class="mode-card" @click="selectMode('describe')">
          <div class="mode-icon"><Sparkles :size="28" /></div>
          <div class="mode-name">描述生成</div>
          <div class="mode-desc">描述你想要的角色，AI 自动生成完整人设</div>
        </button>

        <button type="button" class="mode-card" @click="selectMode('chat')">
          <div class="mode-icon"><MessageSquareText :size="28" /></div>
          <div class="mode-name">聊天记录导入</div>
          <div class="mode-desc">粘贴聊天记录，AI 蒸馏出完整角色人格</div>
        </button>
      </div>
    </div>

    <!-- ═══════════════════════════════════════ -->
    <!-- 方式一：描述生成                          -->
    <!-- ═══════════════════════════════════════ -->
    <template v-if="mode === 'describe'">
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
          <button type="button" class="btn btn-outline" @click="backToSelect">
            返回选择
          </button>
          <div class="step-actions-right">
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
      </div>

      <!-- Step 2: 精细调整 -->
      <div v-if="step === 2" class="step-content">
        <h3 class="step-title">{{ useAdvanced ? '编写角色设定' : '调整角色设定' }}</h3>

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

        <!-- 头像上传 -->
        <div class="form-group">
          <label class="form-label">角色头像</label>
          <div class="avatar-upload">
            <input ref="avatarInput" type="file" accept="image/*" class="file-input-hidden" @change="onAvatarChange" />
            <button type="button" class="avatar-pick" @click="triggerAvatar">
              <template v-if="avatarPreview">
                <img :src="avatarPreview" class="avatar-preview-img" />
              </template>
              <template v-else>
                <Camera :size="20" />
                <span>选择头像</span>
              </template>
            </button>
          </div>
        </div>

        <template v-if="useAdvanced">
          <div class="form-group">
            <label class="form-label">角色人设（系统提示词）</label>
            <textarea v-model="systemPrompt" class="form-textarea" rows="8" placeholder="描述角色的性格、说话风格、背景故事等..." maxlength="5000" />
          </div>
        </template>

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
          <div class="form-group">
            <label class="form-label">表达风格</label>
            <div class="expr-grid">
              <div class="expr-item">
                <span class="expr-label">确认用语</span>
                <input
                  :value="(expr.confirm || []).join('、')"
                  @input="profile.expression_style = { ...expr, confirm: ($event.target as HTMLInputElement).value.split('、').filter(Boolean) }"
                  class="form-input" placeholder="好的呀、嗯嗯"
                />
              </div>
              <div class="expr-item">
                <span class="expr-label">道歉用语</span>
                <input
                  :value="(expr.apologize || []).join('、')"
                  @input="profile.expression_style = { ...expr, apologize: ($event.target as HTMLInputElement).value.split('、').filter(Boolean) }"
                  class="form-input" placeholder="对不起嘛"
                />
              </div>
              <div class="expr-item">
                <span class="expr-label">感谢用语</span>
                <input
                  :value="(expr.thanks || []).join('、')"
                  @input="profile.expression_style = { ...expr, thanks: ($event.target as HTMLInputElement).value.split('、').filter(Boolean) }"
                  class="form-input" placeholder="谢谢你呀"
                />
              </div>
              <div class="expr-item">
                <span class="expr-label">对用户称呼</span>
                <input
                  :value="(expr.pet_names || []).join('、')"
                  @input="profile.expression_style = { ...expr, pet_names: ($event.target as HTMLInputElement).value.split('、').filter(Boolean) }"
                  class="form-input" placeholder="宝贝、亲爱的"
                />
              </div>
              <div class="expr-item">
                <span class="expr-label">常用 emoji</span>
                <input
                  :value="(expr.emoji || []).join('')"
                  @input="profile.expression_style = { ...expr, emoji: Array.from(($event.target as HTMLInputElement).value).filter(c => /\p{Emoji}/u.test(c)) }"
                  class="form-input" placeholder="🥰💕😊"
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
            <textarea v-model="profile.output_examples" class="form-textarea" rows="3" placeholder="用 \ 分隔不同示例回复&#10;例如：在想你呀～🥰\\今天工作辛苦了\\晚安呀✨" />
          </div>
          <div class="form-group">
            <label class="form-label">行为规则</label>
            <textarea v-model="profile.behavioral_rules" class="form-textarea" rows="2" placeholder="回复长度、语言要求、特殊约束..." />
          </div>
        </template>

        <div v-if="error" class="error-msg">{{ error }}</div>

        <div class="step-actions">
          <button type="button" class="btn btn-outline" @click="step = 1">
            <ChevronLeft :size="16" /> 上一步
          </button>
          <button type="button" class="btn btn-primary" @click="doSubmitDescribe">
            创建角色
          </button>
        </div>
      </div>
    </template>

    <!-- ═══════════════════════════════════════ -->
    <!-- 方式二：聊天记录导入                      -->
    <!-- ═══════════════════════════════════════ -->
    <template v-if="mode === 'chat'">
      <!-- Step indicator -->
      <div class="steps">
        <div class="step-dot" :class="{ active: step >= 1, done: step > 1 }">1</div>
        <div class="step-line" :class="{ active: step > 1 }" />
        <div class="step-dot" :class="{ active: step >= 2 }">2</div>
      </div>

      <!-- Step 1: 上传聊天记录 -->
      <div v-if="step === 1" class="step-content">
        <h3 class="step-title">导入聊天记录</h3>
        <p class="step-desc">粘贴聊天记录，AI 会从中蒸馏出说话者的完整角色人格——包括性格、说话风格、口头禅、情感模式等。</p>

        <!-- 文件上传 -->
        <div class="form-group">
          <label class="form-label">上传文件（可选）</label>
          <p class="field-hint">支持 .txt 文本文件，如导出的微信/QQ聊天记录</p>
          <input
            ref="chatFileInput"
            type="file"
            accept=".txt,.md,.json,.csv"
            class="file-input-hidden"
            @change="onChatFileSelected"
          />
          <button type="button" class="upload-btn" @click="triggerChatFile">
            {{ chatFileName || '选择文件...' }}
          </button>
        </div>

        <!-- 文本粘贴 -->
        <div class="form-group">
          <label class="form-label">或直接粘贴聊天记录</label>
          <textarea
            v-model="chatLogText"
            class="form-textarea chat-log-textarea"
            rows="8"
            placeholder="将聊天记录粘贴到此处...&#10;&#10;格式示例：&#10;2024-03-15 14:30 对方：今天去哪吃饭呀&#10;2024-03-15 14:31 你：想吃火锅了～&#10;2024-03-15 14:32 对方：好啊，老地方见"
          />
          <div class="char-count">{{ chatLogText.length }} 字</div>
        </div>

        <div v-if="error" class="error-msg">{{ error }}</div>

        <div class="step-actions">
          <button type="button" class="btn btn-outline" @click="backToSelect">
            返回选择
          </button>
          <button
            type="button"
            class="btn btn-primary"
            :disabled="analyzing || !chatLogText.trim()"
            @click="onAnalyzeChat"
          >
            <Brain v-if="!analyzing" :size="16" />
            <span v-if="analyzing" class="spinner" />
            {{ analyzing ? '正在蒸馏角色人格...' : 'AI 开始蒸馏' }}
          </button>
        </div>
      </div>

      <!-- Step 2: 确认信息 + 创建 -->
      <div v-if="step === 2" class="step-content">
        <h3 class="step-title">确认角色信息</h3>

        <!-- 分析结果总览 -->
        <div v-if="analysisResult" class="analysis-result">
          <h4 class="analysis-title">蒸馏结果 — 角色设定总览</h4>
          <div v-if="analysisResult.background" class="analysis-section">
            <span class="analysis-label">背景经历</span>
            <p class="analysis-val">{{ analysisResult.background }}</p>
          </div>
          <div v-if="analysisResult.personality" class="analysis-section">
            <span class="analysis-label">性格特点</span>
            <p class="analysis-val">{{ analysisResult.personality }}</p>
          </div>
          <div v-if="analysisResult.speaking_style" class="analysis-section">
            <span class="analysis-label">说话风格</span>
            <p class="analysis-val">{{ analysisResult.speaking_style }}</p>
          </div>
          <div v-if="analysisResult.output_examples" class="analysis-section">
            <span class="analysis-label">输出示例</span>
            <p class="analysis-val examples-val">{{ analysisResult.output_examples.split('\\').filter(Boolean).join(' / ') }}</p>
          </div>
          <div v-if="analysisResult.expression_style" class="analysis-section">
            <span class="analysis-label">口头禅 / 称呼</span>
            <p class="analysis-val">
              <template v-if="analysisResult.expression_style.confirm?.length">确认：{{ analysisResult.expression_style.confirm.join('、') }}<br/></template>
              <template v-if="analysisResult.expression_style.pet_names?.length">称呼：{{ analysisResult.expression_style.pet_names.join('、') }}</template>
            </p>
          </div>
        </div>

        <!-- 名字 + 描述 -->
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

        <!-- 头像上传 -->
        <div class="form-group">
          <label class="form-label">角色头像</label>
          <div class="avatar-upload">
            <input ref="avatarInput" type="file" accept="image/*" class="file-input-hidden" @change="onAvatarChange" />
            <button type="button" class="avatar-pick" @click="triggerAvatar">
              <template v-if="avatarPreview">
                <img :src="avatarPreview" class="avatar-preview-img" />
              </template>
              <template v-else>
                <Camera :size="20" />
                <span>选择头像</span>
              </template>
            </button>
          </div>
        </div>

        <div v-if="error" class="error-msg">{{ error }}</div>

        <div class="step-actions">
          <button type="button" class="btn btn-outline" @click="step = 1">
            <ChevronLeft :size="16" /> 上一步
          </button>
          <button type="button" class="btn btn-primary" @click="doSubmitChat">
            创建角色
          </button>
        </div>
      </div>
    </template>
  </form>

  <!-- API Key 警告弹窗 -->
  <div v-if="auth.showApiKeyWarning" class="api-key-overlay" @click.self="auth.dismissApiKeyWarning()">
    <div class="api-key-dialog">
      <div class="dialog-icon">🔑</div>
      <h3>尚未设置 API Key</h3>
      <p>需要配置自己的 DeepSeek API Key 才能使用 AI 对话、角色生成等功能。</p>
      <div class="dialog-actions">
        <button class="dialog-btn cancel" @click="auth.dismissApiKeyWarning()">稍后再说</button>
        <button class="dialog-btn confirm" @click="auth.dismissApiKeyWarning()">我知道了</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.wizard {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ── Mode select ── */
.mode-select {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.mode-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.mode-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 22px 16px;
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all var(--duration) var(--ease-bounce);
  text-align: center;
}
.mode-card:hover {
  border-color: var(--color-primary);
  background: var(--color-sakura-light);
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}
.mode-icon {
  width: 52px; height: 52px;
  border-radius: var(--radius-full);
  background: var(--color-sakura);
  display: flex; align-items: center; justify-content: center;
  color: var(--color-primary);
  transition: all var(--duration-fast);
}
.mode-card:hover .mode-icon {
  background: var(--color-primary);
  color: #fff;
}
.mode-name {
  font-family: var(--font-heading);
  font-size: var(--text-base);
  font-weight: 700;
  color: var(--color-text);
}
.mode-desc {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  line-height: 1.5;
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
  width: 28px; height: 28px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700;
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
  width: 50px; height: 2px;
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
.step-actions-right {
  display: flex;
  gap: 8px;
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
  width: 14px; height: 14px;
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

/* ── Avatar upload ── */
.avatar-upload {
  display: flex;
  align-items: center;
  gap: 12px;
}
.avatar-pick {
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
  min-width: 100px;
  min-height: 60px;
  justify-content: center;
}
.avatar-pick:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: var(--color-sakura);
}
.avatar-preview-img {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-full);
  object-fit: cover;
  border: 2px solid var(--color-primary);
}

/* ── File upload ── */
.file-input-hidden { display: none; }

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

.chat-log-textarea {
  font-size: var(--text-xs);
  font-family: 'Courier New', monospace;
  line-height: 1.8;
}

/* ── Analysis result ── */
.analysis-result {
  background: var(--color-sakura-light);
  border: 1px solid var(--color-primary-light);
  border-radius: var(--radius-sm);
  padding: 14px 16px;
}
.analysis-title {
  font-family: var(--font-heading);
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-primary-dark);
  margin-bottom: 10px;
}
.analysis-section {
  margin-bottom: 10px;
}
.analysis-section:last-child { margin-bottom: 0; }
.analysis-label {
  color: var(--color-primary-dark);
  font-weight: 600;
  font-size: var(--text-xs);
  margin-bottom: 2px;
}
.analysis-val {
  color: var(--color-text-secondary);
  font-size: var(--text-xs);
  line-height: 1.6;
  margin: 0;
}
.examples-val {
  font-style: italic;
  color: var(--color-primary-dark);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}

/* ── API Key Warning Dialog ── */
.api-key-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  animation: apiFadeIn 0.2s ease;
}
.api-key-dialog {
  background: var(--color-bg);
  border-radius: var(--radius-md);
  padding: 32px 28px 24px;
  max-width: 360px;
  width: 90%;
  text-align: center;
  box-shadow: var(--shadow-lg);
  animation: apiScaleIn 0.25s var(--ease-bounce);
}
.dialog-icon { font-size: 40px; margin-bottom: 12px; }
.api-key-dialog h3 {
  font-size: 18px;
  font-weight: 700;
  font-family: var(--font-heading);
  color: var(--color-text);
  margin: 0 0 8px;
}
.api-key-dialog p {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  margin: 0 0 20px;
  line-height: 1.6;
}
.dialog-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
}
.dialog-btn {
  padding: 8px 20px;
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  font-family: var(--font-body);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--duration-fast);
  border: none;
}
.dialog-btn.cancel {
  background: var(--color-surface);
  color: var(--color-text-secondary);
}
.dialog-btn.cancel:hover { background: var(--color-border); }
.dialog-btn.confirm {
  background: var(--color-primary);
  color: #fff;
}
.dialog-btn.confirm:hover { opacity: 0.9; }

@keyframes apiFadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes apiScaleIn { from { opacity: 0; transform: scale(0.92); } to { opacity: 1; transform: scale(1); } }
</style>
