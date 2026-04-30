import { defineStore } from 'pinia'
import { ref } from 'vue'
import api, { uploadApi } from '@/utils/http'
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
    const res = await api.post('/conversations', null, {
      params: { character_id: char.id },
    })
    currentConversation.value = res.data
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
      { user_description: description }
    )
    return res.data.personality_profile
  }

  async function uploadCharacterDocuments(characterId: string, files: File[]) {
    for (const file of files) {
      const form = new FormData()
      form.append('file', file)
      await uploadApi.post(`/characters/${characterId}/documents`, form)
    }
  }

  async function loadMessages() {
    if (!currentConversation.value) return
    const res = await api.get<Message[]>(
      `/conversations/${currentConversation.value.id}/messages`
    )
    messages.value = res.data
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

  // ── WebSocket ──

  function connectWebSocket() {
    if (ws.value) {
      wsIntentionalClose.value = true
      ws.value.close()
      ws.value = null
      wsIntentionalClose.value = false
    }

    if (!currentConversation.value) return
    const token = localStorage.getItem('access_token')
    if (!token) return

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
        streamingComplete.value = true
        messages.value.push({
          id: crypto.randomUUID(),
          role: 'assistant',
          content: data.full_reply,
          content_type: 'text',
          metadata: null,
          emotion_label: null,
          created_at: new Date().toISOString(),
        })
        if (data.emotion_state) {
          emotionState.value = data.emotion_state
        }
        // 过渡动画后清除流式内容
        setTimeout(() => {
          streamingContent.value = ''
          streamingComplete.value = false
        }, 300)
        isStreaming.value = false
      } else if (data.type === 'error') {
        isStreaming.value = false
        streamingContent.value = ''
        streamingComplete.value = false
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
    }
  }

  function sendMessage(text: string, image?: string | null) {
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
    uploadCharacterDocuments,
    loadMessages, sendMessage, connectWebSocket,
    loadMemories, updateMemory, deleteMemory,
  }
})
