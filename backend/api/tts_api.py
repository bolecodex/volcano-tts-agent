# -*- coding: utf-8 -*-
"""
TTS Agent API 路由

提供 TTS 相关的 RESTful API 接口
"""

import os
import uuid
import json
import asyncio
import logging
from typing import Optional, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, HTTPException, Query, Response, Body
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, Field

from backend.models import SessionStatus, init_database
from agent import (
    TTSPipelineController,
    create_tts_pipeline,
    TTSSessionService,
    format_all_voices_brief,
    get_voice_by_id,
    get_voices_by_category,
    ALL_VOICES,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# 线程池，用于运行同步的 LLM 调用
_executor = ThreadPoolExecutor(max_workers=4)

# 全局 pipeline 缓存
_pipeline_cache: Dict[str, TTSPipelineController] = {}


def _get_or_create_pipeline(session_id: Optional[str] = None) -> TTSPipelineController:
    """获取或创建 pipeline"""
    if session_id and session_id in _pipeline_cache:
        return _pipeline_cache[session_id]
    
    pipeline = create_tts_pipeline(session_id=session_id, persist=True)
    _pipeline_cache[pipeline.session_id] = pipeline
    return pipeline


# ============================================================================
#                              请求模型
# ============================================================================

class CreateSessionRequest(BaseModel):
    """创建会话请求"""
    user_input: Optional[str] = None
    project_id: Optional[int] = None


class AnalyzeRequest(BaseModel):
    """对话分析请求"""
    user_input: str


class RefineRequest(BaseModel):
    """对话修改请求"""
    instruction: str
    target_indices: Optional[List[int]] = None


class UpdateDialogueRequest(BaseModel):
    """更新对话列表请求"""
    dialogue_list: List[Dict[str, Any]]


class ChangeVoiceRequest(BaseModel):
    """更换音色请求"""
    character: str
    voice_id: str
    voice_name: Optional[str] = ""


class RematchRequest(BaseModel):
    """重新匹配音色请求"""
    instruction: str
    target_characters: Optional[List[str]] = None


# ============================================================================
#                              会话管理 API
# ============================================================================

@router.post("/sessions")
async def create_session(request: CreateSessionRequest = Body(default=CreateSessionRequest())):
    """创建新的 TTS 会话"""
    try:
        pipeline = create_tts_pipeline(persist=True)
        _pipeline_cache[pipeline.session_id] = pipeline
        
        return {
            "success": True,
            "session_id": pipeline.session_id,
            "status": pipeline.status.value,
        }
    except Exception as e:
        logger.exception("创建会话失败")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def list_sessions(
    limit: int = Query(default=50, ge=1, le=200),
    status: Optional[str] = None,
):
    """列出所有会话"""
    try:
        service = TTSSessionService()
        sessions = service.list_sessions(status=status, limit=limit)
        return {"success": True, "sessions": sessions}
    except Exception as e:
        logger.exception("列出会话失败")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """获取会话详情"""
    try:
        pipeline = _get_or_create_pipeline(session_id)
        return {"success": True, "data": pipeline.to_dict()}
    except Exception as e:
        logger.exception(f"获取会话失败: {session_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    try:
        service = TTSSessionService()
        success = service.delete_session(session_id)
        
        if session_id in _pipeline_cache:
            del _pipeline_cache[session_id]
        
        return {"success": success}
    except Exception as e:
        logger.exception(f"删除会话失败: {session_id}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
#                              阶段一：对话分析 API
# ============================================================================

@router.post("/sessions/{session_id}/analyze")
async def analyze_dialogue(session_id: str, request: AnalyzeRequest):
    """阶段一：分析对话（非流式）"""
    try:
        pipeline = _get_or_create_pipeline(session_id)
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            _executor,
            lambda: asyncio.run(pipeline.stage1_analyze(request.user_input))
        )
        
        return result
    except Exception as e:
        logger.exception(f"分析失败: {session_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/analyze/stream")
async def analyze_dialogue_stream(session_id: str, request: AnalyzeRequest):
    """阶段一：分析对话（流式输出）"""
    try:
        pipeline = _get_or_create_pipeline(session_id)
        
        async def generate():
            chunks = []
            
            def on_chunk(chunk: str):
                chunks.append(chunk)
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                _executor,
                lambda: asyncio.run(pipeline.stage1_analyze(request.user_input, on_chunk=on_chunk))
            )
            
            # 流式发送所有收集的 chunks
            for chunk in chunks:
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
            
            yield f"data: {json.dumps({'type': 'result', 'data': result})}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
    except Exception as e:
        logger.exception(f"流式分析失败: {session_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/refine")
async def refine_dialogue(session_id: str, request: RefineRequest):
    """阶段一：对话式修改"""
    try:
        pipeline = _get_or_create_pipeline(session_id)
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            _executor,
            lambda: asyncio.run(
                pipeline.stage1_refine(request.instruction, request.target_indices)
            )
        )
        
        return result
    except Exception as e:
        logger.exception(f"修改失败: {session_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/sessions/{session_id}/dialogues")
