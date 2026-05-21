<script setup lang="ts">
import { ref } from 'vue'
import { Heart, MessageCircle, UserCircle, Sparkles, Settings, Key } from 'lucide-vue-next'

const emit = defineEmits<{ close: [] }>()

const currentStep = ref(0)

const steps = [
  {
    icon: Heart,
    title: '欢迎来到恋爱对话模拟器',
    subtitle: '一个能陪你聊天、记住你说过的话、有自己小情绪的 AI 女友',
    color: '#FF7DAF',
    items: [
      '你可以创建属于自己的 AI 角色，她会记住你们的每一次对话，也会根据聊天内容产生情绪变化',
      '懒得创建？首页已经准备了 3 个默认角色，点进去就能直接聊天',
      '在开始之前，有一件小事需要你去做——给 AI 配一把"钥匙"（API Key），不花钱或者几乎不花钱',
      '别担心，跟着下面的步骤走，5 分钟就能搞定 ~',
    ],
  },
  {
    icon: Key,
    title: '第一步：获取 API Key（AI 的钥匙）',
    subtitle: '就像手机需要话费才能打电话，AI 也需要"买点汽油"才能运转',
    color: '#FFD4A8',
    items: [
      '打开 platform.deepseek.com（注意不是 deepseek.com，或者从官网首页点「API开放平台」进入）',
      '用手机号注册登录后，页面左侧会看到一排菜单——点击「API Keys」',
      '点「创建新的 API Key」，随便起个名字，点创建——立刻复制那一长串 sk-xxxxx 开头的英文数字！关掉弹窗就再也看不到了',
      '复制好后，左侧菜单点「充值」，微信/支付宝充 10 块钱就行（够聊好几个月了，也就一杯奶茶钱）',
    ],
  },
  {
    icon: Settings,
    title: '第二步：把 Key 填进网站',
    subtitle: '刚刚复制的那串 sk-xxxxx 就要用在这里了',
    color: '#E8808A',
    items: [
      '点击右上角头像 → 进入「个人中心」→ 找到「API 配置」区域',
      'API Key：粘贴你刚才从 DeepSeek 复制的那串 sk-xxxxx',
      '接口地址：填 https://api.deepseek.com/v1（照抄就行，别改）',
      '模型名称：填 deepseek-v4-pro（也是照抄，别改）',
      '点「测试连接」，看到绿色 ✓ 就说明成功了，点保存即可',
    ],
  },
  {
    icon: Sparkles,
    title: '第三步：创建你的角色',
    subtitle: '配好 Key 之后，AI 就能帮你生成角色了',
    color: '#C4A1FF',
    items: [
      '描述生成：用大白话描述你想要的女生（比如"20岁大学生，温柔可爱，喜欢做饭看动漫"），AI 自动帮你生成完整的性格、外貌、说话风格——需要配好 API Key 才能用',
      '如果还没配 Key，也可以点「跳过，手写设定」，自己动手填，一样能创建角色，只是不能 AI 对话',
      '聊天记录导入：把你和某人的聊天记录粘贴进去，AI 会从中"蒸馏"出她的说话风格（也需要 API Key）',
      '创建时可以上传头像，也能后续慢慢改',
    ],
  },
  {
    icon: MessageCircle,
    title: '第四步：开始聊天',
    subtitle: '就像平时发微信一样，她随时在线',
    color: '#FF7DAF',
    items: [
      '点击角色卡片进入聊天界面，可以发文字、表情和图片',
      '电脑端：按 Enter 发送，Shift + Enter 换行',
      '手机端：点输入框右下角的发送按钮（换行键就是换行）',
      '消息可以撤回，AI 的回复不满意也可以点重试让她重新说',
    ],
  },
  {
    icon: UserCircle,
    title: '其他功能',
    subtitle: '慢慢探索，不着急',
    color: '#C4A1FF',
    items: [
      '角色编辑：聊天界面点角色头像进入，随时调整她的外貌、性格、说话风格',
      '记忆管理：个人中心里可以看到她记住了你哪些事，可以删改',
      '更换头像：个人中心可以改你的头像，角色编辑里可以改她的头像',
      '创建多个角色：首页点「+」可以创建新角色，每个角色有独立对话和记忆',
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
