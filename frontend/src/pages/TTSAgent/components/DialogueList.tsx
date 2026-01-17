/**
 * 对话列表组件
 * 
 * 功能：
 * - 显示分析后的对话列表
 * - 支持编辑对话内容
 * - 显示角色、情绪指令等信息
 */

import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  MessageSquare, 
  Edit3, 
  Check, 
  X,
  Sparkles,
} from 'lucide-react'
import type { DialogueItem } from '@/types'

interface DialogueListProps {
  dialogues: DialogueItem[]
  onUpdate?: (dialogues: DialogueItem[]) => void
  editable?: boolean
}

export default function DialogueList({ 
  dialogues, 
  onUpdate, 
  editable = true 
}: DialogueListProps) {
  const [editingIndex, setEditingIndex] = useState<number | null>(null)
  const [editText, setEditText] = useState('')
  const [editCharacter, setEditCharacter] = useState('')
  const [editInstruction, setEditInstruction] = useState('')

  const handleEdit = (index: number) => {
    setEditingIndex(index)
    setEditText(dialogues[index].text)
    setEditCharacter(dialogues[index].character)
    setEditInstruction(dialogues[index].instruction || '')
  }

  const handleSave = () => {
    if (editingIndex !== null && onUpdate) {
      const updated = dialogues.map((d, i) => 
        i === editingIndex ? { 
          ...d, 
          text: editText,
          character: editCharacter,
          instruction: editInstruction || undefined
        } : d
      )
      onUpdate(updated)
    }
    setEditingIndex(null)
    setEditText('')
    setEditCharacter('')
    setEditInstruction('')
  }

  const handleCancel = () => {
    setEditingIndex(null)
    setEditText('')
    setEditCharacter('')
    setEditInstruction('')
  }

  // 解析 instruction 中的情绪标签
  const parseInstruction = (inst?: string) => {
    if (!inst) return null
    const match = inst.match(/\[#(.+?)\]/)
    return match ? match[1] : inst
  }

  if (dialogues.length === 0) {
    return (
      <div className="text-center py-12 text-slate-500">
        暂无对话内容
      </div>
    )
  }

  return (
    <div className="glass-card p-6">
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-gradient-to-br from-neon-green/20 to-neon-green/5 rounded-xl border border-neon-green/20">
            <MessageSquare className="w-5 h-5 text-neon-green" />
          </div>
          <div>
            <h3 className="font-heading font-semibold text-white">对话列表</h3>
            <p className="text-sm text-slate-500">{dialogues.length} 条对话</p>
          </div>
        </div>
      </div>
      
      <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2">
        {dialogues.map((item, index) => {
          const isEditing = editingIndex === index
          const parsedInstruction = parseInstruction(item.instruction)
          
          return (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.03 }}
              className="p-4 bg-cyber-bg/50 rounded-xl border border-cyber-border/50 
                       hover:border-neon-cyan/20 transition-colors group"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="px-2.5 py-1 bg-gradient-to-r from-neon-cyan/20 to-neon-purple/20 
                                 text-neon-cyan text-xs font-medium rounded-lg border border-neon-cyan/20">
                    {item.character}
                  </span>
                  {parsedInstruction && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 
                                   bg-amber-500/10 text-amber-400 text-[10px] rounded-full 
                                   border border-amber-500/20">
                      <Sparkles size={10} />
                      {parsedInstruction.length > 15 ? parsedInstruction.slice(0, 15) + '...' : parsedInstruction}
                    </span>
                  )}
                </div>
                
                {/* 编辑按钮 */}
                {editable && !isEditing && (
                  <button
                    onClick={() => handleEdit(index)}
                    className="opacity-0 group-hover:opacity-100 p-1.5 text-slate-500 
                             hover:text-neon-cyan hover:bg-neon-cyan/10 rounded-lg 
                             transition-all cursor-pointer"
                  >
                    <Edit3 size={14} />
                  </button>
                )}
              </div>
              
              {isEditing ? (
                <div className="space-y-3">
                  {/* 角色名称编辑 */}
                  <div className="flex items-center gap-2">
                    <label className="text-xs text-slate-500 w-16 shrink-0">角色</label>
                    <input
                      type="text"
                      value={editCharacter}
                      onChange={(e) => setEditCharacter(e.target.value)}
                      className="flex-1 px-3 py-1.5 bg-cyber-bg border border-neon-cyan/30 rounded-lg
                               text-slate-300 text-sm
                               focus:outline-none focus:border-neon-cyan/50"
                      placeholder="角色名称"
                    />
                  </div>
                  
                  {/* 情绪指令编辑 */}
                  <div className="flex items-center gap-2">
                    <label className="text-xs text-slate-500 w-16 shrink-0">情绪</label>
                    <input
                      type="text"
                      value={editInstruction}
                      onChange={(e) => setEditInstruction(e.target.value)}
                      className="flex-1 px-3 py-1.5 bg-cyber-bg border border-amber-500/30 rounded-lg
                               text-slate-300 text-sm
                               focus:outline-none focus:border-amber-500/50"
                      placeholder="情绪指令，如：用温和的语气..."
                    />
                  </div>
                  
                  {/* 对话内容编辑 */}
                  <div className="flex items-start gap-2">
                    <label className="text-xs text-slate-500 w-16 shrink-0 pt-2">内容</label>
                    <textarea
                      value={editText}
                      onChange={(e) => setEditText(e.target.value)}
                      className="flex-1 p-3 bg-cyber-bg border border-neon-cyan/30 rounded-lg
                               text-slate-300 text-sm leading-relaxed resize-none
                               focus:outline-none focus:border-neon-cyan/50"
                      rows={3}
                      autoFocus
                    />
                  </div>
                  
                  <div className="flex justify-end gap-2">
                    <button
                      onClick={handleCancel}
                      className="px-3 py-1.5 text-xs text-slate-400 hover:text-white 
                               hover:bg-white/5 rounded-lg transition-colors cursor-pointer"
                    >
                      <X size={14} className="inline mr-1" />
                      取消
                    </button>
                    <button
                      onClick={handleSave}
                      className="px-3 py-1.5 text-xs text-neon-cyan bg-neon-cyan/10 
                               hover:bg-neon-cyan/20 rounded-lg transition-colors cursor-pointer"
                    >
                      <Check size={14} className="inline mr-1" />
                      保存
                    </button>
                  </div>
                </div>
              ) : (
                <p className="text-slate-300 leading-relaxed text-sm">{item.text}</p>
              )}
              
              {/* 上下文信息 */}
              {item.context && (
                <p className="mt-2 text-xs text-slate-500 italic">
                  场景：{item.context}
                </p>
              )}
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}
