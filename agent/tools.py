# -*- coding: utf-8 -*-
"""
🎤 TTS Agent 工具包

提供 LangChain Tool 格式的 TTS 工具
"""

import os
import uuid
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any

os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")
os.environ.setdefault("LANGSMITH_TRACING", "false")

try:
    from langchain_core.tools import tool
except ImportError:
    def tool(func=None, **_kwargs):
        def decorator(f):
            return f
        return decorator if func is None else decorator(func)

from dotenv import load_dotenv
load_dotenv()


# 默认输出目录
DEFAULT_OUTPUT_DIR = os.path.join(tempfile.gettempdir(), "tts_agent_output")
os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)


def _get_resource_id(voice_id: str) -> str:
    """根据音色 ID 自动选择正确的资源 ID"""
    voice_lower = voice_id.lower()
    
    if voice_lower.startswith("icl_"):
        return "seed-icl-1.0"
    
    if "uranus" in voice_lower:
        return "seed-tts-2.0"
    
    if voice_lower.startswith("saturn_"):
        return "seed-tts-2.0"
    
    if "_saturn_bigtts" in voice_lower:
        return "seed-tts-2.0"
    
    return "seed-tts-1.0"


def _get_tts_service(voice_id: str = None):
    """延迟导入 TTS 服务"""
    from backend.services import DoubaoTTSService
    from backend.models import TTSConfig
    
    resource_id = _get_resource_id(voice_id) if voice_id else "seed-tts-1.0"
    return DoubaoTTSService(resource_id=resource_id), TTSConfig


