# 虚拟女友 — 设计规范 (柚子社画风)

## 审美方向
**Soft Claymorphism × Sakura Motif · 柚子社风**
- 柚子社 (Yuzusoft) 是知名日系美少女游戏品牌
- 画风特征：柔和的色彩、细腻的光影、温暖治愈的氛围
- UI 映射：粉嫩色系、高圆角、柔和阴影、樱花点缀

## 色彩系统

| Token | Hex | 用途 |
|--------|-----|------|
| --color-primary | #FF7DAF | 主色 · 樱花粉 |
| --color-primary-light | #FFB8D4 | 浅樱 |
| --color-accent | #C4A1FF | 强调 · 淡薰衣草 |
| --color-gold | #FFD4A8 | 点缀 · 暖金 |
| --color-bg | #FFF5F8 | 背景 · 暖粉白 |
| --color-sakura | #FFE8F0 | 樱花底色 |
| --color-text | #4A2535 | 正文 · 暖棕 |
| --color-text-muted | #C495A8 | 辅助文字 |

## 字体

| 用途 | 字体 | 备选 |
|------|------|------|
| 标题 | Varela Round | ZCOOL QingKe HuangYou |
| 正文 | Nunito Sans | Noto Sans SC |
| 特殊 | ZCOOL QingKe HuangYou | 品牌用字 |

## 圆角系统
- xs: 8px | sm: 14px | base: 20px | lg: 28px | xl: 36px | full: 9999px
- 头像用 14px（丸角矩形）
- 气泡用 20px（一侧 8px 小角）

## 阴影
- 所有阴影带粉色 tint (`rgba(255,125,175,...)`)
- Glow 效果用于 Logo 和重要按钮
- 气泡轻阴影，卡片中阴影

## 动画
- Easing: cubic-bezier(0.25, 0.8, 0.25, 1.2) — 轻微弹性
- Bounce: cubic-bezier(0.34, 1.56, 0.64, 1) — 按钮 hover
- 消息入场：上滑 + 淡入 + 微缩放 (0.35s)
- 登录页：樱花飘落动画
- 打字指示器：三点弹跳，三色（粉/紫/金）

## 图标
- SVG 图标 (Lucide set)，24x24 viewBox，stroke-width 1.5-2
- 无 emoji 作为 UI 图标
- 装饰性 emoji（🌸💕）仅用于氛围

## 反模式 · 禁止
- 紫蓝渐变
- 毛玻璃效果
- 纯黑纯白
- Inter 字体
- 尖锐直角
