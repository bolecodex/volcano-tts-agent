import { useState, useCallback, useEffect, useRef } from 'react'
import type { TTSSession, DialogueItem, SessionStatus, SessionListItem } from '@/types'
import * as api from '@/services/api'

interface UseTTSSessionReturn {
  session: TTSSession | null
  loading: boolean
  error: string | null
  streamingText: string
  isStreaming: boolean
  
  // 会话管理
  createSession: () => Promise<string | undefined>
  loadSession: (sessionId: string) => Promise<void>
  deleteSession: (sessionId: string) => Promise<void>
  refreshSession: () => Promise<void>
  
  // 阶段一
  analyzeDialogue: (userInput: string) => Promise<void>
  refineDialogue: (instruction: string, targetIndices?: number[]) => Promise<void>
  updateDialogues: (dialogueList: DialogueItem[]) => Promise<void>
  confirmStage1: () => Promise<boolean>
  
  // 阶段二
  matchVoices: () => Promise<void>
  rematchVoices: (instruction: string, targetCharacters?: string[]) => Promise<void>
  changeVoice: (character: string, voiceId: string, voiceName?: string) => Promise<void>
  confirmStage2: () => Promise<void>
  
  // 阶段三
  synthesizeAudio: () => Promise<void>
  
  // 工具方法
  reset: () => void
}

// 会话列表 Hook
export interface UseTTSSessionListReturn {
  sessions: SessionListItem[]
  loading: boolean
  error: string | null
  refresh: () => Promise<void>
}

