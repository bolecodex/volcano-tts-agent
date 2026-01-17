/**
 * 会话列表组件
 * 
 * 功能：
 * - 显示会话列表
 * - 状态图标显示
 * - 友好的时间显示
 * - 刷新和删除功能
 */

import { motion } from 'framer-motion'
import {
  Clock,
  Trash2,
  RefreshCw,
  MessageSquare,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Mic,
} from 'lucide-react'
import type { SessionListItem, SessionStatus } from '@/types'

interface SessionListProps {
  sessions: SessionListItem[]
  currentSessionId?: string
  isLoading: boolean
  onSelect: (sessionId: string) => void
  onDelete: (sessionId: string) => void
  onRefresh: () => void
}

export default function SessionList({
  sessions,
  currentSessionId,
  isLoading,
  onSelect,
  onDelete,
  onRefresh,
}: SessionListProps) {
  // 格式化时间
  const formatTime = (timeStr?: string): string => {
    if (!timeStr) return ''
    try {
      const date = new Date(timeStr)
      const now = new Date()
      const diffMs = now.getTime() - date.getTime()
      const diffMins = Math.floor(diffMs / (1000 * 60))
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
      const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

      if (diffMins < 1) return '刚刚'
      if (diffMins < 60) return `${diffMins}分钟前`
      if (diffHours < 24) return `${diffHours}小时前`
      if (diffDays < 7) return `${diffDays}天前`

      return date.toLocaleDateString('zh-CN', {
        month: 'short',
        day: 'numeric',
      })
    } catch {
      return ''
    }
  }

  // 获取状态图标和颜色
  const getStatusInfo = (status: SessionStatus) => {
    switch (status) {
      case 'completed':
        return {
          icon: <CheckCircle2 size={12} />,
          color: 'text-neon-green',
          bg: 'bg-neon-green/10',
          label: '已完成',
        }
      case 'error':
        return {
          icon: <AlertCircle size={12} />,
          color: 'text-red-400',
          bg: 'bg-red-500/10',
          label: '错误',
        }
      case 'analyzing':
      case 'matching':
      case 'synthesizing':
        return {
          icon: <Loader2 size={12} className="animate-spin" />,
          color: 'text-neon-cyan',
          bg: 'bg-neon-cyan/10',
          label: status === 'analyzing' ? '分析中' : status === 'matching' ? '匹配中' : '合成中',
        }
      case 'dialogue_ready':
        return {
          icon: <MessageSquare size={12} />,
          color: 'text-neon-green',
          bg: 'bg-neon-green/10',
          label: '对话就绪',
        }
      case 'voice_ready':
        return {
          icon: <Mic size={12} />,
          color: 'text-neon-purple',
          bg: 'bg-neon-purple/10',
          label: '音色就绪',
        }
      default:
        return {
          icon: <MessageSquare size={12} />,
          color: 'text-slate-400',
          bg: 'bg-slate-500/10',
          label: '草稿',
        }
    }
  }

  // 截取输入文本
  const truncateInput = (input?: string, maxLen = 30): string => {
    if (!input) return '新会话'
    return input.length > maxLen ? input.slice(0, maxLen) + '...' : input
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* 标题栏 */}
      <div className="px-4 py-3 flex items-center justify-between border-b border-cyber-border">
        <span className="text-xs text-slate-500">
          {sessions.length} 个会话
        </span>
        <button
          onClick={onRefresh}
          disabled={isLoading}
          className="p-1.5 text-slate-500 hover:text-neon-cyan hover:bg-neon-cyan/10 
                   rounded-lg transition-colors cursor-pointer disabled:opacity-50"
        >
          <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
        </button>
      </div>

      {/* 会话列表 */}
      <div className="flex-1 overflow-auto p-2">
        {isLoading && sessions.length === 0 ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 size={20} className="text-neon-cyan animate-spin" />
          </div>
        ) : sessions.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="p-4 bg-cyber-card rounded-2xl border border-cyber-border mb-4">
              <Mic className="w-10 h-10 text-slate-600" />
            </div>
            <p className="text-sm text-slate-500">暂无会话</p>
            <p className="text-xs text-slate-600 mt-1">点击上方按钮创建</p>
          </div>
        ) : (
          <div className="space-y-1">
            {sessions.map((session, index) => {
              const statusInfo = getStatusInfo(session.status)
              const isActive = session.session_id === currentSessionId

              return (
                <motion.div
                  key={session.session_id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.03 }}
                  whileHover={{ x: 2 }}
                  onClick={() => onSelect(session.session_id)}
                  className={`group p-3 rounded-xl cursor-pointer transition-all ${
                    isActive
                      ? 'bg-gradient-to-r from-neon-cyan/10 to-neon-purple/10 border border-neon-cyan/30'
                      : 'bg-cyber-card/50 border border-transparent hover:border-cyber-border hover:bg-cyber-card'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    {/* 状态图标 */}
                    <div className={`flex-shrink-0 w-8 h-8 rounded-lg ${statusInfo.bg} 
                                   flex items-center justify-center ${statusInfo.color}`}>
                      {statusInfo.icon}
                    </div>

                    {/* 内容 */}
                    <div className="flex-1 min-w-0">
                      <h4 className={`text-sm truncate ${
                        isActive ? 'text-neon-cyan' : 'text-slate-300'
                      }`}>
                        {truncateInput(session.user_input)}
                      </h4>
                      <div className="flex items-center gap-2 mt-1">
                        <span className={`text-xs ${statusInfo.color}`}>
                          {statusInfo.label}
                        </span>
                        {session.dialogue_count && session.dialogue_count > 0 && (
                          <>
                            <span className="text-slate-700">•</span>
                            <span className="text-xs text-slate-600">
                              {session.dialogue_count} 条
                            </span>
                          </>
                        )}
                      </div>
                      <div className="flex items-center gap-1 mt-1 text-xs text-slate-600">
                        <Clock size={10} />
                        {formatTime(session.updated_at || session.created_at)}
                      </div>
                    </div>

                    {/* 删除按钮 */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        if (confirm('确定删除此会话?')) {
                          onDelete(session.session_id)
                        }
                      }}
                      className="flex-shrink-0 p-1.5 text-transparent group-hover:text-red-400/60 
                               hover:!text-red-400 hover:bg-red-500/10 rounded-lg transition-all cursor-pointer"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </motion.div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
