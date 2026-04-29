import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/utils/http'
import type { Character, Conversation, Message } from '@/types/models'

export const useChatStore = defineStore('chat', () => {
  const characters = ref<Character[]>([])
  const currentCharacter = ref<Character | null>(null)
  const conversations = ref<Conversation[]>([])
  const currentConversation = ref<Conversation | null>(null)
  const messages = ref<Message[]>([])
  const isStreaming = ref(false)
  const streamingContent = ref('')
  const ws = ref<WebSocket | null>(null)

  async function loadCharacters() {
    const res = await api.get<Character[]>('/characters')
    characters.value = res.data
    if (!currentCharacter.value && res.data.length > 0) {
      await selectCharacter(res.data[0])
    }
  }

  async function selectCharacter(char: Character) {
    currentCharacter.value = char
    // 获取或创建会话
    const res = await api.post('/conversations', null, {
      params: { character_id: char.id },
    })
    currentConversation.value = res.data
    await loadMessages()
  }

  async function loadMessages() {
    if (!currentConversation.value) return
    const res = await api.get<Message[]>(
      `/conversations/${currentConversation.value.id}/messages`
    )
    messages.value = res.data
  }

  function connectWebSocket() {
    if (!currentConversation.value) return
    const token = localStorage.getItem('access_token')
    const convId = currentConversation.value.id

    const socket = new WebSocket(`ws://localhost:8000/ws/chat/${convId}`)
    ws.value = socket

    socket.onopen = () => {
      socket.send(JSON.stringify({ type: 'auth', token }))
    }

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'chunk') {
        streamingContent.value += data.content
      } else if (data.type === 'done') {
        messages.value.push({
          id: crypto.randomUUID(),
          role: 'assistant',
          content: data.full_reply,
          content_type: 'text',
          metadata: null,
          emotion_label: null,
          created_at: new Date().toISOString(),
        })
        streamingContent.value = ''
        isStreaming.value = false
      } else if (data.type === 'error') {
        isStreaming.value = false
        console.error(data.message)
      }
    }

    socket.onclose = () => {
      ws.value = null
    }
  }

  function sendMessage(text: string, image?: string | null) {
    if (!ws.value || ws.value.readyState !== WebSocket.OPEN) {
      connectWebSocket()
      // Wait briefly for connection, then send
      setTimeout(() => {
        if (ws.value?.readyState === WebSocket.OPEN) {
          _send(text, image)
        }
      }, 500)
      return
    }
    _send(text, image)
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
    ws.value?.send(JSON.stringify({ type: 'chat', message: text, image }))
  }

  return {
    characters, currentCharacter, conversations, currentConversation,
    messages, isStreaming, streamingContent,
    loadCharacters, selectCharacter, loadMessages, sendMessage, connectWebSocket,
  }
})
