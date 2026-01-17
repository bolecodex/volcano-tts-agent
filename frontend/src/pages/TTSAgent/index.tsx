/**
 * TTS Agent 主页面 - 语音合成工作台
 * 
 * 三栏式布局：
 * - 左栏：会话列表
 * - 中栏：主内容区（输入/对话列表/音色匹配/结果）
 * - 右栏：Agent 交互面板（可选）
 */

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Plus, 
  Loader2,
  Sparkles,
  Activity,
  Music2,
  Radio,
  ArrowRight,
  Users,
  Volume2,
} from 'lucide-react'
import { useTTSSession, useTTSSessionList } from '@/hooks/useTTSSession'
import SessionList from './components/SessionList'
import StageIndicator from './components/StageIndicator'
import DialogueList from './components/DialogueList'
import VoiceMappingList from './components/VoiceMappingList'
import ResultPanel from './components/ResultPanel'
import type { Stage, StreamingLog } from '@/types'

export default function TTSAgentPage() {
  const [userInput, setUserInput] = useState('')
  const [streamingLogs, setStreamingLogs] = useState<StreamingLog[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  
  const {
    session,
    loading,
    error,
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
  } = useTTSSession()
  
  const sessionList = useTTSSessionList()
  
  // 计算当前阶段
  const getCurrentStage = (): Stage => {
    if (!session) return 1
    switch (session.status) {
      case 'created':
      case 'analyzing':
      case 'dialogue_ready':
        return 1
      case 'matching':
      case 'voice_ready':
        return 2
      case 'synthesizing':
      case 'completed':
        return 3
      default:
        return 1
    }
  }
  
  const currentStage = getCurrentStage()
  
  // 创建新会话
  const handleCreateSession = async () => {
    const newSessionId = await createSession()
    if (newSessionId) {
      sessionList.refresh()
    }
  }
  
  // 选择会话
  const handleSelectSession = async (sessionId: string) => {
    setStreamingLogs([])
    await loadSession(sessionId)
  }
  
  // 删除会话
  const handleDeleteSession = async (sessionId: string) => {
    await deleteSession(sessionId)
    sessionList.refresh()
  }
  
  // 开始分析
  const handleAnalyze = async () => {
    if (!userInput.trim()) return
    setStreamingLogs([])
    await analyzeDialogue(userInput)
    setUserInput('')
  }
  
  // 确认对话并进入阶段二
  const handleConfirmDialogue = async () => {
    await confirmStage1()
    await matchVoices()
  }
  
  // 确认音色并进入阶段三
  const handleConfirmVoice = async () => {
    await confirmStage2()
    await synthesizeAudio()
  }

  // 更换音色
  const handleChangeVoice = async (character: string, voiceId: string, voiceName?: string) => {
    await changeVoice(character, voiceId, voiceName)
  }

  // 更新对话
  const handleUpdateDialogues = async (dialogues: any[]) => {
    await updateDialogues(dialogues)
  }
  
  return (
    <div className="min-h-screen bg-cyber-bg relative overflow-hidden">
      {/* 背景效果 */}
      <div className="fixed inset-0 bg-cyber-grid bg-grid opacity-30" />
      <div className="fixed inset-0 bg-gradient-radial from-neon-cyan/5 via-transparent to-transparent" />
      <div className="fixed top-0 right-0 w-[800px] h-[800px] bg-gradient-radial from-neon-purple/10 via-transparent to-transparent" />
      <div className="fixed bottom-0 left-0 w-[600px] h-[600px] bg-gradient-radial from-neon-cyan/5 via-transparent to-transparent" />
      
      <div className="relative flex h-screen">
        {/* 左侧：会话列表 */}
        <motion.aside
          initial={{ x: -20, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          className="w-80 bg-cyber-surface/80 backdrop-blur-xl border-r border-cyber-border flex flex-col"
        >
          {/* Logo 区域 */}
          <div className="p-5 border-b border-cyber-border">
            <div className="flex items-center gap-3 mb-5">
              <div className="relative">
                <div className="absolute inset-0 bg-neon-cyan/30 blur-lg rounded-xl" />
                <div className="relative p-2.5 bg-gradient-to-br from-neon-cyan/20 to-neon-purple/20 rounded-xl border border-neon-cyan/30">
                  <Activity className="w-6 h-6 text-neon-cyan" />
                </div>
              </div>
              <div>
                <h1 className="font-heading font-bold text-lg text-white">TTS Agent</h1>
                <p className="text-xs text-slate-500">智能语音合成</p>
              </div>
            </div>
            
            <button
              onClick={handleCreateSession}
              disabled={loading}
              className="cyber-button-primary w-full flex items-center justify-center gap-2 font-heading cursor-pointer"
            >
              <Plus className="w-5 h-5" />
              <span>新建会话</span>
            </button>
          </div>
          
          {/* 会话列表 */}
          <SessionList
            sessions={sessionList.sessions}
            currentSessionId={session?.session_id}
            isLoading={sessionList.loading}
            onSelect={handleSelectSession}
            onDelete={handleDeleteSession}
            onRefresh={sessionList.refresh}
          />
        </motion.aside>
        
        {/* 主内容区 */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {/* 头部 - 阶段指示器 */}
          {session && (
            <motion.header
              initial={{ y: -20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              className="px-8 py-4 bg-cyber-surface/50 backdrop-blur-xl border-b border-cyber-border"
            >
              <StageIndicator currentStage={currentStage} status={session.status} />
            </motion.header>
          )}
          
          {/* 内容区 */}
          <div className="flex-1 overflow-y-auto p-8">
            <AnimatePresence mode="wait">
              {!session ? (
                <EmptyState />
              ) : (
                <motion.div
                  key="content"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="max-w-4xl mx-auto space-y-6"
                >
                  {/* 错误提示 */}
                  {error && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="p-4 glass-card border-red-500/30 bg-red-500/10"
                    >
                      <p className="text-red-300">{error}</p>
                    </motion.div>
                  )}
                  
                  {/* 阶段一：输入分析 */}
                  {currentStage === 1 && (
                    <>
                      {/* 输入框 */}
                      {session.dialogue_list.length === 0 && (
                        <motion.div
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          className="glass-card p-6"
                        >
                          <div className="flex items-center gap-3 mb-5">
                            <div className="p-2.5 bg-gradient-to-br from-neon-cyan/20 to-neon-cyan/5 rounded-xl border border-neon-cyan/20">
                              <Sparkles className="w-5 h-5 text-neon-cyan" />
                            </div>
                            <div>
                              <h2 className="font-heading font-semibold text-lg text-white">
                                阶段一：对话分析
                              </h2>
                              <p className="text-sm text-slate-500">输入内容，AI 将自动识别对话结构</p>
                            </div>
                          </div>
                          
                          {/* 快速输入预设 */}
                          <div className="mb-4">
                            <p className="text-xs text-slate-500 mb-2">快速开始：</p>
                            <div className="flex flex-wrap gap-2">
                              {[
                                { label: '职场面试', value: '职场面试。' },
                                { label: '科技新闻', value: '科技新闻播报。' },
                                { label: '情感故事', value: '写一个感人的爱情故事。' },
                                { label: '产品介绍', value: '智能手机产品介绍。' },
                                { label: '日常对话', value: '朋友之间的日常闲聊对话。' },
                                { label: '教育科普', value: '关于宇宙的科普知识讲解。' },
                              ].map((preset) => (
                                <button
                                  key={preset.label}
                                  onClick={() => setUserInput(preset.value)}
                                  className="px-3 py-1.5 text-xs font-medium rounded-lg 
                                           bg-cyber-border/50 text-slate-400 
                                           hover:bg-neon-cyan/20 hover:text-neon-cyan 
                                           hover:border-neon-cyan/30 border border-transparent
                                           transition-all duration-200 cursor-pointer"
                                >
                                  {preset.label}
                                </button>
                              ))}
                            </div>
                          </div>
                          
                          <textarea
                            value={userInput}
                            onChange={(e) => setUserInput(e.target.value)}
                            placeholder={`输入要转换为语音的内容...\n\n支持以下输入类型：\n• 话题关键词（如：职场面试、科技新闻）\n• 完整文章\n• 对话脚本`}
                            className="cyber-input h-44 resize-none font-body"
                          />
                          
                          <div className="flex items-center justify-between mt-5">
                            <p className="text-xs text-slate-500">
                              {userInput.length > 0 && `${userInput.length} 字符`}
                            </p>
                            <button
                              onClick={handleAnalyze}
                              disabled={loading || !userInput.trim()}
                              className="cyber-button-primary flex items-center gap-2 cursor-pointer"
                            >
                              {loading ? (
                                <>
                                  <Loader2 className="w-4 h-4 animate-spin" />
                                  <span>分析中...</span>
                                </>
                              ) : (
                                <>
                                  <Sparkles className="w-4 h-4" />
                                  <span>开始分析</span>
                                </>
                              )}
                            </button>
                          </div>
                        </motion.div>
                      )}
                      
                      {/* 对话列表显示 */}
                      {session.dialogue_list.length > 0 && (
                        <>
                          <DialogueList
                            dialogues={session.dialogue_list}
                            onUpdate={handleUpdateDialogues}
                            editable={true}
                          />
                          
                          {/* 确认按钮 */}
                          <div className="flex justify-center pt-4">
                            <motion.button
                              whileHover={{ scale: 1.02 }}
                              whileTap={{ scale: 0.98 }}
                              onClick={handleConfirmDialogue}
                              disabled={loading}
                              className="px-8 py-3 bg-gradient-to-r from-neon-cyan to-neon-purple 
                                       text-white font-medium rounded-xl
                                       hover:from-neon-cyan/90 hover:to-neon-purple/90 transition-all
                                       shadow-lg shadow-neon-cyan/20
                                       disabled:opacity-50 disabled:cursor-not-allowed
                                       flex items-center gap-3 cursor-pointer"
                            >
                              {loading ? (
                                <>
                                  <Loader2 className="w-5 h-5 animate-spin" />
                                  处理中...
                                </>
                              ) : (
                                <>
                                  <Users className="w-5 h-5" />
                                  确认并匹配音色
                                  <ArrowRight className="w-5 h-5" />
                                </>
                              )}
                            </motion.button>
                          </div>
                        </>
                      )}
                    </>
                  )}
                  
                  {/* 阶段二：音色匹配 */}
                  {currentStage === 2 && (
                    <>
                      <VoiceMappingList
                        mappings={session.voice_mapping}
                        onChangeVoice={handleChangeVoice}
                        isStreaming={isStreaming}
                        streamingLogs={streamingLogs}
                      />
                      
                      {/* 确认按钮 */}
                      {session.voice_mapping.length > 0 && !isStreaming && (
                        <div className="flex justify-center pt-4">
                          <motion.button
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={handleConfirmVoice}
                            disabled={loading}
                            className="px-8 py-3 bg-gradient-to-r from-neon-purple to-neon-pink 
                                     text-white font-medium rounded-xl
                                     hover:from-neon-purple/90 hover:to-neon-pink/90 transition-all
                                     shadow-lg shadow-neon-purple/20
                                     disabled:opacity-50 disabled:cursor-not-allowed
                                     flex items-center gap-3 cursor-pointer"
                          >
                            {loading ? (
                              <>
                                <Loader2 className="w-5 h-5 animate-spin" />
                                合成中...
                              </>
                            ) : (
                              <>
                                <Volume2 className="w-5 h-5" />
                                确认并开始合成
                                <ArrowRight className="w-5 h-5" />
                              </>
                            )}
                          </motion.button>
                        </div>
                      )}
                    </>
                  )}
                  
                  {/* 阶段三：合成结果 */}
                  {currentStage === 3 && (
                    <>
                      {session.status === 'synthesizing' || isStreaming ? (
                        <SynthesisProgress logs={streamingLogs} total={session.dialogue_list.length} />
                      ) : (
                        <ResultPanel
                          sessionId={session.session_id}
                          audioFiles={session.audio_files}
                          mergedAudio={session.merged_audio}
                          dialogues={session.dialogue_list}
                        />
                      )}
                    </>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </main>
      </div>
    </div>
  )
}

// ============================================================================
// 空状态组件
// ============================================================================

function EmptyState() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center justify-center h-full text-center px-8"
    >
      <div className="relative mb-8">
        <motion.div
          animate={{ 
            scale: [1, 1.1, 1],
            rotate: [0, 5, -5, 0]
          }}
          transition={{ duration: 4, repeat: Infinity }}
          className="relative"
        >
          <div className="absolute inset-0 bg-gradient-to-r from-neon-cyan/20 to-neon-purple/20 blur-3xl rounded-full" />
          <div className="relative glass-card p-8 rounded-3xl border-neon-cyan/20">
            <Music2 className="w-20 h-20 text-neon-cyan" strokeWidth={1.5} />
          </div>
        </motion.div>
        
        <motion.div
          className="absolute -top-2 -right-2"
          animate={{ y: [-2, 2, -2] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          <Sparkles className="w-6 h-6 text-neon-purple" />
        </motion.div>
      </div>
      
      <h2 className="text-2xl font-heading font-bold text-white mb-3">
        开始创建语音
      </h2>
      <p className="text-slate-400 max-w-md mb-8 leading-relaxed">
        选择一个已有会话继续工作，或点击左侧的
        <span className="text-neon-cyan font-medium"> "新建会话" </span>
        按钮开始全新的语音合成之旅
      </p>
      
      <div className="flex items-center gap-2 text-sm text-slate-500">
        <Radio className="w-4 h-4" />
        <span>支持多角色对话、自动音色匹配</span>
      </div>
    </motion.div>
  )
}

// ============================================================================
// 合成进度组件
// ============================================================================

interface SynthesisProgressProps {
  logs: StreamingLog[]
  total: number
}

function SynthesisProgress({ logs, total }: SynthesisProgressProps) {
  // 从日志中提取当前进度
  const progressLog = logs.filter(l => l.type === 'progress').pop()
  let current = 0
  if (progressLog) {
    const match = progressLog.message.match(/(\d+)\/(\d+)/)
    if (match) {
      current = parseInt(match[1])
    }
  }
  
  const progress = total > 0 ? (current / total) * 100 : 0

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-8 text-center"
    >
      <div className="w-16 h-16 mx-auto mb-6 relative">
        <div className="absolute inset-0 rounded-full border-4 border-cyber-border" />
        <motion.div 
          className="absolute inset-0 rounded-full border-4 border-neon-cyan border-t-transparent"
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
        />
        <div className="absolute inset-0 flex items-center justify-center">
          <Volume2 className="w-6 h-6 text-neon-cyan" />
        </div>
      </div>
      
      <h3 className="text-xl font-heading font-semibold text-white mb-2">
        正在合成语音...
      </h3>
      <p className="text-slate-400 mb-6">
        {current > 0 ? `已完成 ${current}/${total} 条对话` : '准备中...'}
      </p>
      
      {/* 进度条 */}
      <div className="max-w-md mx-auto">
        <div className="h-2 bg-cyber-border rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-neon-cyan to-neon-purple"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>
        <p className="text-xs text-slate-500 mt-2">{Math.round(progress)}%</p>
      </div>
      
      {/* 日志显示 */}
      <div className="mt-6 max-h-32 overflow-auto text-left">
        {logs.slice(-5).map((log) => (
          <div
            key={log.id}
            className={`text-xs py-1 ${
              log.type === 'success' ? 'text-neon-green' :
              log.type === 'error' ? 'text-red-400' :
              log.type === 'progress' ? 'text-neon-cyan' :
              'text-slate-500'
            }`}
          >
            {log.message}
          </div>
        ))}
      </div>
    </motion.div>
  )
}