export function useTTSSession(initialSessionId?: string): UseTTSSessionReturn {
  const [session, setSession] = useState<TTSSession | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [streamingText, setStreamingText] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const cancelStreamRef = useRef<null | (() => void)>(null)
  
  const reset = useCallback(() => {
    cancelStreamRef.current?.()
    cancelStreamRef.current = null
    setSession(null)
    setLoading(false)
    setError(null)
    setStreamingText('')
    setIsStreaming(false)
  }, [])
  
  // 加载初始会话
  useEffect(() => {
    if (initialSessionId) {
      loadSessionInternal(initialSessionId)
    }
  }, [initialSessionId])
  
  const loadSessionInternal = async (sessionId: string) => {
    cancelStreamRef.current?.()
    cancelStreamRef.current = null
    setStreamingText('')
    setIsStreaming(false)
    setLoading(true)
    setError(null)
    try {
      const result = await api.getSession(sessionId)
      if (result.success) {
        setSession(result.data)
      } else {
        setError(result.error || '加载会话失败')
      }
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }
  
  const createSession = useCallback(async (): Promise<string | undefined> => {
    cancelStreamRef.current?.()
    cancelStreamRef.current = null
    setStreamingText('')
    setIsStreaming(false)
    setLoading(true)
    setError(null)
    try {
      const result = await api.createSession()
      if (result.success) {
        const newSession: TTSSession = {
          session_id: result.session_id,
          status: result.status as SessionStatus,
          dialogue_list: [],
          voice_mapping: [],
          audio_files: [],
        }
        setSession(newSession)
        return result.session_id
      } else {
        setError(result.error || '创建会话失败')
        return undefined
      }
    } catch (e) {
      setError((e as Error).message)
      return undefined
    } finally {
      setLoading(false)
    }
  }, [])
  
  const loadSession = useCallback(async (sessionId: string) => {
    await loadSessionInternal(sessionId)
  }, [])
  
  const refreshSession = useCallback(async () => {
    if (session?.session_id) {
      await loadSessionInternal(session.session_id)
    }
  }, [session?.session_id])
  
  const deleteSession = useCallback(async (sessionId: string) => {
    setLoading(true)
    setError(null)
    try {
      await api.deleteSession(sessionId)
      if (session?.session_id === sessionId) {
        reset()
      }
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }, [session, reset])
  
  const analyzeDialogue = useCallback(async (userInput: string) => {
    if (!session) return
    
    setLoading(true)
    setError(null)
    setStreamingText('')
    setIsStreaming(true)
    cancelStreamRef.current?.()
    cancelStreamRef.current = null
    setSession(prev => prev ? { ...prev, status: 'analyzing' as SessionStatus } : null)
    
    try {
      await new Promise<void>((resolve) => {
        const cancel = api.analyzeDialogueStream(
          session.session_id,
          userInput,
          (chunk) => setStreamingText((prev) => prev + chunk),
          (data) => {
            cancelStreamRef.current = null
            const result = data as Record<string, unknown>
            if (result?.success) {
              setSession(prev => prev ? {
                ...prev,
                status: (result.status as SessionStatus) || ('dialogue_ready' as SessionStatus),
                input_type: result.input_type as TTSSession['input_type'],
                dialogue_list: (result.dialogue_list as DialogueItem[]) || [],
              } : null)
            } else {
              setError((result?.error as string) || '分析失败')
            }
            resolve()
          },
          (err) => {
            cancelStreamRef.current = null
            if (err.name !== 'AbortError') {
              setError(err.message)
            }
            resolve()
          }
        )
        cancelStreamRef.current = cancel
      })
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
      setIsStreaming(false)
    }
  }, [session])
  
  const refineDialogue = useCallback(async (instruction: string, targetIndices?: number[]) => {
    if (!session) return
    
    setLoading(true)
    setError(null)
    
    try {
      const result = await api.refineDialogue(session.session_id, instruction, targetIndices)
      
      if (result.success) {
        setSession(prev => prev ? {
          ...prev,
          dialogue_list: result.dialogue_list || [],
        } : null)
      } else {
        setError(result.error || '修改失败')
      }
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }, [session])
  
  const updateDialogues = useCallback(async (dialogueList: DialogueItem[]) => {
    if (!session) return
    
    setLoading(true)
    setError(null)
    
    try {
      const result = await api.updateDialogues(session.session_id, dialogueList)
      
      if (result.success) {
        setSession(prev => prev ? {
          ...prev,
          dialogue_list: result.dialogue_list || dialogueList,
        } : null)
      } else {
        setError(result.error || '更新失败')
      }
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }, [session])
  
  const confirmStage1 = useCallback(async (): Promise<boolean> => {
    if (!session) return false
    
    setLoading(true)
    setError(null)
    
    try {
      const result = await api.confirmStage1(session.session_id)
      
      if (result.success) {
        setSession(prev => prev ? {
          ...prev,
          status: result.status as SessionStatus,
        } : null)
        return true
      } else {
        setError(result.error || '确认失败')
        return false
      }
    } catch (e) {
      setError((e as Error).message)
      return false
    } finally {
      setLoading(false)
    }
  }, [session])
  
  const matchVoices = useCallback(async () => {
    if (!session) return
    if (!session.dialogue_list?.length) {
      setError('对话列表为空，请先完成对话分析')
      return
    }
    if (session.status !== 'dialogue_ready') {
      setError('请先确认对话列表')
      return
    }
    
    setLoading(true)
    setError(null)
    setStreamingText('')
    setIsStreaming(true)
    cancelStreamRef.current?.()
    cancelStreamRef.current = null
    const prevStatus = session.status
    setSession(prev => prev ? { ...prev, status: 'matching' as SessionStatus } : null)
    
    try {
      await new Promise<void>((resolve) => {
        const cancel = api.matchVoicesStream(
          session.session_id,
          (chunk) => setStreamingText((prev) => prev + chunk),
          (data) => {
            cancelStreamRef.current = null
            const result = data as Record<string, unknown>
            if (result?.success) {
              setSession(prev => prev ? {
                ...prev,
                status: (result.status as SessionStatus) || ('voice_ready' as SessionStatus),
                voice_mapping: (result.voice_mapping as TTSSession['voice_mapping']) || [],
              } : null)
            } else {
              setError((result?.error as string) || '匹配失败')
              setSession(prev => prev ? { ...prev, status: prevStatus as SessionStatus } : null)
            }
            resolve()
          },
          (err) => {
            cancelStreamRef.current = null
            if (err.name !== 'AbortError') {
              setError(err.message)
              setSession(prev => prev ? { ...prev, status: prevStatus as SessionStatus } : null)
            }
            resolve()
          }
        )
        cancelStreamRef.current = cancel
      })
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
      setIsStreaming(false)
    }
  }, [session])
  
  const rematchVoices = useCallback(async (instruction: string, targetCharacters?: string[]) => {
    if (!session) return
    
    setLoading(true)
    setError(null)
    
    try {
      const result = await api.rematchVoices(session.session_id, instruction, targetCharacters)
      
      if (result.success) {
        setSession(prev => prev ? {
          ...prev,
          voice_mapping: result.voice_mapping || [],
          status: 'voice_ready' as SessionStatus,
          audio_files: [],
          merged_audio: undefined,
        } : null)
      } else {
        setError(result.error || '重新匹配失败')
      }
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }, [session])
  
  const changeVoice = useCallback(async (character: string, voiceId: string, voiceName?: string) => {
    if (!session) return
    
    setLoading(true)
    setError(null)
    
    try {
      const result = await api.changeVoice(session.session_id, character, voiceId, voiceName)
      
      if (result.success) {
        setSession(prev => prev ? {
          ...prev,
          voice_mapping: result.voice_mapping || [],
          status: 'voice_ready' as SessionStatus,
          audio_files: [],
          merged_audio: undefined,
        } : null)
      } else {
        setError(result.error || '更换音色失败')
      }
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }, [session])
  
  const confirmStage2 = useCallback(async () => {
    if (!session) return
    
    setLoading(true)
    setError(null)
    
    try {
      const result = await api.confirmStage2(session.session_id)
      
      if (result.success) {
        setSession(prev => prev ? {
          ...prev,
          status: result.status as SessionStatus,
        } : null)
      } else {
        setError(result.error || '确认失败')
      }
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }, [session])
  
  const synthesizeAudio = useCallback(async () => {
    if (!session) return
    
    setLoading(true)
    setError(null)
    
    try {
      const result = await api.synthesizeAudio(session.session_id)
      
      if (result.success) {
        setSession(prev => prev ? {
          ...prev,
          status: result.status as SessionStatus,
          audio_files: result.audio_files || [],
          merged_audio: result.merged_audio,
          audio_file_urls: result.audio_file_urls || [],
          merged_audio_url: result.merged_audio_url,
        } : null)
      } else {
        setError(result.error || '合成失败')
      }
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }, [session])
  
  return {
    session,
    loading,
    error,
    streamingText,
    isStreaming,
    createSession,
    loadSession,
    deleteSession,
    refreshSession,
    analyzeDialogue,
    refineDialogue,
    updateDialogues,
    confirmStage1,
    matchVoices,
    rematchVoices,
    changeVoice,
    confirmStage2,
    synthesizeAudio,
    reset,
  }
}

// ============================================================================
// 会话列表 Hook
// ============================================================================

export function useTTSSessionList(): UseTTSSessionListReturn {
  const [sessions, setSessions] = useState<SessionListItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await api.listSessions(50)
      if (result.success) {
        setSessions(result.sessions || [])
      } else {
        setError(result.error || '加载会话列表失败')
      }
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  return {
    sessions,
    loading,
    error,
    refresh,
  }
}

export default useTTSSession
