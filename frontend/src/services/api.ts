import axios from 'axios'
import type { DialogueItem } from '@/types'

const runtimeBaseUrl = (import.meta.env.VITE_TTS_API_BASE_URL || '').trim().replace(/\/$/, '')
const apiBaseUrl = runtimeBaseUrl ? `${runtimeBaseUrl}/api/tts` : '/api/tts'
const runtimeApiKey = (import.meta.env.VITE_TTS_API_KEY || '').trim()

const defaultHeaders: Record<string, string> = {
  'Content-Type': 'application/json',
}

if (runtimeApiKey) {
  defaultHeaders.Authorization = `Bearer ${runtimeApiKey}`
}

const api = axios.create({
  baseURL: apiBaseUrl,
  timeout: 120000,
  headers: {
    ...defaultHeaders,
  },
})

// ============================================================================
//                              会话管理
// ============================================================================

export async function createSession() {
  const response = await api.post('/sessions')
  return response.data
}

export async function listSessions(limit = 50, status?: string) {
  const params = new URLSearchParams()
  params.append('limit', String(limit))
  if (status) params.append('status', status)
  
  const response = await api.get(`/sessions?${params}`)
  return response.data
}

export async function getSession(sessionId: string) {
  const response = await api.get(`/sessions/${sessionId}`)
  return response.data
}

export async function deleteSession(sessionId: string) {
  const response = await api.delete(`/sessions/${sessionId}`)
  return response.data
}

// ============================================================================
//                              阶段一：对话分析
// ============================================================================

export async function analyzeDialogue(sessionId: string, userInput: string) {
  const response = await api.post(`/sessions/${sessionId}/analyze`, {
    user_input: userInput,
  })
  return response.data
}

export function analyzeDialogueStream(
  sessionId: string,
  userInput: string,
  onChunk: (chunk: string) => void,
  onResult: (result: unknown) => void,
  onError: (error: Error) => void
) {
  // SSE 需要 POST，这里用 fetch
  const controller = new AbortController()
  const url = `${apiBaseUrl}/sessions/${sessionId}/analyze/stream`

  fetch(url, {
    method: 'POST',
    headers: defaultHeaders,
    body: JSON.stringify({ user_input: userInput }),
    signal: controller.signal,
  }).then(async (response) => {
    if (!response.ok) {
      onError(new Error(`Stream request failed: ${response.status}`))
      return
    }
    const reader = response.body?.getReader()
    const decoder = new TextDecoder()
    
    if (!reader) {
      onError(new Error('No reader available'))
      return
    }
    
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      buffer += decoder.decode(value, { stream: true })
      let newlineIndex = buffer.indexOf('\n')
      while (newlineIndex >= 0) {
        const rawLine = buffer.slice(0, newlineIndex)
        buffer = buffer.slice(newlineIndex + 1)
        const line = rawLine.trim()
        if (line.startsWith('data:')) {
          const payload = line.slice(5).trimStart()
          if (payload) {
            try {
              const data = JSON.parse(payload)
              if (data.type === 'chunk') {
                onChunk(data.content)
              } else if (data.type === 'result') {
                onResult(data.data)
              }
            } catch {
              void 0
            }
          }
        }
        newlineIndex = buffer.indexOf('\n')
      }
    }
  }).catch(onError)
  
  return () => controller.abort()
}

export async function refineDialogue(
  sessionId: string,
  instruction: string,
  targetIndices?: number[]
) {
  const response = await api.post(`/sessions/${sessionId}/refine`, {
    instruction,
    target_indices: targetIndices,
  })
  return response.data
}

export async function updateDialogues(
  sessionId: string,
  dialogueList: DialogueItem[]
) {
  const response = await api.put(`/sessions/${sessionId}/dialogues`, {
    dialogue_list: dialogueList,
  })
  return response.data
}

export async function confirmStage1(sessionId: string) {
  const response = await api.post(`/sessions/${sessionId}/confirm-stage1`)
  return response.data
}

// ============================================================================
//                              阶段二：音色匹配
// ============================================================================

export async function matchVoices(sessionId: string) {
  const response = await api.post(`/sessions/${sessionId}/match`)
  return response.data
}

export function matchVoicesStream(
  sessionId: string,
  onChunk: (chunk: string) => void,
  onResult: (result: unknown) => void,
  onError: (error: Error) => void
) {
  const controller = new AbortController()
  const url = `${apiBaseUrl}/sessions/${sessionId}/match/stream`

  fetch(url, {
    method: 'POST',
    headers: defaultHeaders,
    signal: controller.signal,
  })
    .then(async (response) => {
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        onError(new Error('No reader available'))
        return
      }

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const text = decoder.decode(value)
        const lines = text.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.type === 'chunk') {
                onChunk(data.content)
              } else if (data.type === 'result') {
                onResult(data.data)
              }
            } catch (err) {
              void err
            }
          }
        }
      }
    })
    .catch(onError)

  return () => controller.abort()
}

export async function rematchVoices(
  sessionId: string,
  instruction: string,
  targetCharacters?: string[]
) {
  const response = await api.post(`/sessions/${sessionId}/rematch`, {
    instruction,
    target_characters: targetCharacters,
  })
  return response.data
}

export async function changeVoice(
  sessionId: string,
  character: string,
  voiceId: string,
  voiceName?: string
) {
  const response = await api.post(`/sessions/${sessionId}/change-voice`, {
    character,
    voice_id: voiceId,
    voice_name: voiceName || '',
  })
  return response.data
}

export async function confirmStage2(sessionId: string) {
  const response = await api.post(`/sessions/${sessionId}/confirm-stage2`)
  return response.data
}

// ============================================================================
//                              阶段三：批量合成
// ============================================================================

export async function synthesizeAudio(sessionId: string) {
  const response = await api.post(`/sessions/${sessionId}/synthesize`)
  return response.data
}

// ============================================================================
//                              音色管理
// ============================================================================

export async function listVoices(category?: string, gender?: string, limit = 50) {
  const params = new URLSearchParams()
  params.append('limit', String(limit))
  if (category) params.append('category', category)
  if (gender) params.append('gender', gender)
  
  const response = await api.get(`/voices?${params}`)
  return response.data
}

export async function getVoiceDetail(voiceId: string) {
  const response = await api.get(`/voices/${voiceId}`)
  return response.data
}

export async function getVoiceCategories() {
  const response = await api.get('/voice-categories')
  return response.data
}

export async function previewVoice(voiceId: string, text?: string) {
  const response = await api.post('/preview', {
    voice_id: voiceId,
    text: text || '你好，这是一段试听文本。',
  }, {
    responseType: 'blob',
  })
  return response.data
}

// ============================================================================
//                              音频下载
// ============================================================================

export function getAudioUrl(sessionId: string, filename: string) {
  return `${apiBaseUrl}/audio/${sessionId}/${filename}`
}

export function getMergedAudioUrl(sessionId: string) {
  return `${apiBaseUrl}/sessions/${sessionId}/merged-audio`
}

export default api
