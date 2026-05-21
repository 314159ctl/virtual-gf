<script setup lang="ts">
import { ref } from 'vue'
import { X, Heart, MessageCircle, UserCircle, Sparkles, Settings, Key, Image } from 'lucide-vue-next'

const emit = defineEmits<{ close: [] }>()

const currentStep = ref(0)

const steps = [
  {
    icon: Heart,
    title: '欢迎来到恋爱对话模拟器',
    subtitle: '一个能陪你聊天、记住你说过的话、有自己小情绪的 AI 女友',
    color: '#FF7DAF',
    items: [
      '你可以创建属于自己的 AI 角色，她会记住你们的每一次对话',
      '她有自己的性格、说话风格，甚至会根据聊天内容产生不同的情绪',
      '先来看看怎么使用吧，很简单的 ~',
    ],
  },
  {
    icon: Sparkles,
    title: '第一步：创建你的角色',
    subtitle: '有两种方式创建角色，选你喜欢的方式就好',
    color: '#C4A1FF',
    items: [
      '描述生成：用几句话描述你想要的女生（性格、年龄、关系等），AI 会自动生成完整的角色人设，包括外貌、背景、说话风格',
      '聊天记录导入：如果你有和某人的聊天记录，粘贴进来，AI 会从中蒸馏出完整的角色人格',
      '创建时可以上传头像，也可以后续在角色编辑中修改',
    ],
  },
  {
    icon: MessageCircle,
    title: '第二步：开始聊天',
    subtitle: '就像平时发消息一样，她随时在线',
    color: '#FF7DAF',
    items: [
      '点击角色卡片进入聊天界面，支持发送文字、表情和图片',
      '如果她回复了图片，长按可以保存到本地',
      '消息可以撤回（点击消息旁的 ✕），也可以重新生成 AI 回复',
      '电脑端按 Enter 发送，Shift+Enter 换行；手机端按换行键换行，点击右侧按钮发送',
    ],
  },
  {
    icon: Key,
    title: '第三步：设置 API Key',
    subtitle: '这是让 AI 女友"活过来"的关键一步',
    color: '#FFD4A8',
    items: [
      '点击右上角头像进入「个人中心」，找到「API 配置」区域',
      '需要一个兼容 OpenAI 接口的 API Key（如 DeepSeek、通义千问等）',
      '填入 API Key、接口地址和模型名称，点击测试通过后保存',
      '不设置 API Key 只能浏览，无法对话哦',
    ],
  },
  {
    icon: Settings,
    title: '个人中心',
    subtitle: '管理你的账号和 AI 女友的记忆',
    color: '#E8808A',
    items: [
      '修改昵称、头像和密码',
      '查看和管理 AI 对你的记忆（她会记住你说过的重要事情）',
      '可以手动编辑或删除记忆条目',
      '点击「记忆整合」可以让 AI 把零散记忆提炼成更精炼的长期记忆',
    ],
  },
  {
    icon: UserCircle,
    title: '角色编辑',
    subtitle: '随时调整她的性格和设定',
    color: '#C4A1FF',
    items: [
      '进入聊天界面后，点击角色头像可以进入编辑页面',
      '可以修改角色的外貌、背景经历、性格特点、说话风格、兴趣爱好等',
      '也可以上传文档（txt/pdf）作为角色的知识背景',
      '改完后她会立即用新的设定和你对话',
    ],
  },
]

function next() {
  if (currentStep.value < steps.length - 1) {
    currentStep.value++
  } else {
    localStorage.setItem('guide_read', '1')
    emit('close')
  }
}

function skip() {
  localStorage.setItem('guide_read', '1')
  emit('close')
}
</script>

