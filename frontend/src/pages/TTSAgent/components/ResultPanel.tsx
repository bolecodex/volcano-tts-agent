/**
 * 结果面板组件
 * 
 * 功能：
 * - 完整音频播放（带进度条）
 * - 分句音频列表播放
 * - 播放时高亮当前对话
 * - 字级高亮动画
 * - 自动滚动到播放位置
 * - 下载功能
 */

import { useState, useRef, useMemo, useEffect, useCallback, forwardRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Play,
  Pause,
  Download,
  Music,
  FileAudio,
  Check,
  Volume2,
  ChevronDown,
  ChevronUp,
  Sparkles,
  BookOpen,
} from 'lucide-react'
import { getMergedAudioUrl, getAudioUrl } from '@/services/api'
import type { DialogueItem } from '@/types'

interface TimeRange {
  start: number
  end: number
}

interface ResultPanelProps {
  sessionId: string
  audioFiles: string[]
  mergedAudio?: string
  audioFileUrls?: string[]
  mergedAudioUrl?: string | null
  dialogues: DialogueItem[]
}

export default function ResultPanel({
  sessionId,
  audioFiles,
  mergedAudio,
  audioFileUrls: audioFileUrlsOverride,
  mergedAudioUrl: mergedAudioUrlOverride,
  dialogues,
}: ResultPanelProps) {
  const [playingMerged, setPlayingMerged] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const mergedAudioRef = useRef<HTMLAudioElement>(null)
  const [mergedPlayableUrl, setMergedPlayableUrl] = useState<string | null>(null)
  
  // 高亮状态管理
  const [highlightIndex, setHighlightIndex] = useState<number | null>(null)
  const [playingSource, setPlayingSource] = useState<'merged' | 'item' | null>(null)
  const [playingItemIndex, setPlayingItemIndex] = useState<number | null>(null)
  const [charProgress, setCharProgress] = useState<number>(0)
  
  // 动态加载的音频时长
  const [loadedDurations, setLoadedDurations] = useState<number[]>([])
  
  // 列表容器引用
  const listContainerRef = useRef<HTMLDivElement>(null)
  const itemRefs = useRef<Map<number, HTMLDivElement>>(new Map())

  const runtimeBaseUrl = (import.meta.env.VITE_TTS_API_BASE_URL || '').trim().replace(/\/$/, '')
  const runtimeApiKey = (import.meta.env.VITE_TTS_API_KEY || '').trim()

  const cleanUrl = useCallback((url: string) => {
    const trimmed = url.trim()
    const withoutTicks = trimmed.replace(/^`+/, '').replace(/`+$/, '').trim()
    return withoutTicks
  }, [])

  const needsAuthHeader = useCallback(
    (url: string) => Boolean(runtimeApiKey && runtimeBaseUrl && cleanUrl(url).startsWith(runtimeBaseUrl)),
    [cleanUrl, runtimeApiKey, runtimeBaseUrl]
  )

  const downloadBlob = useCallback((blob: Blob, filename: string) => {
    const objectUrl = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = objectUrl
    a.download = filename
    a.click()
    URL.revokeObjectURL(objectUrl)
  }, [])

  const fetchAudioBlob = useCallback(
    async (url: string, signal?: AbortSignal) => {
      const targetUrl = cleanUrl(url)
      const headers: Record<string, string> = {}
      if (needsAuthHeader(targetUrl)) {
        headers.Authorization = `Bearer ${runtimeApiKey}`
      }
      const response = await fetch(targetUrl, {
        method: 'GET',
        headers,
        signal,
      })
      if (!response.ok) {
        throw new Error(`音频请求失败: ${response.status}`)
      }
      return await response.blob()
    },
    [cleanUrl, needsAuthHeader, runtimeApiKey]
  )

  // 音频 URL
  const mergedAudioUrl = useMemo(
    () => {
      if (!mergedAudio) return null
      if (mergedAudioUrlOverride) return cleanUrl(mergedAudioUrlOverride)
      return getMergedAudioUrl(sessionId)
    },
    [cleanUrl, mergedAudio, mergedAudioUrlOverride, sessionId]
  )
  
  const audioFileUrls = useMemo(
    () => {
      if (audioFileUrlsOverride && audioFileUrlsOverride.length > 0) {
        return audioFileUrlsOverride.map(cleanUrl)
      }
      return audioFiles.map((path, i) => getAudioUrl(sessionId, path.split('/').pop() || `${i}.mp3`))
    },
    [audioFileUrlsOverride, audioFiles, cleanUrl, sessionId]
  )

  // 动态加载所有音频文件的时长
  useEffect(() => {
    if (audioFileUrls.length === 0) return
    
    const controller = new AbortController()
    const signal = controller.signal
    let cancelled = false

    const getDurationForUrl = async (rawUrl: string): Promise<number> => {
      const targetUrl = cleanUrl(rawUrl)
      let objectUrl: string | null = null
      const audio = new Audio()
      audio.preload = 'metadata'

      const durationSec = await new Promise<number>((resolve) => {
        if (signal.aborted) return resolve(2)

        let settled = false
        let timer = 0

        const cleanup = () => {
          window.clearTimeout(timer)
          audio.removeEventListener('loadedmetadata', onLoadedMetadata)
          audio.removeEventListener('error', onError)
          signal.removeEventListener('abort', onAbort)
        }

        const settle = (value: number) => {
          if (settled) return
          settled = true
          cleanup()
          resolve(value || 2)
        }

        const onLoadedMetadata = () => settle(audio.duration || 2)
        const onError = () => settle(2)
        const onAbort = () => settle(2)

        timer = window.setTimeout(() => settle(2), 8000)
        audio.addEventListener('loadedmetadata', onLoadedMetadata)
        audio.addEventListener('error', onError)
        signal.addEventListener('abort', onAbort)

        void (async () => {
          try {
            if (needsAuthHeader(targetUrl)) {
              const blob = await fetchAudioBlob(targetUrl, signal)
              objectUrl = URL.createObjectURL(blob)
              audio.src = objectUrl
            } else {
              audio.src = targetUrl
            }
            audio.load()
          } catch {
            settle(2)
          }
        })()
      })

      if (objectUrl) URL.revokeObjectURL(objectUrl)
      return durationSec
    }

    void (async () => {
      const durations: number[] = []
      for (const url of audioFileUrls) {
        if (cancelled) return
        try {
          durations.push(await getDurationForUrl(url))
        } catch {
          durations.push(2)
        }
      }
      if (!cancelled) setLoadedDurations(durations)
    })()

    return () => {
      cancelled = true
      controller.abort()
    }
  }, [audioFileUrls, cleanUrl, fetchAudioBlob, needsAuthHeader])

  // 计算每条对话在合并音频中的时间范围
  const timeRanges = useMemo<TimeRange[]>(() => {
    const ranges: TimeRange[] = []
    const DEFAULT_GAP_SEC = 0.5
    const n = dialogues.length
    const itemDurationsSec = dialogues.map((dialogue, i) => {
      return loadedDurations[i] || (dialogue.duration_ms ? dialogue.duration_ms / 1000 : 2)
    })
    const totalItemsSec = itemDurationsSec.reduce((sum, d) => sum + d, 0)

    const inferredGapSec =
      duration > 0 && n > 1
        ? Math.max((duration - totalItemsSec) / (n - 1), 0)
        : DEFAULT_GAP_SEC

    const baseTotalSec = totalItemsSec + inferredGapSec * Math.max(n - 1, 0)
    const scale = duration > 0 && baseTotalSec > 0 ? duration / baseTotalSec : 1

    let currentStart = 0
    
    for (let i = 0; i < dialogues.length; i++) {
      const durationSec = itemDurationsSec[i]
      ranges.push({
        start: currentStart,
        end: currentStart + durationSec * scale,
      })
      currentStart += durationSec * scale
      if (i < dialogues.length - 1) {
        currentStart += inferredGapSec * scale
      }
    }
    
    return ranges
  }, [dialogues, duration, loadedDurations])

  // 根据当前播放时间查找对应的对话索引
  const findCurrentDialogueIndex = useCallback((time: number): { index: number | null; progress: number } => {
    for (let i = 0; i < timeRanges.length; i++) {
      const range = timeRanges[i]
      if (time >= range.start && time < range.end) {
        const segmentDuration = range.end - range.start
        const timeInSegment = time - range.start
        const progress = segmentDuration > 0 ? timeInSegment / segmentDuration : 0
        return { index: i, progress }
      }
    }
    if (timeRanges.length > 0 && time >= timeRanges[timeRanges.length - 1].start) {
      return { index: timeRanges.length - 1, progress: 1 }
    }
    return { index: null, progress: 0 }
  }, [timeRanges])

  // 自动滚动到高亮项
  const scrollToItem = useCallback((index: number) => {
    const itemElement = itemRefs.current.get(index)
    if (itemElement && listContainerRef.current) {
      itemElement.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      })
    }
  }, [])

  // 处理合并音频时间更新
  const handleMergedTimeUpdate = useCallback((time: number) => {
    setCurrentTime(time)
    
    if (playingSource === 'merged') {
      const { index, progress } = findCurrentDialogueIndex(time)
      setCharProgress(progress)
      
      if (index !== null && index !== highlightIndex) {
        setHighlightIndex(index)
        scrollToItem(index)
      }
    }
  }, [playingSource, findCurrentDialogueIndex, highlightIndex, scrollToItem])

  // 处理分句音频播放开始
  const handleItemPlayStart = useCallback((index: number) => {
    if (mergedAudioRef.current && playingMerged) {
      mergedAudioRef.current.pause()
      setPlayingMerged(false)
    }
    
    setPlayingSource('item')
    setPlayingItemIndex(index)
    setHighlightIndex(index)
    setCharProgress(0)
  }, [playingMerged])

  // 处理分句音频播放结束
  const handleItemPlayEnd = useCallback((index: number) => {
    if (playingItemIndex === index) {
      setPlayingItemIndex(null)
      setCharProgress(0)
      setTimeout(() => {
        if (playingSource === 'item') {
          setHighlightIndex(null)
          setPlayingSource(null)
        }
      }, 500)
    }
  }, [playingItemIndex, playingSource])

  // 播放/暂停合并音频
  const toggleMergedPlay = async () => {
    if (!mergedAudioRef.current || !mergedAudioUrl) return

    if (playingMerged) {
      mergedAudioRef.current.pause()
      setPlayingMerged(false)
      setPlayingSource(null)
    } else {
      try {
        setPlayingItemIndex(null)

        const targetUrl = cleanUrl(mergedAudioUrl)
        let playable = targetUrl
        if (needsAuthHeader(targetUrl)) {
          if (!mergedPlayableUrl) {
            const blob = await fetchAudioBlob(targetUrl)
            const objectUrl = URL.createObjectURL(blob)
            setMergedPlayableUrl(prev => {
              if (prev) URL.revokeObjectURL(prev)
              return objectUrl
            })
            playable = objectUrl
          } else {
            playable = mergedPlayableUrl
          }
        }

        if (mergedAudioRef.current.src !== playable) {
          mergedAudioRef.current.pause()
          mergedAudioRef.current.src = playable
          mergedAudioRef.current.load()
        }
        
        await mergedAudioRef.current.play()
        setPlayingMerged(true)
        setPlayingSource('merged')
        
        const { index, progress } = findCurrentDialogueIndex(mergedAudioRef.current.currentTime)
        setCharProgress(progress)
        if (index !== null) {
          setHighlightIndex(index)
          scrollToItem(index)
        }
      } catch (err) {
        console.error('播放失败:', err)
      }
    }
  }

  const handleMergedEnded = useCallback(() => {
    setPlayingMerged(false)
    setPlayingSource(null)
    setHighlightIndex(null)
    setCharProgress(0)
  }, [])

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const generateTimestampFilename = (prefix: string, ext: string = 'mp3'): string => {
    const now = new Date()
    const timestamp = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}${String(now.getSeconds()).padStart(2, '0')}`
    return `${prefix}_${timestamp}.${ext}`
  }

  const handleDownload = useCallback(
    async (url: string, filename: string) => {
      const targetUrl = cleanUrl(url)
      try {
        if (needsAuthHeader(targetUrl)) {
          const blob = await fetchAudioBlob(targetUrl)
          downloadBlob(blob, filename)
          return
        }

        const a = document.createElement('a')
        a.href = targetUrl
        a.download = filename
        a.click()
      } catch (err) {
        console.error('下载失败:', err)
      }
    },
    [cleanUrl, downloadBlob, fetchAudioBlob, needsAuthHeader]
  )

  useEffect(() => {
    if (mergedAudioRef.current) {
      mergedAudioRef.current.pause()
      mergedAudioRef.current.src = ''
      mergedAudioRef.current.load()
    }
    setPlayingMerged(false)
    setPlayingSource(null)
    setHighlightIndex(null)
    setCharProgress(0)
    setCurrentTime(0)
    setDuration(0)
    setMergedPlayableUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev)
      return null
    })
  }, [mergedAudioUrl])

  return (
    <div className="space-y-8">
      {/* 成功提示 */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="text-center py-6"
      >
        <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-neon-green/20 to-emerald-500/20 
                      flex items-center justify-center mx-auto mb-4">
          <Check size={36} className="text-neon-green" />
        </div>
        <h2 className="text-xl font-semibold text-white mb-2">合成完成</h2>
        <p className="text-sm text-slate-500">
          共生成 {audioFiles.length} 个音频文件
        </p>
      </motion.div>

      {/* 完整音频播放器 */}
      {mergedAudio && mergedAudioUrl && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-6 border-neon-green/20"
        >
          <div className="flex items-center gap-4 mb-4">
            <div className="w-14 h-14 rounded-xl bg-neon-green/20 flex items-center justify-center">
              <Music size={24} className="text-neon-green" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-medium text-white">完整音频</h3>
              <p className="text-sm text-slate-500">所有对话合并后的完整音频</p>
            </div>
            <button
              onClick={() => {
                if (!mergedAudioUrl) return
                void handleDownload(mergedAudioUrl, generateTimestampFilename('dialogue_full'))
              }}
              className="flex items-center gap-2 px-4 py-2 bg-neon-green hover:bg-neon-green/80 
                       text-cyber-bg rounded-xl transition-colors cursor-pointer"
            >
              <Download size={16} />
              下载
            </button>
          </div>

          {/* 播放控制 */}
          <div className="flex items-center gap-4">
            <button
              onClick={toggleMergedPlay}
              className="w-12 h-12 rounded-full bg-neon-green hover:bg-neon-green/80 
                       flex items-center justify-center text-cyber-bg transition-colors cursor-pointer"
            >
              {playingMerged ? <Pause size={20} /> : <Play size={20} />}
            </button>

            <div className="flex-1">
              <div className="h-2 bg-cyber-border rounded-full cursor-pointer">
                <div
                  className="h-full bg-neon-green rounded-full transition-all"
                  style={{ width: `${duration ? (currentTime / duration) * 100 : 0}%` }}
                />
              </div>
              <div className="flex justify-between mt-1 text-xs text-slate-500">
                <span>{formatTime(currentTime)}</span>
                <span>{formatTime(duration)}</span>
              </div>
            </div>
          </div>

          <audio
            ref={mergedAudioRef}
            preload="none"
            onTimeUpdate={(e) => handleMergedTimeUpdate(e.currentTarget.currentTime)}
            onLoadedMetadata={(e) => setDuration(e.currentTarget.duration)}
            onEnded={handleMergedEnded}
          />
        </motion.div>
      )}

      {/* 分句音频列表 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="glass-card overflow-hidden"
      >
        <div className="p-4 border-b border-cyber-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileAudio size={18} className="text-slate-400" />
            <h3 className="text-sm font-medium text-slate-300">分句音频 ({audioFiles.length})</h3>
          </div>
          <button
            onClick={() => {
              const timestamp = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 14)
              audioFileUrls.forEach((url, i) => {
                setTimeout(() => {
                  void handleDownload(url, `dialogue_${String(i + 1).padStart(3, '0')}_${timestamp}.mp3`)
                }, i * 200)
              })
            }}
            className="text-xs text-slate-400 hover:text-white transition-colors cursor-pointer"
          >
            全部下载
          </button>
        </div>

        <div 
          ref={listContainerRef}
          className="max-h-[500px] overflow-auto divide-y divide-cyber-border/50 scroll-smooth"
        >
          {audioFileUrls.map((url, index) => {
            const dialogue = dialogues[index]
            const isHighlighted = highlightIndex === index
            const isItemPlaying = playingItemIndex === index
            
            return (
              <AudioFileItem
                key={index}
                ref={(el) => {
                  if (el) {
                    itemRefs.current.set(index, el)
                  } else {
                    itemRefs.current.delete(index)
                  }
                }}
                url={url}
                index={index + 1}
                character={dialogue?.character}
                text={dialogue?.text}
                instruction={dialogue?.instruction}
                context={dialogue?.context}
                isHighlighted={isHighlighted}
                isPlaying={isItemPlaying}
                shouldStopPlaying={playingSource === 'merged' && playingMerged}
                charProgress={isHighlighted && playingSource === 'merged' ? charProgress : 0}
                onPlayStart={() => handleItemPlayStart(index)}
                onPlayEnd={() => handleItemPlayEnd(index)}
                onDownload={() => void handleDownload(url, generateTimestampFilename(`dialogue_${String(index + 1).padStart(3, '0')}`))}
              />
            )
          })}
        </div>
      </motion.div>
    </div>
  )
}

// ============================================================================
// HighlightedText 组件
// ============================================================================

interface HighlightedTextProps {
  text: string
  progress: number
}

function HighlightedText({ text, progress }: HighlightedTextProps) {
  const highlightedCount = Math.floor(text.length * Math.min(progress, 1))
  
  return (
    <span className="inline">
      <span className="text-neon-cyan font-medium">
        {text.slice(0, highlightedCount)}
      </span>
      {highlightedCount < text.length && (
        <span className="text-neon-cyan font-semibold animate-pulse">
          {text[highlightedCount]}
        </span>
      )}
      <span className="text-slate-500">
        {text.slice(highlightedCount + 1)}
      </span>
    </span>
  )
}

// ============================================================================
// AudioFileItem 组件
// ============================================================================

interface AudioFileItemProps {
  url: string
  index: number
  character?: string
  text?: string
  instruction?: string
  context?: string
  isHighlighted?: boolean
  isPlaying?: boolean
  shouldStopPlaying?: boolean
  charProgress?: number
  onPlayStart?: () => void
  onPlayEnd?: () => void
  onDownload: () => void
}

const AudioFileItem = forwardRef<HTMLDivElement, AudioFileItemProps>(
  function AudioFileItem(
    { 
      url, 
      index, 
      character, 
      text, 
      instruction, 
      context, 
      isHighlighted = false,
      shouldStopPlaying = false,
      charProgress = 0,
      onPlayStart,
      onPlayEnd,
      onDownload 
    },
    ref
  ) {
    const [isPlaying, setIsPlaying] = useState(false)
    const [isExpanded, setIsExpanded] = useState(false)
    const [localProgress, setLocalProgress] = useState(0)
    const audioRef = useRef<HTMLAudioElement>(null)
    const [playableUrl, setPlayableUrl] = useState<string | null>(null)
    const playableObjectUrlRef = useRef<string | null>(null)

    const runtimeBaseUrl = (import.meta.env.VITE_TTS_API_BASE_URL || '').trim().replace(/\/$/, '')
    const runtimeApiKey = (import.meta.env.VITE_TTS_API_KEY || '').trim()

    const cleanUrl = (u: string) => {
      const trimmed = u.trim()
      return trimmed.replace(/^`+/, '').replace(/`+$/, '').trim()
    }

    const needsAuthHeader = (u: string) => Boolean(runtimeApiKey && runtimeBaseUrl && cleanUrl(u).startsWith(runtimeBaseUrl))

    const revokePlayableObjectUrl = useCallback(() => {
      if (playableObjectUrlRef.current) {
        URL.revokeObjectURL(playableObjectUrlRef.current)
        playableObjectUrlRef.current = null
      }
    }, [])

    useEffect(() => {
      revokePlayableObjectUrl()
      setPlayableUrl(null)
      return () => {
        revokePlayableObjectUrl()
      }
    }, [revokePlayableObjectUrl, url])

    useEffect(() => {
      if (shouldStopPlaying && isPlaying && audioRef.current) {
        audioRef.current.pause()
        setIsPlaying(false)
        setLocalProgress(0)
      }
    }, [shouldStopPlaying, isPlaying])

    const handleTimeUpdate = () => {
      if (!audioRef.current) return
      const duration = audioRef.current.duration
      const currentTime = audioRef.current.currentTime
      if (duration > 0) {
        const progress = currentTime / duration
        setLocalProgress(progress)
      }
    }

    const togglePlay = async () => {
      if (!audioRef.current) return

      if (isPlaying) {
        audioRef.current.pause()
        setIsPlaying(false)
        onPlayEnd?.()
      } else {
        try {
          onPlayStart?.()
          const targetUrl = cleanUrl(url)

          let playable = targetUrl
          if (needsAuthHeader(targetUrl)) {
            if (!playableUrl) {
              const response = await fetch(targetUrl, {
                method: 'GET',
                headers: {
                  Authorization: `Bearer ${runtimeApiKey}`,
                },
              })
              if (!response.ok) {
                throw new Error(`音频请求失败: ${response.status}`)
              }
              const blob = await response.blob()
              const objectUrl = URL.createObjectURL(blob)
              revokePlayableObjectUrl()
              playableObjectUrlRef.current = objectUrl
              setPlayableUrl(objectUrl)
              playable = objectUrl
            } else {
              playable = playableUrl
            }
          }

          if (audioRef.current.src !== playable) {
            audioRef.current.pause()
            audioRef.current.src = playable
            audioRef.current.load()
          }
          await audioRef.current.play()
          setIsPlaying(true)
        } catch (err) {
          console.error('播放失败:', err)
          onPlayEnd?.()
        }
      }
    }

    const handleEnded = () => {
      setIsPlaying(false)
      setLocalProgress(0)
      onPlayEnd?.()
    }
    
    const effectiveProgress = isPlaying ? localProgress : (isHighlighted ? charProgress : 0)

    const parseInstruction = (inst?: string) => {
      if (!inst) return null
      const match = inst.match(/\[#(.+?)\]/)
      return match ? match[1] : inst
    }

    const parsedInstruction = parseInstruction(instruction)
    const hasExtraInfo = parsedInstruction || context

    return (
      <div 
        ref={ref}
        className={`
          transition-all duration-300 ease-out group
          ${isHighlighted 
            ? 'bg-gradient-to-r from-neon-cyan/15 via-neon-cyan/10 to-transparent border-l-2 border-neon-cyan' 
            : 'hover:bg-white/[0.02] border-l-2 border-transparent'
          }
        `}
      >
        <div className="flex items-center gap-4 p-4">
          {/* 序号 */}
          <div className={`
            flex-shrink-0 w-8 h-8 rounded-lg 
            flex items-center justify-center text-xs transition-all
            ${isHighlighted 
              ? 'bg-neon-cyan/20 text-neon-cyan' 
              : 'bg-cyber-card text-slate-500'
            }
          `}>
            {isPlaying || isHighlighted ? (
              <Volume2 size={14} className={isPlaying ? 'animate-pulse' : ''} />
            ) : (
              `#${index}`
            )}
          </div>

          {/* 播放按钮 */}
          <button
            onClick={togglePlay}
            className={`
              flex-shrink-0 w-8 h-8 rounded-full 
              flex items-center justify-center transition-colors cursor-pointer
              ${isPlaying 
                ? 'bg-neon-cyan text-cyber-bg' 
                : 'bg-cyber-card text-slate-400 hover:bg-neon-cyan/20 hover:text-neon-cyan'
              }
            `}
          >
            {isPlaying ? <Pause size={14} /> : <Play size={14} />}
          </button>

          {/* 内容 */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className={`
                text-sm font-medium transition-colors
                ${isHighlighted ? 'text-neon-cyan' : 'text-neon-purple'}
              `}>
                {character || '未知'}
              </span>
              {parsedInstruction && (
                <span className={`
                  inline-flex items-center gap-1 px-2 py-0.5 
                  text-[10px] rounded-full border transition-colors
                  ${isHighlighted 
                    ? 'bg-amber-500/20 text-amber-300 border-amber-500/30' 
                    : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                  }
                `}>
                  <Sparkles size={10} />
                  {parsedInstruction.length > 20 ? parsedInstruction.slice(0, 20) + '...' : parsedInstruction}
                </span>
              )}
            </div>
            {text && (
              <p className={`
                text-xs mt-1 line-clamp-2 transition-colors leading-relaxed
                ${isHighlighted ? 'text-slate-300' : 'text-slate-400'}
              `}>
                {(isHighlighted || isPlaying) && effectiveProgress > 0 ? (
                  <HighlightedText text={text} progress={effectiveProgress} />
                ) : (
                  text
                )}
              </p>
            )}
          </div>

          {/* 展开按钮 */}
          {hasExtraInfo && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="flex-shrink-0 p-2 text-slate-500 hover:text-white 
                       hover:bg-white/5 rounded-lg transition-all cursor-pointer"
            >
              {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </button>
          )}

          {/* 下载按钮 */}
          <button
            onClick={onDownload}
            className="flex-shrink-0 p-2 text-transparent group-hover:text-slate-400 
                     hover:!text-white hover:bg-white/5 rounded-lg transition-all cursor-pointer"
          >
            <Download size={14} />
          </button>

          <audio
            ref={audioRef}
            preload="none"
            onTimeUpdate={handleTimeUpdate}
            onEnded={handleEnded}
          />
        </div>

        {/* 展开详情 */}
        <AnimatePresence>
          {isExpanded && hasExtraInfo && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="overflow-hidden"
            >
              <div className="px-4 pb-4 pt-0 ml-12 space-y-3">
                {parsedInstruction && (
                  <div className="flex items-start gap-2">
                    <div className="flex-shrink-0 w-6 h-6 rounded-md bg-amber-500/10 
                                  flex items-center justify-center mt-0.5">
                      <Sparkles size={12} className="text-amber-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[10px] text-slate-500 mb-0.5">情绪/语气</p>
                      <p className="text-xs text-amber-300/90 leading-relaxed">
                        {parsedInstruction}
                      </p>
                    </div>
                  </div>
                )}

                {context && (
                  <div className="flex items-start gap-2">
                    <div className="flex-shrink-0 w-6 h-6 rounded-md bg-neon-cyan/10 
                                  flex items-center justify-center mt-0.5">
                      <BookOpen size={12} className="text-neon-cyan" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[10px] text-slate-500 mb-0.5">场景上下文</p>
                      <p className="text-xs text-neon-cyan/80 leading-relaxed">
                        {context}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    )
  }
)
