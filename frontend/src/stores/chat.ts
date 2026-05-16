import { defineStore } from 'pinia'
import { ref } from 'vue'
import api, { uploadApi } from '@/utils/http'
import { useAuthStore } from '@/stores/auth'
import type { Character, Conversation, Message, Memory } from '@/types/models'

export const useChatStore = defineStore('chat', () => {
  const characters = ref<Character[]>([])
  const currentCharacter = ref<Character | null>(null)
  const conversations = ref<Conversation[]>([])
  const currentConversation = ref<Conversation | null>(null)
  const messages = ref<Message[]>([])
  const isStreaming = ref(false)
  const streamingContent = ref('')
  const streamingComplete = ref(false) // 用于过渡动画
  const ws = ref<WebSocket | null>(null)
  const wsReconnectAttempts = ref(0)
  const wsIntentionalClose = ref(false)
  const emotionState = ref<{ primary: string; intensity: number; valence: number } | null>(null)

  // 记忆
  const memories = ref<Memory[]>([])

  async function loadCharacters() {
    const res = await api.get<Character[]>('/characters')
    characters.value = res.data
  }

  async function selectCharacter(characterId: string) {
    let char = characters.value.find(c => c.id === characterId)
    if (!char) {
      // 角色不在 store 中（如直接刷新页面），从 API 加载
      try {
        const res = await api.get<Character>(`/characters/${characterId}`)
        char = res.data
        if (!characters.value.find(c => c.id === char!.id)) {
          characters.value.push(char)
        }
      } catch {
        throw new Error('角色不存在')
      }
    }
    if (!char) throw new Error('角色不存在')
    currentCharacter.value = char
    // 重置流式状态，防止上次未完成就退出导致加载条卡死
    isStreaming.value = false
    streamingContent.value = ''
    streamingComplete.value = false
    emotionState.value = null

    // 加载该角色所有会话作为短期记忆
    const convRes = await api.get<Conversation[]>('/conversations', {
      params: { character_id: char.id },
    })
    if (convRes.data.length > 0) {
      conversations.value = convRes.data
      currentConversation.value = convRes.data[0]
    } else {
      const res = await api.post('/conversations', null, {
        params: { character_id: char.id },
      })
      conversations.value = [res.data]
      currentConversation.value = res.data
    }
    messages.value = []
    wsIntentionalClose.value = true
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
    wsIntentionalClose.value = false
    await loadMessages()
    await loadMemories(characterId)
    connectWebSocket()

    // 检测中断：最后一条是用户发的但没收到 AI 回复 → 自动重发
    const msgs = messages.value
    if (msgs.length > 0 && msgs[msgs.length - 1].role === 'user') {
      const last = msgs.pop()!
      // 延迟一小段等 WebSocket 连上
      setTimeout(() => {
        sendMessage(last.content, last.metadata?.image_base64)
      }, 600)
    }
  }

  async function createCharacter(data: {
    name: string
    description: string
    system_prompt?: string
    personality_profile?: Record<string, any> | null
  }) {
    const res = await api.post<Character>('/characters', data)
    characters.value.push(res.data)
    return res.data
  }

  async function generateCharacterProfile(description: string): Promise<Record<string, any>> {
    const res = await api.post<{ personality_profile: Record<string, any> }>(
      '/characters/generate',
      { user_description: description },
      { timeout: 120000 },
    )
    return res.data.personality_profile
  }

  async function analyzeChatLogs(chatText: string, currentProfile?: Record<string, any> | null) {
    const res = await api.post<{
      enhanced_profile: Record<string, any>
    }>('/characters/analyze-chat', {
      chat_text: chatText,
      current_profile: currentProfile || null,
    }, { timeout: 120000 })
    return res.data
  }

  async function uploadCharacterDocuments(characterId: string, files: File[]) {
    for (const file of files) {
      const form = new FormData()
      form.append('file', file)
      await uploadApi.post(`/characters/${characterId}/documents`, form)
    }
  }

  async function updateCharacter(id: string, data: { name?: string; description?: string; system_prompt?: string; personality_profile?: Record<string, any> | null }) {
    const res = await api.patch<Character>(`/characters/${id}`, data)
    const idx = characters.value.findIndex(c => c.id === id)
    if (idx >= 0) characters.value[idx] = res.data
    if (currentCharacter.value?.id === id) currentCharacter.value = res.data
    return res.data
  }

  async function deleteCharacter(id: string) {
    await api.delete(`/characters/${id}`)
    characters.value = characters.value.filter(c => c.id !== id)
  }

  async function uploadAvatar(characterId: string, file: File) {
    const form = new FormData()
    form.append('file', file)
    const res = await uploadApi.post<Character>(`/characters/${characterId}/avatar`, form)
    // 更新列表和当前角色中的头像
    const idx = characters.value.findIndex(c => c.id === characterId)
    if (idx >= 0) characters.value[idx] = res.data
    if (currentCharacter.value?.id === characterId) currentCharacter.value = res.data
    return res.data
  }

  async function loadMessages() {
    if (conversations.value.length === 0) return
    const results = await Promise.all(
      conversations.value.map(conv =>
        api.get<Message[]>(`/conversations/${conv.id}/messages`)
      )
    )
    const allMessages = results.flatMap(r => r.data)
    allMessages.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
    messages.value = allMessages
  }

  // ── 记忆 ──

  async function loadMemories(characterId?: string) {
    const cid = characterId || currentCharacter.value?.id
    if (!cid) return
    try {
      const res = await api.get<Memory[]>('/memories', { params: { character_id: cid } })
      memories.value = res.data
    } catch { /* ignore */ }
  }

  async function updateMemory(id: string, data: { content?: string; importance?: number }) {
    await api.patch(`/memories/${id}`, data)
    const idx = memories.value.findIndex(m => m.id === id)
    if (idx >= 0) {
      if (data.content !== undefined) memories.value[idx].content = data.content
      if (data.importance !== undefined) memories.value[idx].importance = data.importance
    }
  }

  async function deleteMemory(id: string) {
    await api.delete(`/memories/${id}`)
    memories.value = memories.value.filter(m => m.id !== id)
  }

  const consolidating = ref(false)
  async function consolidateMemories(characterId?: string | null) {
    const cid = characterId || currentCharacter.value?.id
    if (!cid) return
    consolidating.value = true
    try {
      const res = await api.post('/memories/consolidate', null, { params: { character_id: cid } })
      if (res.data.consolidated) {
        await loadMemories(cid)
      }
      return res.data
    } finally {
      consolidating.value = false
    }
  }

  // ── WebSocket ──

  function connectWebSocket() {
    if (ws.value) {
      wsIntentionalClose.value = true
      ws.value.close()
      ws.value = null
      wsIntentionalClose.value = false
    }

    if (!currentConversation.value) return
    const token = localStorage.getItem('access_token') || 'guest'

    const convId = currentConversation.value.id
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const socket = new WebSocket(`${protocol}//${window.location.host}/ws/chat/${convId}`)
    ws.value = socket

    socket.onopen = () => {
      wsReconnectAttempts.value = 0
      socket.send(JSON.stringify({ type: 'auth', token }))
    }

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'chunk') {
        if (!isStreaming.value) isStreaming.value = true
        streamingContent.value += data.content
      } else if (data.type === 'done') {
        console.log('[WS] done:', { hasImage: !!data.image_url, hasText: !!(data.full_reply && data.full_reply?.trim()), full_reply_len: (data.full_reply || '').length })
        streamingComplete.value = true
        const hasImage = !!data.image_url
        const hasText = data.full_reply && data.full_reply.trim()
        if (hasText || hasImage) {
          messages.value.push({
            id: crypto.randomUUID(),
            role: 'assistant',
            content: data.full_reply || '',
            content_type: hasImage ? 'image' : 'text',
            metadata: hasImage ? { image_url: data.image_url, prompt: data.image_prompt } : null,
            emotion_label: null,
            created_at: new Date().toISOString(),
          })
        }
        if (data.emotion_state) {
          emotionState.value = data.emotion_state
        }
        // 过渡动画后清除流式内容
        setTimeout(() => {
          streamingContent.value = ''
          streamingComplete.value = false
        }, 300)
        isStreaming.value = false
      } else if (data.type === 'image') {
        console.log('[WS] image event:', { url: (data.url || '').slice(0, 50), prompt: data.prompt })
        // 兼容旧版单独的图片事件
        messages.value.push({
          id: crypto.randomUUID(),
          role: 'assistant',
          content: data.prompt || '',
          content_type: 'image',
          metadata: { image_url: data.url, prompt: data.prompt },
          emotion_label: null,
          created_at: new Date().toISOString(),
        })
        // 收到图片后清除流式状态
        isStreaming.value = false
        streamingContent.value = ''
        streamingComplete.value = false
      } else if (data.type === 'ai_error') {
        isStreaming.value = false
        streamingContent.value = ''
        streamingComplete.value = false
        const errorMessages: Record<string, string> = {
          invalid_key: 'API Key 无效，请前往个人中心重新设置',
          insufficient_balance: 'API 余额不足，请充值或更换 Key',
          server_error: 'AI 服务暂时异常，请稍后重试',
          unknown: 'AI 调用失败，请稍后重试',
        }
        const msg = errorMessages[data.code] || data.message || 'AI 调用失败'
        messages.value.push({
          id: crypto.randomUUID(),
          role: 'assistant',
          content: msg,
          content_type: 'text',
          metadata: { error_code: data.code },
          emotion_label: null,
          created_at: new Date().toISOString(),
        })
      } else if (data.type === 'error') {
        isStreaming.value = false
        streamingContent.value = ''
        streamingComplete.value = false
        messages.value.push({
          id: crypto.randomUUID(),
          role: 'assistant',
          content: '呜…刚才好像出了点问题 (′；ω；`) 能再说一遍吗？',
          content_type: 'text',
          metadata: null,
          emotion_label: null,
          created_at: new Date().toISOString(),
        })
        console.error(data.message)
      }
    }

    socket.onclose = () => {
      ws.value = null
      if (!wsIntentionalClose.value && wsReconnectAttempts.value < 5) {
        const delay = Math.min(1000 * Math.pow(2, wsReconnectAttempts.value), 10000)
        wsReconnectAttempts.value++
        setTimeout(() => connectWebSocket(), delay)
      }
    }

    socket.onerror = () => {
      ws.value = null
      isStreaming.value = false
      streamingContent.value = ''
      streamingComplete.value = false
    }
  }

  function disconnectWebSocket() {
    wsIntentionalClose.value = true
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
    isStreaming.value = false
    streamingContent.value = ''
    streamingComplete.value = false
  }

  function sendMessage(text: string, image?: string | null) {
    const auth = useAuthStore()
    if (!auth.hasApiKey) {
      auth.promptApiKey()
      return
    }
    // 先将用户消息立即显示在 UI
    messages.value.push({
      id: crypto.randomUUID(),
      role: 'user',
      content: text || '[图片]',
      content_type: image ? 'image' : 'text',
      metadata: image ? { image_base64: image } : null,
      emotion_label: null,
      created_at: new Date().toISOString(),
    })
    isStreaming.value = true
    streamingContent.value = ''
    streamingComplete.value = false

    // 确保 WebSocket 已连接
    if (!ws.value || ws.value.readyState !== WebSocket.OPEN) {
      if (!currentConversation.value) {
        isStreaming.value = false
        console.error('没有活跃的对话')
        return
      }
      connectWebSocket()
      // 等待连接建立后发送
      const checkAndSend = () => {
        if (ws.value?.readyState === WebSocket.OPEN) {
          ws.value.send(JSON.stringify({ type: 'chat', message: text, image }))
        } else if (wsReconnectAttempts.value < 5) {
          setTimeout(checkAndSend, 300)
        } else {
          isStreaming.value = false
          console.error('WebSocket 连接失败')
        }
      }
      setTimeout(checkAndSend, 500)
      return
    }
    ws.value.send(JSON.stringify({ type: 'chat', message: text, image }))
  }

  function _send(text: string, image?: string | null) {
    messages.value.push({
      id: crypto.randomUUID(),
      role: 'user',
      content: text || '[图片]',
      content_type: image ? 'image' : 'text',
      metadata: image ? { image_base64: image } : null,
      emotion_label: null,
      created_at: new Date().toISOString(),
    })
    isStreaming.value = true
    streamingContent.value = ''
    streamingComplete.value = false
    ws.value?.send(JSON.stringify({ type: 'chat', message: text, image }))
  }

  return {
    characters, currentCharacter, conversations, currentConversation,
    messages, isStreaming, streamingContent, streamingComplete, emotionState,
    memories,
    loadCharacters, selectCharacter, createCharacter, generateCharacterProfile,
    analyzeChatLogs, uploadCharacterDocuments,
    loadMessages, sendMessage, connectWebSocket, disconnectWebSocket, uploadAvatar,
    updateCharacter, deleteCharacter, loadMemories, updateMemory, deleteMemory,
    consolidating, consolidateMemories,
  }
})