<template>
  <Teleport to="body">
    <transition name="guide-fade">
      <div class="guide-overlay">
        <div class="guide-modal">
          <!-- 进度指示器 -->
          <div class="guide-progress">
            <div
              v-for="(s, i) in steps"
              :key="i"
              class="guide-dot"
              :class="{ active: i <= currentStep, done: i < currentStep }"
              :style="i <= currentStep ? { background: s.color } : {}"
            />
          </div>

          <!-- 跳过按钮 -->
          <button class="guide-skip" @click="skip">跳过</button>

          <!-- 图标 -->
          <div class="guide-icon-wrap" :style="{ background: steps[currentStep].color }">
            <component :is="steps[currentStep].icon" :size="36" color="#fff" />
          </div>

          <!-- 内容 -->
          <div class="guide-body">
            <h2 class="guide-title">{{ steps[currentStep].title }}</h2>
            <p class="guide-subtitle">{{ steps[currentStep].subtitle }}</p>

            <ul class="guide-list">
              <li v-for="item in steps[currentStep].items" :key="item" class="guide-item">
                {{ item }}
              </li>
            </ul>
          </div>

          <!-- 底部按钮 -->
          <div class="guide-footer">
            <button class="guide-btn" :style="{ background: steps[currentStep].color }" @click="next">
              {{ currentStep < steps.length - 1 ? '下一步' : '开始使用' }}
            </button>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<style scoped>
.guide-overlay {
  position: fixed;
  inset: 0;
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(74, 37, 53, 0.4);
  backdrop-filter: blur(4px);
}

.guide-modal {
  background: #fff;
  border-radius: 28px;
  box-shadow: 0 8px 48px rgba(255, 125, 175, 0.18);
  width: 420px;
  max-width: 92vw;
  padding: 36px 32px 28px;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
}

/* 进度点 */
.guide-progress {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 28px;
}
.guide-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #F5D0DA;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.guide-dot.active {
  transform: scale(1.3);
}
.guide-dot.done {
  transform: scale(0.8);
  opacity: 0.5;
}

/* 跳过 */
.guide-skip {
  position: absolute;
  top: 14px;
  right: 16px;
  font-size: 13px;
  color: #C495A8;
  background: none;
  border: none;
  cursor: pointer;
  font-family: inherit;
  transition: color 0.2s;
}
.guide-skip:hover {
  color: #4A2535;
}

/* 图标 */
.guide-icon-wrap {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24px;
  transition: background 0.3s;
}

/* 正文 */
.guide-body {
  text-align: center;
  width: 100%;
}
.guide-title {
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 20px;
  font-weight: 700;
  color: #4A2535;
  margin-bottom: 6px;
}
.guide-subtitle {
  font-size: 13px;
  color: #C495A8;
  margin-bottom: 20px;
  line-height: 1.6;
}

.guide-list {
  list-style: none;
  padding: 0;
  margin: 0;
  text-align: left;
}
.guide-item {
  position: relative;
  padding: 8px 0 8px 20px;
  font-size: 14px;
  color: #4A2535;
  line-height: 1.7;
}
.guide-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 14px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #FFB8D4;
}

/* 按钮 */
.guide-footer {
  margin-top: 24px;
}
.guide-btn {
  padding: 12px 48px;
  border: none;
  border-radius: 9999px;
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.guide-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
}
.guide-btn:active {
  transform: scale(0.97);
}

/* 动画 */
.guide-fade-enter-active,
.guide-fade-leave-active {
  transition: opacity 0.25s ease;
}
.guide-fade-enter-from,
.guide-fade-leave-to {
  opacity: 0;
}

@media (max-width: 480px) {
  .guide-modal {
    padding: 24px 18px 20px;
    border-radius: 24px;
  }
  .guide-icon-wrap {
    width: 64px;
    height: 64px;
    margin-bottom: 16px;
  }
  .guide-title {
    font-size: 17px;
  }
  .guide-item {
    font-size: 13px;
    padding: 6px 0 6px 18px;
  }
  .guide-item::before {
    top: 12px;
  }
  .guide-btn {
    padding: 10px 36px;
    font-size: 14px;
  }
}
</style>