async def update_dialogues(session_id: str, request: UpdateDialogueRequest):
    """阶段一：手动更新对话列表"""
    try:
        pipeline = _get_or_create_pipeline(session_id)
        result = pipeline.stage1_update(request.dialogue_list)
        return result
    except Exception as e:
        logger.exception(f"更新失败: {session_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/confirm-stage1")
async def confirm_stage1(session_id: str):
    """确认阶段一完成"""
    try:
        pipeline = _get_or_create_pipeline(session_id)
        
        if not pipeline.dialogue_list:
            return {"success": False, "error": "对话列表为空"}
        
        pipeline._update_status(SessionStatus.DIALOGUE_READY)
        
        return {
            "success": True,
            "session_id": session_id,
            "status": pipeline.status.value,
        }
    except Exception as e:
        logger.exception(f"确认阶段一失败: {session_id}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
#                              阶段二：音色匹配 API
# ============================================================================

@router.post("/sessions/{session_id}/match")
async def match_voices(session_id: str):
    """阶段二：匹配音色"""
    try:
        pipeline = _get_or_create_pipeline(session_id)
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            _executor,
            lambda: asyncio.run(pipeline.stage2_match())
        )
        
        return result
    except Exception as e:
        logger.exception(f"匹配失败: {session_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/match/stream")
async def match_voices_stream(session_id: str):
    """阶段二：匹配音色（流式输出）"""
    try:
        pipeline = _get_or_create_pipeline(session_id)
        
        async def generate():
            chunks = []
            
            def on_chunk(chunk: str):
                chunks.append(chunk)
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                _executor,
                lambda: asyncio.run(pipeline.stage2_match(on_chunk=on_chunk))
            )
            
            for chunk in chunks:
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
            
            yield f"data: {json.dumps({'type': 'result', 'data': result})}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
    except Exception as e:
        logger.exception(f"流式匹配失败: {session_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/rematch")
async def rematch_voices(session_id: str, request: RematchRequest):
    """阶段二：对话式重新匹配"""
    try:
        pipeline = _get_or_create_pipeline(session_id)
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            _executor,
            lambda: asyncio.run(
                pipeline.stage2_rematch(request.instruction, request.target_characters)
            )
        )
        
        return result
    except Exception as e:
        logger.exception(f"重新匹配失败: {session_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/change-voice")
async def change_voice(session_id: str, request: ChangeVoiceRequest):
    """阶段二：手动更换角色音色"""
    try:
        pipeline = _get_or_create_pipeline(session_id)
        result = pipeline.stage2_change_voice(
            request.character,
            request.voice_id,
            request.voice_name or "",
        )
        return result
    except Exception as e:
        logger.exception(f"更换音色失败: {session_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/confirm-stage2")
