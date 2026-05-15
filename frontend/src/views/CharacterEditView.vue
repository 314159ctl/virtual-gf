<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore } from '@/stores/chat'
import { ArrowLeft, Save, RotateCcw } from 'lucide-vue-next'

const props = defineProps<{ characterId: string }>()
const router = useRouter()
const chat = useChatStore()

const loading = ref(true)
const saving = ref(false)
const error = ref('')

// 基本信息
const name = ref('')
const description = ref('')

// 人格字段
const task = ref('')
const appearance = ref('')
const background = ref('')
const personality = ref('')
const speakingStyle = ref('')
const preferences = ref('')
const outputExamples = ref('')
const behavioralRules = ref('')

// expression_style 数组
const exprConfirm = ref('')
const exprApologize = ref('')
const exprThanks = ref('')
const exprPetNames = ref('')
const exprEmoji = ref('')

interface ProfileData {
  name?: string
  description?: string
  personality_profile?: Record<string, any> | null
}

function loadProfile() {
  loading.value = true
  let char = chat.characters.find(c => c.id === props.characterId)
  if (!char) {
    error.value = '角色不存在'
    loading.value = false
    return
  }
  const profile = char.personality_profile
  name.value = char.name || ''
  description.value = char.description || ''
  if (profile) {
    task.value = profile.task || ''
    appearance.value = profile.appearance || ''
    background.value = profile.background || ''
    personality.value = profile.personality || ''
    speakingStyle.value = profile.speaking_style || ''
    preferences.value = profile.preferences || ''
    outputExamples.value = profile.output_examples || ''
    behavioralRules.value = profile.behavioral_rules || ''

    const expr = profile.expression_style || {}
    exprConfirm.value = (expr.confirm || []).join('、')
    exprApologize.value = (expr.apologize || []).join('、')
    exprThanks.value = (expr.thanks || []).join('、')
    exprPetNames.value = (expr.pet_names || []).join('、')
    exprEmoji.value = (expr.emoji || []).join('')
  }
  loading.value = false
}

function parseExpr(val: string): string[] {
  return val.split(/[，,、]/).map(s => s.trim()).filter(Boolean)
}

async function save() {
  saving.value = true
  try {
    const profile: Record<string, any> = {
      task: task.value,
      appearance: appearance.value,
      background: background.value,
      personality: personality.value,
      speaking_style: speakingStyle.value,
      expression_style: {
        confirm: parseExpr(exprConfirm.value),
        apologize: parseExpr(exprApologize.value),
        thanks: parseExpr(exprThanks.value),
        pet_names: parseExpr(exprPetNames.value),
        emoji: parseExpr(exprEmoji.value).join('').split(''),
      },
      preferences: preferences.value,
      output_examples: outputExamples.value,
      behavioral_rules: behavioralRules.value,
    }
    await chat.updateCharacter(props.characterId, {
      name: name.value,
      description: description.value,
      personality_profile: profile,
    })
  } finally {
    saving.value = false
  }
}

function goBack() {
  router.back()
}

onMounted(() => {
  if (!chat.characters.length) {
    chat.loadCharacters().then(loadProfile)
  } else {
    loadProfile()
  }
})
</script>