@tool
def tts_preview(
    text: str,
    voice_id: str,
    output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    TTS 试听工具 - 生成单句语音试听音频
    
    Args:
        text: 要合成的文本
        voice_id: 音色ID
        output_dir: 输出目录
    
    Returns:
        包含 success, audio_path, duration_ms, error 的字典
    """
    try:
        service, TTSConfig = _get_tts_service(voice_id)
        config = TTSConfig(voice_type=voice_id)
        
        out_dir = output_dir or DEFAULT_OUTPUT_DIR
        os.makedirs(out_dir, exist_ok=True)
        
        filename = f"preview_{uuid.uuid4().hex[:8]}.mp3"
        output_path = os.path.join(out_dir, filename)
        
        result = service.synthesize_auto(text=text, config=config, output_path=output_path)
        
        if result.success:
            return {
                "success": True,
                "audio_path": result.audio_path or output_path,
                "duration_ms": result.duration_ms,
            }
        else:
            return {"success": False, "error": result.error_message or "合成失败"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def tts_synthesize(
    text: str,
    voice_id: str,
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    TTS 合成工具 - 合成单句语音音频
    
    Args:
        text: 要合成的文本
        voice_id: 音色ID
        output_path: 输出文件路径
    
    Returns:
        包含 success, audio_path, duration_ms, error 的字典
    """
    try:
        service, TTSConfig = _get_tts_service(voice_id)
        config = TTSConfig(voice_type=voice_id)
        
        if not output_path:
            os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
            filename = f"synth_{uuid.uuid4().hex[:8]}.mp3"
            output_path = os.path.join(DEFAULT_OUTPUT_DIR, filename)
        
        result = service.synthesize_auto(text=text, config=config, output_path=output_path)
        
        if result.success:
            return {
                "success": True,
                "audio_path": result.audio_path or output_path,
                "duration_ms": result.duration_ms,
            }
        else:
            return {"success": False, "error": result.error_message or "合成失败"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def tts_synthesize_batch(
    items: List[Dict[str, Any]],
    output_dir: Optional[str] = None,
    use_multi_turn: bool = True,
    context_window: int = 3,
) -> Dict[str, Any]:
    """
    TTS 批量合成工具 - 批量合成多句语音音频
    
    Args:
        items: 合成项列表
        output_dir: 输出目录
        use_multi_turn: 是否启用多轮上下文
        context_window: 上下文窗口大小
    
    Returns:
        包含 success, results, total, succeeded, failed 的字典
    """
    try:
        out_dir = output_dir or DEFAULT_OUTPUT_DIR
        os.makedirs(out_dir, exist_ok=True)
        
        if use_multi_turn:
            return _synthesize_batch_multi_turn(items, out_dir)
        else:
            return _synthesize_batch_legacy(items, out_dir)
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "total": len(items),
            "succeeded": 0,
            "failed": len(items),
        }


def _synthesize_batch_multi_turn(items: List[Dict[str, Any]], out_dir: str) -> Dict[str, Any]:
    """使用 MultiTurnTTSSession 进行批量合成"""
    from backend.services import DoubaoTTSService, MultiTurnTTSSession
    
    tts = DoubaoTTSService()
    session = MultiTurnTTSSession(tts, output_dir=out_dir)
    
    results = []
    succeeded = 0
    failed = 0
    
    for i, item in enumerate(items):
        text = item.get("text", "")
        voice_id = item.get("voice_id", "")
        instruction = item.get("instruction", "")
        emotion = item.get("emotion")
        emotion_scale = item.get("emotion_scale")
        filename = item.get("filename", f"dialogue_{i+1:03d}.mp3")
        reset_context = item.get("reset_context", False)
        
        if not text or not voice_id:
            results.append({
                "index": i,
                "success": False,
                "error": "缺少必要参数 text 或 voice_id",
            })
            failed += 1
            continue
        
        if reset_context:
            session.reset_context()
        
        emotion_instruction = _build_emotion_instruction(instruction) if instruction else None
        
        result = session.synthesize(
            text=text,
            voice_type=voice_id,
            emotion_instruction=emotion_instruction,
            emotion=emotion,
            emotion_scale=emotion_scale,
            output_filename=filename,
        )
        
        if result.success:
            results.append({
                "index": i,
                "success": True,
                "audio_path": result.audio_path,
                "duration_ms": result.duration_ms,
            })
            succeeded += 1
        else:
            results.append({
                "index": i,
                "success": False,
                "error": result.error_message or "合成失败",
            })
            failed += 1
    
    return {
        "success": failed == 0,
        "results": results,
        "total": len(items),
        "succeeded": succeeded,
        "failed": failed,
        "output_dir": out_dir,
        "context_depth": session.v2_context_depth,
    }


def _synthesize_batch_legacy(items: List[Dict[str, Any]], out_dir: str) -> Dict[str, Any]:
    """原逻辑：独立合成"""
    from backend.services import DoubaoTTSService
    from backend.models import TTSConfig
    
    results = []
    succeeded = 0
    failed = 0
    service_cache = {}
    
    for i, item in enumerate(items):
        text = item.get("text", "")
        instruction = item.get("instruction", "")
        voice_id = item.get("voice_id", "")
        filename = item.get("filename", f"dialogue_{i+1:03d}.mp3")
        output_path = os.path.join(out_dir, filename)
        
        if not text or not voice_id:
            results.append({
                "index": i,
                "success": False,
                "error": "缺少必要参数 text 或 voice_id",
            })
            failed += 1
            continue
        
        resource_id = _get_resource_id(voice_id)
        if resource_id not in service_cache:
            service_cache[resource_id] = DoubaoTTSService(resource_id=resource_id)
        service = service_cache[resource_id]
        
        config = TTSConfig(voice_type=voice_id)
        context_texts = _build_context_legacy(instruction)
        
        result = service.synthesize(
            text=text,
            config=config,
            output_path=output_path,
            context_texts=context_texts,
        )
        
        if result.success:
            results.append({
                "index": i,
                "success": True,
                "audio_path": result.audio_path or output_path,
                "duration_ms": result.duration_ms,
            })
            succeeded += 1
        else:
            results.append({
                "index": i,
                "success": False,
                "error": result.error_message or "合成失败",
            })
            failed += 1
    
    return {
        "success": failed == 0,
        "results": results,
        "total": len(items),
        "succeeded": succeeded,
        "failed": failed,
        "output_dir": out_dir,
    }


def _build_emotion_instruction(instruction: str) -> Optional[str]:
    """将 instruction 转换为2.0的情绪指令格式"""
    if not instruction:
        return None
    
    clean = instruction.strip()
    clean = clean.lstrip('[').lstrip('#').lstrip('＃')
    clean = clean.rstrip(']')
    clean = clean.strip()
    
    if not clean:
        return None
    
    if not clean.endswith('话') and not clean.endswith('?') and not clean.endswith('？'):
        clean = clean.rstrip('说')
        clean = f"请{clean}说话"
    
    return clean


def _build_context_legacy(instruction: str) -> Optional[list]:
    """原逻辑：构建 context_texts 参数"""
    result = _build_emotion_instruction(instruction)
    return [result] if result else None


@tool
def audio_merge(
    audio_paths: List[str],
    output_path: str,
    gap_ms: int = 500,
) -> Dict[str, Any]:
    """
    音频合并工具 - 将多个音频文件合并为一个
    
    Args:
        audio_paths: 要合并的音频文件路径列表
        output_path: 合并后的输出文件路径
        gap_ms: 片段之间的间隔时长（毫秒）
    
    Returns:
        包含 success, merged_audio_path, total_duration_ms, error 的字典
    """
    try:
        if not audio_paths:
            return {"success": False, "error": "音频路径列表为空"}

        for path in audio_paths:
            if not os.path.exists(path):
                return {"success": False, "error": f"音频文件不存在: {path}"}

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        suffix = Path(output_path).suffix.lower()
        if suffix == ".mp3":
            import shutil
            import subprocess

            ffmpeg = shutil.which("ffmpeg")
            if ffmpeg:
                try:
                    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
                        concat_list_path = f.name
                        for p in audio_paths:
                            safe_path = p.replace("'", "'\\''")
                            f.write(f"file '{safe_path}'\n")

                    proc = subprocess.run(
                        [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", concat_list_path, "-c", "copy", output_path],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=False,
                    )
                    if proc.returncode == 0 and os.path.exists(output_path):
                        return {
                            "success": True,
                            "merged_audio_path": output_path,
                            "total_duration_ms": None,
                        }
                finally:
                    try:
                        os.remove(concat_list_path)
                    except Exception:
                        pass

            def _strip_id3v2(data: bytes) -> bytes:
                if len(data) < 10 or data[:3] != b"ID3":
                    return data
                size_bytes = data[6:10]
                tag_size = 0
                for b in size_bytes:
                    tag_size = (tag_size << 7) | (b & 0x7F)
                start = 10 + tag_size
                return data[start:] if start < len(data) else b""

            with open(output_path, "wb") as out_f:
                for i, p in enumerate(audio_paths):
                    with open(p, "rb") as in_f:
                        data = in_f.read()
                    if i > 0:
                        data = _strip_id3v2(data)
                    out_f.write(data)

            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return {
                    "success": True,
                    "merged_audio_path": output_path,
                    "total_duration_ms": None,
                }
            return {"success": False, "error": "合并失败：无法生成输出文件"}

        from pydub import AudioSegment

        merged = AudioSegment.from_file(audio_paths[0])
        gap = AudioSegment.silent(duration=gap_ms)

        for path in audio_paths[1:]:
            audio = AudioSegment.from_file(path)
            merged = merged + gap + audio

        merged.export(output_path, format=suffix.lstrip(".") or "mp3")

        return {
            "success": True,
            "merged_audio_path": output_path,
            "total_duration_ms": len(merged),
        }
    except ImportError:
        return {"success": False, "error": "需要安装 pydub 库：pip install pydub"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def get_voice_list(
    gender: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 20,
) -> Dict[str, Any]:
    """
    获取可用音色列表
    
    Args:
        gender: 性别过滤
        category: 类别过滤
        limit: 返回的最大数量
    
    Returns:
        包含 success, voices, total 的字典
    """
    voices = [
        {"voice_id": "zh_female_vv_uranus_bigtts", "name": "Vivi 2.0", "gender": "female", "category": "2.0通用", "desc": "年轻女性，清晰自然"},
        {"voice_id": "zh_female_xiaohe_uranus_bigtts", "name": "小何 2.0", "gender": "female", "category": "2.0通用", "desc": "温柔亲切"},
        {"voice_id": "zh_male_m191_uranus_bigtts", "name": "云舟 2.0", "gender": "male", "category": "2.0通用", "desc": "成熟男性"},
        {"voice_id": "zh_male_taocheng_uranus_bigtts", "name": "小天 2.0", "gender": "male", "category": "2.0通用", "desc": "年轻男性"},
        {"voice_id": "zh_female_gaolengyujie_emo_v2_mars_bigtts", "name": "高冷御姐", "gender": "female", "category": "多情感", "desc": "冷艳高傲"},
        {"voice_id": "zh_female_tianxinxiaomei_emo_v2_mars_bigtts", "name": "甜心小美", "gender": "female", "category": "多情感", "desc": "甜美可爱"},
        {"voice_id": "zh_male_lengkugege_emo_v2_mars_bigtts", "name": "冷酷哥哥", "gender": "male", "category": "多情感", "desc": "冷酷帅气"},
        {"voice_id": "zh_male_aojiaobazong_emo_v2_mars_bigtts", "name": "傲娇霸总", "gender": "male", "category": "多情感", "desc": "傲娇霸气"},
        {"voice_id": "saturn_zh_female_keainvsheng_tob", "name": "可爱女生", "gender": "female", "category": "角色扮演", "desc": "可爱甜美"},
        {"voice_id": "saturn_zh_male_shuanglangshaonian_tob", "name": "爽朗少年", "gender": "male", "category": "角色扮演", "desc": "阳光爽朗"},
    ]
    
    result = voices
    if gender:
        result = [v for v in result if v["gender"] == gender]
    if category:
        result = [v for v in result if v["category"] == category]
    
    return {
        "success": True,
        "voices": result[:limit],
        "total": len(result),
    }


# 工具集合
PREVIEW_TOOLS = [tts_preview, get_voice_list]
SYNTHESIS_TOOLS = [tts_synthesize, tts_synthesize_batch, audio_merge]
TTS_TOOLS = PREVIEW_TOOLS + SYNTHESIS_TOOLS
