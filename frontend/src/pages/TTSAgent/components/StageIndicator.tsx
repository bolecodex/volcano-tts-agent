/**
 * 阶段指示器组件
 * 
 * 显示当前处于哪个阶段：
 * 1. 对话分析
 * 2. 音色匹配  
 * 3. 语音合成
 */

import { motion } from 'framer-motion'
import { MessageSquare, Users, Volume2, ChevronRight } from 'lucide-react'
import type { Stage, SessionStatus } from '@/types'

interface StageIndicatorProps {
  currentStage: Stage
  status?: SessionStatus
}

const stages = [
  { stage: 1, icon: MessageSquare, label: '对话分析', color: 'neon-cyan' },
  { stage: 2, icon: Users, label: '音色匹配', color: 'neon-purple' },
  { stage: 3, icon: Volume2, label: '语音合成', color: 'neon-green' },
] as const

export default function StageIndicator({ currentStage, status }: StageIndicatorProps) {
  // 判断某个阶段是否在进行中
  const isProcessing = (stage: number) => {
    if (stage === 1 && status === 'analyzing') return true
    if (stage === 2 && status === 'matching') return true
    if (stage === 3 && status === 'synthesizing') return true
    return false
  }

  return (
    <div className="flex items-center justify-center gap-2 py-4">
      {stages.map((stageItem, index) => {
        const isActive = stageItem.stage === currentStage
        const isCompleted = stageItem.stage < currentStage
        const processing = isProcessing(stageItem.stage)
        const StageIcon = stageItem.icon
        
        return (
          <div key={stageItem.stage} className="flex items-center">
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: index * 0.1 }}
              className={`relative flex flex-col items-center gap-2 ${isActive ? 'scale-105' : ''}`}
            >
              {/* 图标容器 */}
              <motion.div
                animate={processing ? { scale: [1, 1.05, 1] } : {}}
                transition={processing ? { duration: 1.5, repeat: Infinity } : {}}
                className={`
                  relative flex items-center justify-center w-12 h-12 rounded-xl
                  transition-all duration-300
                  ${isActive 
                    ? `bg-gradient-to-br from-${stageItem.color}/30 to-${stageItem.color}/10 border-2 border-${stageItem.color}/50` 
                    : isCompleted 
                      ? 'bg-gradient-to-br from-neon-green/30 to-neon-green/10 border-2 border-neon-green/50'
                      : 'bg-cyber-card border border-cyber-border'
                  }
                `}
              >
                {/* 活跃状态的光晕效果 */}
                {isActive && (
                  <motion.div
                    className={`absolute inset-0 rounded-xl bg-gradient-to-br from-${stageItem.color}/20 to-transparent`}
                    animate={{ opacity: [0.5, 1, 0.5] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  />
                )}
                
                {/* 处理中的脉冲效果 */}
                {processing && (
                  <motion.div
                    className="absolute inset-0 rounded-xl border-2 border-neon-cyan"
                    animate={{ scale: [1, 1.2], opacity: [1, 0] }}
                    transition={{ duration: 1, repeat: Infinity }}
                  />
                )}
                
                <StageIcon className={`
                  w-5 h-5 relative z-10
                  ${isActive 
                    ? stageItem.color === 'neon-cyan' ? 'text-neon-cyan' 
                      : stageItem.color === 'neon-purple' ? 'text-neon-purple' 
                      : 'text-neon-green'
                    : isCompleted ? 'text-neon-green' : 'text-slate-500'}
                `} />
              </motion.div>
              
              {/* 阶段标签 */}
              <span className={`
                text-xs font-medium whitespace-nowrap
                ${isActive 
                  ? stageItem.color === 'neon-cyan' ? 'text-neon-cyan' 
                    : stageItem.color === 'neon-purple' ? 'text-neon-purple' 
                    : 'text-neon-green'
                  : isCompleted ? 'text-neon-green' : 'text-slate-500'}
              `}>
                {stageItem.label}
              </span>
            </motion.div>
            
            {/* 连接线 */}
            {index < stages.length - 1 && (
              <div className="flex items-center mx-2 mb-6">
                <div className={`
                  w-12 h-0.5 rounded-full transition-all duration-500
                  ${stageItem.stage < currentStage 
                    ? 'bg-gradient-to-r from-neon-green to-neon-green' 
                    : 'bg-cyber-border'
                  }
                `} />
                <ChevronRight className={`
                  w-4 h-4 -ml-1
                  ${stageItem.stage < currentStage ? 'text-neon-green' : 'text-cyber-border'}
                `} />
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
