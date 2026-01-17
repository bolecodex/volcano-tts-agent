// ============================================================================
// 枚举与基础类型
// ============================================================================

// 会话状态
export type SessionStatus =
  | 'created'
  | 'analyzing'
  | 'dialogue_ready'
  | 'matching'
  | 'voice_ready'
  | 'synthesizing'
  | 'completed'
  | 'error'

// 输入类型
export type InputType = 'topic' | 'article' | 'dialogue'

// 阶段类型
export type Stage = 1 | 2 | 3

// ============================================================================
// 基础数据模型
// ============================================================================

// 对话条目
export interface DialogueItem {
  id?: number
  index: number
  character: string
  character_desc?: string
  text: string
  instruction?: string
  context?: string
  audio_path?: string
  duration_ms?: number
}

// 音色映射
export interface VoiceMapping {
  id?: number
  character: string
  voice_id: string
  voice_name?: string
  reason?: string
  preview_audio?: string
  preview_text?: string
}

// 音色信息
export interface VoiceInfo {
  voice_id: string
  name: string
  gender: string
  description?: string
  tags?: string[]
  category?: string
}

// 音色分类
export interface VoiceCategory {
  category: string
  name: string
  description?: string
  count: number
}

// ============================================================================
// 会话模型
// ============================================================================

// TTS 会话
export interface TTSSession {
  session_id: string
  db_id?: number
  status: SessionStatus
  user_input?: string
  input_type?: InputType
  dialogue_list: DialogueItem[]
  voice_mapping: VoiceMapping[]
  audio_files: string[]
  merged_audio?: string
  output_dir?: string
  error?: string
  created_at?: string
  updated_at?: string
}

// 会话列表项（简化版）
export interface SessionListItem {
  id?: number
  session_id: string
  status: SessionStatus
  user_input?: string
  input_type?: InputType
  dialogue_count?: number
  voice_mapping_count?: number
  has_merged_audio?: boolean
  created_at?: string
  updated_at?: string
}

// ============================================================================
// SSE 事件类型
// ============================================================================

export type TTSEventType =
  | 'tts:session:created'
  | 'tts:session:connected'
  | 'tts:session:ended'
  | 'tts:analyze:start'
  | 'tts:analyze:chunk'
  | 'tts:analyze:complete'
  | 'tts:match:start'
  | 'tts:match:character'
  | 'tts:preview:generating'
  | 'tts:preview:ready'
  | 'tts:match:complete'
  | 'tts:synth:start'
  | 'tts:synth:item'
  | 'tts:synth:merge'
  | 'tts:synth:complete'
  | 'tts:status:changed'
  | 'tts:error'

export interface TTSEvent {
  type: TTSEventType
  data: Record<string, any>
}

// ============================================================================
// UI 状态类型
// ============================================================================

export interface StageInfo {
  stage: Stage
  label: string
  status: 'pending' | 'active' | 'completed'
}

export interface StreamingLog {
  id: string
  type: 'info' | 'success' | 'error' | 'progress'
  message: string
  timestamp: Date
}