async def confirm_stage2(session_id: str):
    """确认阶段二完成"""
    try:
        pipeline = _get_or_create_pipeline(session_id)
        
        if not pipeline.voice_mapping:
            return {"success": False, "error": "音色映射为空"}
        
        pipeline._update_status(SessionStatus.VOICE_READY)
        
        return {
            "success": True,
            "session_id": session_id,
            "status": pipeline.status.value,
        }
    except Exception as e:
        logger.exception(f"确认阶段二失败: {session_id}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
#                              阶段三：批量合成 API
# ============================================================================

@router.post("/sessions/{session_id}/synthesize")
async def synthesize_audio(session_id: str):
    """阶段三：批量合成音频"""
    try:
        pipeline = _get_or_create_pipeline(session_id)
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            _executor,
            lambda: asyncio.run(pipeline.stage3_synthesize())
        )
        
        return result
    except Exception as e:
        logger.exception(f"合成失败: {session_id}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
#                              音频文件下载 API
# ============================================================================

@router.get("/audio/{session_id}/{filename}")
async def get_audio_file(session_id: str, filename: str):
    """获取音频文件"""
    try:
        pipeline = _get_or_create_pipeline(session_id)
        file_path = os.path.join(pipeline.output_dir, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return FileResponse(
            file_path,
            media_type="audio/mpeg",
            filename=filename,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"获取音频文件失败: {session_id}/{filename}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/merged-audio")
async def get_merged_audio(session_id: str):
    """获取合并后的音频"""
    try:
        pipeline = _get_or_create_pipeline(session_id)
        
        if not pipeline.merged_audio:
            raise HTTPException(status_code=404, detail="合并音频不存在")
        
        if not os.path.exists(pipeline.merged_audio):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return FileResponse(
            pipeline.merged_audio,
            media_type="audio/mpeg",
            filename="dialogue_full.mp3",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"获取合并音频失败: {session_id}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
#                              音色查询 API
# ============================================================================

@router.get("/voices")
async def list_voices(
    category: Optional[str] = None,
    gender: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
):
    """获取可用音色列表"""
    try:
        voices = ALL_VOICES
        
        if category:
            voices = get_voices_by_category(category)
        
        if gender:
            voices = [v for v in voices if v.get("gender") == gender]
        
        return {
            "success": True,
            "voices": voices[:limit],
            "total": len(voices),
        }
    except Exception as e:
        logger.exception("获取音色列表失败")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voices/{voice_id}")
async def get_voice_detail(voice_id: str):
    """获取音色详情"""
    try:
        voice = get_voice_by_id(voice_id)
        if not voice:
            raise HTTPException(status_code=404, detail="音色不存在")
        
        return {"success": True, "voice": voice}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"获取音色详情失败: {voice_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voice-categories")
async def get_voice_categories():
    """获取音色分类"""
    categories = [
        {"id": "female_2.0", "name": "女声 2.0", "count": 10},
        {"id": "male_2.0", "name": "男声 2.0", "count": 10},
        {"id": "female_emotion", "name": "女声多情感", "count": 10},
        {"id": "male_emotion", "name": "男声多情感", "count": 10},
        {"id": "roleplay", "name": "角色扮演", "count": 10},
    ]
    return {"success": True, "categories": categories}


# ============================================================================
#                              试听 API
# ============================================================================

@router.post("/preview")
async def preview_voice(
    voice_id: str = Body(...),
    text: str = Body(default="你好，这是一段试听文本。"),
):
    """试听音色"""
    try:
        from agent.tools import tts_preview
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            _executor,
            lambda: tts_preview.invoke({"text": text, "voice_id": voice_id})
        )
        
        if result.get("success") and result.get("audio_path"):
            return FileResponse(
                result["audio_path"],
                media_type="audio/mpeg",
                filename="preview.mp3",
            )
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "合成失败"))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"试听失败: {voice_id}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
#                              健康检查
# ============================================================================

@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "service": "tts-agent"}
