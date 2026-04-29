export interface User {
  id: string
  email: string
  username: string
  avatar_url: string | null
  membership_tier: 'free' | 'premium' | 'vip'
  membership_expires_at: string | null
  is_admin: boolean
  created_at: string
}

export interface Character {
  id: string
  name: string
  description: string | null
  system_prompt: string
  avatar_url: string | null
  is_template: boolean
  is_public: boolean
  tags: string | null
  created_at: string
  updated_at: string
}

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  content_type: 'text' | 'image' | 'voice'
  metadata: Record<string, any> | null
  emotion_label: string | null
  created_at: string
}

export interface Conversation {
  id: string
  character_id: string
  title: string | null
  message_count: number
  created_at: string
  updated_at: string
}

export interface Memory {
  id: string
  character_id: string
  content: string
  importance: number
  created_at: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
}
