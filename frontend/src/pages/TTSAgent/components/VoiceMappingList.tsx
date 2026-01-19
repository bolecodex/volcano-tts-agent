/**
 * 音色匹配列表组件
 * 
 * 功能：
 * - 显示角色与音色的映射关系
 * - 试听音频播放
 * - 更换音色（带音色选择器）
 * - 流式日志显示
 */

import { useState, useRef, useMemo, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  User,
  Volume2,
  Play,
  Pause,
  RefreshCw,
  ChevronDown,
  Loader2,
  CheckCircle2,
  XCircle,
  Circle,
  ChevronUp,
  Check,
  Search,
} from 'lucide-react'
import { listVoices, getVoiceCategories, previewVoice } from '@/services/api'
import type { VoiceMapping, VoiceInfo, VoiceCategory, StreamingLog } from '@/types'

interface VoiceMappingListProps {
  mappings: VoiceMapping[]
  onChangeVoice: (character: string, voiceId: string, voiceName?: string) => Promise<void>
  isStreaming?: boolean
  streamingLogs?: StreamingLog[]
}

export default function VoiceMappingList({ 
  mappings, 
  onChangeVoice, 
  isStreaming = false,
  streamingLogs = [] 
}: VoiceMappingListProps) {
  const [showLogs, setShowLogs] = useState(true)
  const logsEndRef = useRef<HTMLDivElement>(null)
  const [voices, setVoices] = useState<VoiceInfo[]>([])
  const [categories, setCategories] = useState<VoiceCategory[]>([])
  const [isVoiceLoading, setIsVoiceLoading] = useState(false)
  const [voiceError, setVoiceError] = useState<string | null>(null)

  // 自动滚动到最新日志
  useEffect(() => {
    if (isStreaming && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [streamingLogs, isStreaming])

  const loadVoiceOptions = useCallback(async () => {
    setIsVoiceLoading(true)
    setVoiceError(null)
    try {
      const [voiceRes, categoryRes] = await Promise.all([
        listVoices(undefined, undefined, 200),
        getVoiceCategories(),
      ])
      if (voiceRes.success) {
        setVoices(voiceRes.voices || [])
      }
      if (categoryRes.success) {
        setCategories(categoryRes.categories || [])
      }
    } catch (err) {
      setVoiceError((err as Error).message || '音色列表加载失败')
    } finally {
      setIsVoiceLoading(false)
    }
  }, [])

  useEffect(() => {
    loadVoiceOptions()
  }, [loadVoiceOptions])

  return (
    <div className="space-y-6">
      {/* 标题 */}
      <div className="flex items-center gap-3">
        <div className="p-2.5 bg-gradient-to-br from-neon-purple/20 to-neon-purple/5 rounded-xl border border-neon-purple/20">
          <Volume2 size={20} className="text-neon-purple" />
        </div>
        <div>
          <h3 className="font-heading font-semibold text-white">音色匹配</h3>
          <p className="text-sm text-slate-500">AI 已为每个角色推荐最佳音色</p>
        </div>
        <span className="text-sm text-slate-500 ml-auto">({mappings.length} 个角色)</span>
        
        {/* 流式处理指示器 */}
        {isStreaming && (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-neon-purple/10 rounded-lg">
            <Loader2 size={14} className="text-neon-purple animate-spin" />
            <span className="text-xs text-neon-purple">匹配中...</span>
          </div>
        )}
      </div>

      {/* 流式日志面板 */}
      <AnimatePresence>
        {(isStreaming || streamingLogs.length > 0) && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-cyber-bg rounded-xl border border-cyber-border overflow-hidden"
          >
            {/* 日志面板头部 */}
            <button
              onClick={() => setShowLogs(!showLogs)}
              className="w-full flex items-center justify-between px-4 py-3 
                       hover:bg-white/[0.02] transition-colors cursor-pointer"
            >
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${isStreaming ? 'bg-neon-purple animate-pulse' : 'bg-neon-green'}`} />
                <span className="text-sm text-slate-300">
                  {isStreaming ? '音色匹配进行中' : '匹配完成'}
                </span>
                <span className="text-xs text-slate-500">({streamingLogs.length} 条日志)</span>
              </div>
              <motion.div
                animate={{ rotate: showLogs ? 180 : 0 }}
                transition={{ duration: 0.2 }}
              >
                <ChevronUp size={16} className="text-slate-500" />
              </motion.div>
            </button>

            {/* 日志内容 */}
            <AnimatePresence>
              {showLogs && (
                <motion.div
                  initial={{ height: 0 }}
                  animate={{ height: 'auto' }}
                  exit={{ height: 0 }}
                  className="overflow-hidden"
                >
                  <div className="px-4 pb-4 max-h-48 overflow-auto space-y-1.5">
                    {streamingLogs.map((log) => (
                      <motion.div
                        key={log.id}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="flex items-start gap-2 text-sm"
                      >
                        <div className="flex-shrink-0 mt-0.5">
                          {log.type === 'success' ? (
                            <CheckCircle2 size={14} className="text-neon-green" />
                          ) : log.type === 'error' ? (
                            <XCircle size={14} className="text-red-400" />
                          ) : log.type === 'progress' ? (
                            <Loader2 size={14} className="text-neon-cyan animate-spin" />
                          ) : (
                            <Circle size={14} className="text-slate-500" />
                          )}
                        </div>
                        <span className={`flex-1 ${
                          log.type === 'success' ? 'text-neon-green' :
                          log.type === 'error' ? 'text-red-400' :
                          log.type === 'progress' ? 'text-neon-cyan' :
                          'text-slate-400'
                        }`}>
                          {log.message}
                        </span>
                        <span className="flex-shrink-0 text-xs text-slate-600">
                          {new Date(log.timestamp).toLocaleTimeString('zh-CN', { 
                            hour: '2-digit', 
                            minute: '2-digit',
                            second: '2-digit'
                          })}
                        </span>
                      </motion.div>
                    ))}
                    <div ref={logsEndRef} />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 音色卡片列表 */}
      <div className="grid gap-4">
        {mappings.map((mapping, index) => (
          <VoiceCard
            key={mapping.character}
            mapping={mapping}
            index={index}
            onChangeVoice={onChangeVoice}
            voices={voices}
            categories={categories}
            isVoiceLoading={isVoiceLoading}
            voiceError={voiceError}
          />
        ))}
      </div>
    </div>
  )
}

// ============================================================================
// VoiceCard 子组件
// ============================================================================

interface VoiceCardProps {
  mapping: VoiceMapping
  index: number
  onChangeVoice: (character: string, voiceId: string, voiceName?: string) => Promise<void>
  voices: VoiceInfo[]
  categories: VoiceCategory[]
  isVoiceLoading: boolean
  voiceError: string | null
}

function VoiceCard({
  mapping,
  index,
  onChangeVoice,
  voices,
  categories,
  isVoiceLoading,
  voiceError,
}: VoiceCardProps) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [isPreviewLoading, setIsPreviewLoading] = useState(false)
  const [previewError, setPreviewError] = useState<string | null>(null)
  const [showSelector, setShowSelector] = useState(false)
  const [search, setSearch] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('')
  const [selectedGender, setSelectedGender] = useState('')
  const [isChanging, setIsChanging] = useState(false)
  const audioRef = useRef<HTMLAudioElement>(null)
  const selectorRef = useRef<HTMLDivElement>(null)

  const releasePreviewUrl = useCallback((url: string | null) => {
    if (!url) return
    URL.revokeObjectURL(url)
  }, [])

  const ensurePreviewUrl = useCallback(async () => {
    if (previewUrl) return previewUrl
    if (!mapping.voice_id) return null

    setIsPreviewLoading(true)
    setPreviewError(null)
    try {
      const blob = await previewVoice(
        mapping.voice_id,
        mapping.preview_text || mapping.character || '你好，这是一段试听文本。'
      )
      const url = URL.createObjectURL(blob)
      setPreviewUrl((prev) => {
        releasePreviewUrl(prev)
        return url
      })
      return url
    } catch (err) {
      setPreviewError((err as Error).message || '试听生成失败')
      return null
    } finally {
      setIsPreviewLoading(false)
    }
  }, [mapping.character, mapping.preview_text, mapping.voice_id, previewUrl, releasePreviewUrl])

  // 播放/暂停试听
  const togglePlay = async () => {
    if (!audioRef.current) return
    const url = await ensurePreviewUrl()
    if (!url) return

    if (isPlaying) {
      audioRef.current.pause()
      setIsPlaying(false)
    } else {
      try {
        if (audioRef.current.src !== url) {
          audioRef.current.pause()
          audioRef.current.src = url
          audioRef.current.load()
        }
        await audioRef.current.play()
        setIsPlaying(true)
      } catch (err) {
        setPreviewError((err as Error).message || '播放失败')
      }
    }
  }

  const handleEnded = () => {
    setIsPlaying(false)
  }

  const availableGenders = useMemo(() => {
    const genders = new Set<string>()
    voices.forEach((voice) => {
      if (voice.gender) {
        genders.add(voice.gender)
      }
    })
    return Array.from(genders)
  }, [voices])

  const filteredVoices = useMemo(() => {
    return voices.filter((voice) => {
      if (selectedCategory && voice.category !== selectedCategory) return false
      if (selectedGender && voice.gender !== selectedGender) return false
      if (!search.trim()) return true
      const keyword = search.trim().toLowerCase()
      return (
        voice.name.toLowerCase().includes(keyword) ||
        voice.voice_id.toLowerCase().includes(keyword) ||
        voice.description?.toLowerCase().includes(keyword) ||
        voice.tags?.some((tag) => tag.toLowerCase().includes(keyword))
      )
    })
  }, [voices, selectedCategory, selectedGender, search])

  const handleSelectVoice = async (voice: VoiceInfo) => {
    if (isChanging || voice.voice_id === mapping.voice_id) return
    setIsChanging(true)
    try {
      await onChangeVoice(mapping.character, voice.voice_id, voice.name)
      setIsPlaying(false)
      setPreviewUrl((prev) => {
        releasePreviewUrl(prev)
        return null
      })
      setShowSelector(false)
    } catch (err) {
      console.error('更换音色失败:', err)
    } finally {
      setIsChanging(false)
    }
  }

  useEffect(() => {
    setIsPlaying(false)
    setPreviewError(null)
    setPreviewUrl((prev) => {
      releasePreviewUrl(prev)
      return null
    })
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.src = ''
      audioRef.current.load()
    }
  }, [mapping.voice_id, mapping.preview_text, releasePreviewUrl])

  useEffect(() => {
    return () => {
      releasePreviewUrl(previewUrl)
    }
  }, [previewUrl, releasePreviewUrl])

  useEffect(() => {
    if (!showSelector) return
    const handleClickOutside = (event: MouseEvent) => {
      if (!selectorRef.current) return
      if (!selectorRef.current.contains(event.target as Node)) {
        setShowSelector(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [showSelector])

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className={`glass-card p-5 relative ${showSelector ? 'z-50' : 'z-0'}`}
    >
      <div className="flex items-start gap-4">
        {/* 角色图标 */}
        <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-gradient-to-br from-neon-purple/20 to-neon-pink/20 
                      flex items-center justify-center">
          <User size={24} className="text-neon-purple" />
        </div>

        {/* 内容 */}
        <div className="flex-1 min-w-0">
          {/* 角色名称 */}
          <h4 className="text-base font-medium text-white mb-1">
            {mapping.character}
          </h4>

          {/* 音色信息 */}
          <div className="flex items-center gap-2 mb-2">
            <span className="px-2.5 py-1 text-xs font-medium bg-gradient-to-r from-neon-purple/20 to-neon-pink/20 
                           text-neon-purple rounded-lg border border-neon-purple/20">
              {mapping.voice_name || mapping.voice_id}
            </span>
          </div>

          {/* 匹配理由 */}
          {mapping.reason && (
            <p className="text-xs text-slate-500 mb-3">{mapping.reason}</p>
          )}

          {/* 试听播放器 */}
          <div className="space-y-2">
            <div className="flex items-center gap-3 p-3 bg-cyber-bg/50 rounded-lg border border-cyber-border/50">
              <button
                onClick={togglePlay}
                disabled={isPreviewLoading || !mapping.voice_id}
                className="flex-shrink-0 w-8 h-8 rounded-full bg-neon-purple/20 
                         flex items-center justify-center text-neon-purple
                         hover:bg-neon-purple/30 transition-colors cursor-pointer
                         disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isPreviewLoading ? (
                  <Loader2 size={14} className="animate-spin" />
                ) : isPlaying ? (
                  <Pause size={14} />
                ) : (
                  <Play size={14} />
                )}
              </button>

              <div className="flex-1">
                <div className="text-xs text-slate-400 mb-1 truncate">
                  {mapping.preview_text || '试听音频'}
                </div>
                <div className="h-1 bg-cyber-border rounded-full">
                  <div className="h-full w-0 bg-neon-purple rounded-full" />
                </div>
              </div>

              <audio ref={audioRef} onEnded={handleEnded} />
            </div>

            {previewError && <div className="text-xs text-red-400">{previewError}</div>}
          </div>
        </div>

        {/* 更换音色按钮 */}
        <div className="flex-shrink-0 relative">
          <button
            onClick={() => setShowSelector(!showSelector)}
            className="flex items-center gap-2 px-3 py-2 text-sm text-slate-400
                     hover:text-white hover:bg-white/5 rounded-lg transition-colors cursor-pointer"
          >
            <RefreshCw size={14} />
            更换
            <ChevronDown size={14} />
          </button>

          {/* 音色选择器 */}
          {showSelector && (
            <div
              ref={selectorRef}
              className="absolute top-full right-0 mt-2 w-96 bg-cyber-surface border border-cyber-border 
                       rounded-xl shadow-xl z-[70] overflow-hidden"
            >
              <div className="p-3 border-b border-cyber-border space-y-2">
                <div className="text-xs text-slate-500">选择音色</div>
                <div className="relative">
                  <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                  <input
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="搜索音色名称或标签..."
                    className="w-full pl-9 pr-3 py-2 text-xs bg-cyber-bg border border-cyber-border rounded-lg
                             text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-neon-purple/40"
                  />
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <select
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    className="flex-1 bg-cyber-bg border border-cyber-border rounded-lg px-2 py-1.5 text-slate-300"
                  >
                    <option value="">全部分类</option>
                    {categories.map((category) => (
                      <option key={category.category} value={category.category}>
                        {category.name || category.category}
                      </option>
                    ))}
                  </select>
                  <select
                    value={selectedGender}
                    onChange={(e) => setSelectedGender(e.target.value)}
                    className="flex-1 bg-cyber-bg border border-cyber-border rounded-lg px-2 py-1.5 text-slate-300"
                  >
                    <option value="">全部性别</option>
                    {availableGenders.map((gender) => (
                      <option key={gender} value={gender}>
                        {gender}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="max-h-72 overflow-auto">
                {isVoiceLoading ? (
                  <div className="p-4 text-sm text-slate-400 text-center flex items-center justify-center gap-2">
                    <Loader2 size={14} className="animate-spin text-neon-purple" />
                    音色列表加载中...
                  </div>
                ) : voiceError ? (
                  <div className="p-4 text-sm text-red-400 text-center">
                    {voiceError}
                  </div>
                ) : filteredVoices.length === 0 ? (
                  <div className="p-4 text-sm text-slate-400 text-center">
                    没有找到匹配的音色
                  </div>
                ) : (
                  filteredVoices.map((voice) => (
                    <button
                      key={voice.voice_id}
                      onClick={() => handleSelectVoice(voice)}
                      disabled={isChanging}
                      className={`w-full text-left px-4 py-3 border-b border-cyber-border last:border-b-0
                                transition-colors cursor-pointer ${
                                  voice.voice_id === mapping.voice_id
                                    ? 'bg-neon-purple/10'
                                    : 'hover:bg-white/5'
                                } ${isChanging ? 'opacity-60 cursor-not-allowed' : ''}`}
                    >
                      <div className="flex items-start gap-3">
                        <div className="flex-shrink-0 pt-0.5">
                          {voice.voice_id === mapping.voice_id ? (
                            <Check size={14} className="text-neon-purple" />
                          ) : (
                            <div className="w-3.5 h-3.5 rounded-full border border-slate-600" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-slate-200 truncate">
                              {voice.name || voice.voice_id}
                            </span>
                            <span className="text-xs text-slate-500">{voice.gender}</span>
                          </div>
                          {voice.description && (
                            <div className="text-xs text-slate-500 mt-1 max-h-8 overflow-hidden">
                              {voice.description}
                            </div>
                          )}
                          {voice.tags && voice.tags.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-1">
                              {voice.tags.slice(0, 3).map((tag) => (
                                <span
                                  key={tag}
                                  className="px-1.5 py-0.5 text-[10px] bg-cyber-bg text-slate-400 rounded"
                                >
                                  {tag}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </button>
                  ))
                )}
              </div>
              {isChanging && (
                <div className="px-4 py-2 text-xs text-neon-purple border-t border-cyber-border flex items-center gap-2">
                  <Loader2 size={12} className="animate-spin" />
                  正在切换音色...
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  )
}