<template>
  <div class="edit-view">
    <header class="edit-header">
      <button class="back-btn" @click="goBack">
        <ArrowLeft :size="20" />
      </button>
      <h1>角色微调</h1>
      <button class="save-btn" :disabled="saving" @click="save">
        <Save :size="16" />
        <span>{{ saving ? '保存中...' : '保存' }}</span>
      </button>
    </header>

    <div v-if="error" class="edit-error">{{ error }}</div>

    <main v-if="!loading && !error" class="edit-main">
      <!-- 基本信息 -->
      <section class="edit-section">
        <h2 class="section-title">基本信息</h2>
        <label class="field">
          <span>名字</span>
          <input v-model="name" class="field-input" />
        </label>
        <label class="field">
          <span>简介</span>
          <input v-model="description" class="field-input" />
        </label>
      </section>

      <!-- 人设 -->
      <section class="edit-section">
        <h2 class="section-title">人设总览</h2>
        <label class="field">
          <span>任务描述</span>
          <textarea v-model="task" class="field-area" rows="3" />
        </label>
        <label class="field">
          <span>外貌</span>
          <textarea v-model="appearance" class="field-area" rows="3" />
        </label>
        <label class="field">
          <span>经历/背景</span>
          <textarea v-model="background" class="field-area" rows="4" />
        </label>
        <label class="field">
          <span>性格</span>
          <textarea v-model="personality" class="field-area" rows="4" />
        </label>
        <label class="field">
          <span>说话风格</span>
          <textarea v-model="speakingStyle" class="field-area" rows="3" />
        </label>
      </section>

      <!-- 表达风格 -->
      <section class="edit-section">
        <h2 class="section-title">表达风格</h2>
        <p class="section-hint">用中文逗号或顿号分隔多个条目</p>
        <label class="field">
          <span>确认时</span>
          <input v-model="exprConfirm" class="field-input" placeholder="嗯嗯、好的、明白啦" />
        </label>
        <label class="field">
          <span>道歉时</span>
          <input v-model="exprApologize" class="field-input" placeholder="对不起、抱歉啦" />
        </label>
        <label class="field">
          <span>感谢时</span>
          <input v-model="exprThanks" class="field-input" placeholder="谢谢、多谢啦" />
        </label>
        <label class="field">
          <span>对你的称呼</span>
          <input v-model="exprPetNames" class="field-input" placeholder="宝贝、亲爱的" />
        </label>
        <label class="field">
          <span>常用 emoji</span>
          <input v-model="exprEmoji" class="field-input" placeholder="😊💕✨" />
        </label>
      </section>

      <!-- 其他 -->
      <section class="edit-section">
        <h2 class="section-title">其他</h2>
        <label class="field">
          <span>偏好</span>
          <textarea v-model="preferences" class="field-area" rows="3" />
        </label>
        <label class="field">
          <span>输出示例</span>
          <p class="section-hint">用 \\ 分隔不同示例</p>
          <textarea v-model="outputExamples" class="field-area" rows="3" />
        </label>
        <label class="field">
          <span>行为规则</span>
          <textarea v-model="behavioralRules" class="field-area" rows="5" />
        </label>
      </section>
    </main>
  </div>
</template>

<style scoped>
.edit-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-bg);
}
.edit-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg);
  position: sticky;
  top: 0;
  z-index: 10;
}
.edit-header h1 {
  flex: 1;
  font-size: 18px;
  font-weight: 700;
  font-family: var(--font-heading);
  color: var(--color-text);
  margin: 0;
}
.back-btn {
  display: flex;
  align-items: center;
  padding: 4px;
  border: none;
  background: none;
  color: var(--color-text-secondary);
  cursor: pointer;
  border-radius: var(--radius-xs);
}
.back-btn:hover { color: var(--color-text); }
.save-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 16px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--color-primary);
  color: #fff;
  font-size: var(--text-sm);
  font-family: var(--font-body);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--duration-fast);
}
.save-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.save-btn:hover:not(:disabled) { opacity: 0.9; }
.edit-error {
  padding: 60px 24px;
  text-align: center;
  color: var(--color-error);
  font-size: var(--text-sm);
}
.edit-main {
  flex: 1;
  overflow-y: auto;
  padding: 20px 16px 40px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.edit-section {
  background: var(--color-surface);
  border-radius: var(--radius-md);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.section-title {
  font-size: 15px;
  font-weight: 700;
  font-family: var(--font-heading);
  color: var(--color-text);
  margin: 0;
}
.section-hint {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin: -8px 0 0;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.field span {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text-secondary);
  font-family: var(--font-body);
}
.field-input {
  padding: 6px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xs);
  font-size: var(--text-sm);
  font-family: var(--font-body);
  color: var(--color-text);
  background: var(--color-bg);
  outline: none;
  transition: border-color var(--duration-fast);
}
.field-input:focus { border-color: var(--color-primary); }
.field-area {
  padding: 8px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xs);
  font-size: var(--text-sm);
  font-family: var(--font-body);
  color: var(--color-text);
  background: var(--color-bg);
  outline: none;
  resize: vertical;
  line-height: 1.6;
  transition: border-color var(--duration-fast);
}
.field-area:focus { border-color: var(--color-primary); }
</style>
