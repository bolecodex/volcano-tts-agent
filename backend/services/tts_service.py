# -*- coding: utf-8 -*-
"""
豆包语音合成服务 (V3 接口)

提供同步和异步的 TTS 合成功能。
使用 V3 HTTP 单向流式接口。
"""

import os
import uuid
import json
import base64
import logging
import tempfile
from pathlib import Path
from typing import Optional, Union

import httpx

from ..models import TTSConfig, TTSResult, AudioEncoding, detect_voice_version, get_resource_id
from ..config import DOUBAO_TTS_APP_ID, DOUBAO_TTS_ACCESS_TOKEN, DOUBAO_TTS_CLUSTER

logger = logging.getLogger(__name__)

_VOICE_ALIASES: dict[str, str] = {
    "zh_male_ahu_uranus_bigtts": "zh_male_wennuanahu_uranus_bigtts",
}


def _normalize_voice_type(voice_type: str) -> str:
    if not voice_type:
        return voice_type
    return _VOICE_ALIASES.get(voice_type, voice_type)


def _is_clone_voice(voice_type: str) -> bool:
    if not voice_type:
        return False
    lower = voice_type.lower()
    return lower.startswith("icl_") or "_icl_" in lower


def _normalize_credential(value: Optional[str]) -> str:
    if value is None:
        return ""
    normalized = str(value).strip()
    if not normalized:
        return ""
    normalized = normalized.strip("`").strip()
    if (normalized.startswith('"') and normalized.endswith('"')) or (normalized.startswith("'") and normalized.endswith("'")):
        normalized = normalized[1:-1].strip()
    return normalized


def _first_non_empty(*candidates: Optional[str]) -> str:
    for candidate in candidates:
        normalized = _normalize_credential(candidate)
        if normalized:
            return normalized
    return ""

def _first_non_empty_with_source(candidates: list[tuple[str, Optional[str]]]) -> tuple[str, str]:
    for source, candidate in candidates:
        normalized = _normalize_credential(candidate)
        if normalized:
            return normalized, source
    return "", ""


class DoubaoTTSService:
    """
    豆包语音合成服务 (V3 接口)
    
    使用火山引擎 TTS V3 API 进行语音合成。
    
    示例:
        ```python
        from backend.doubao_tts_v2 import DoubaoTTSService, TTSConfig
        
        # 创建服务实例
        tts = DoubaoTTSService(
            app_id="your_app_id",
            access_token="your_access_token",
        )
        
        # 配置音色
        config = TTSConfig(voice_type="zh_female_cancan_mars_bigtts")
        
        # 合成语音
        result = tts.synthesize("你好，我是豆包语音助手。", config)
        
        if result.success:
            # 保存到文件
            with open("output.mp3", "wb") as f:
                f.write(result.audio_data)
        ```
    """
    
    # V3 API 端点
    API_URL = "https://openspeech.bytedance.com/api/v3/tts/unidirectional"
    
    # 资源 ID 映射
    RESOURCE_ID_MAP = {
        "tts_1.0": "seed-tts-1.0",           # 豆包语音合成模型1.0 (字符版)
        "tts_1.0_concurr": "seed-tts-1.0-concurr",  # 豆包语音合成模型1.0 (并发版)
        "tts_2.0": "seed-tts-2.0",           # 豆包语音合成模型2.0
        "icl_1.0": "seed-icl-1.0",           # 声音复刻1.0 (字符版)
        "icl_1.0_concurr": "seed-icl-1.0-concurr",  # 声音复刻1.0 (并发版)
        "icl_2.0": "seed-icl-2.0",           # 声音复刻2.0
    }
    
    def __init__(
        self,
        app_id: Optional[str] = None,
        access_token: Optional[str] = None,
        resource_id: str = "seed-tts-1.0",
        timeout: float = 60.0,
    ):
        """
        初始化 TTS 服务
        
        Args:
            app_id: 应用 ID，优先级: 参数 > 配置文件 > 环境变量
            access_token: 访问令牌，优先级: 参数 > 配置文件 > 环境变量
            resource_id: 资源 ID，默认 "seed-tts-1.0" (豆包语音合成模型1.0)
            timeout: 请求超时时间 (秒)
        """
        # 优先级: 参数 > 配置文件 > 环境变量
        self.app_id, self.app_id_source = _first_non_empty_with_source([
            ("arg:app_id", app_id),
            ("config:DOUBAO_TTS_APP_ID", DOUBAO_TTS_APP_ID),
            ("env:DOUBAO_TTS_APP_ID", os.getenv("DOUBAO_TTS_APP_ID")),
            ("env:DOUBAO_TTS_APP_KEY", os.getenv("DOUBAO_TTS_APP_KEY")),
            ("env:DOUBAO_TTS_APPID", os.getenv("DOUBAO_TTS_APPID")),
            ("env:TTS_APP_ID", os.getenv("TTS_APP_ID")),
            ("env:TTS_APP_KEY", os.getenv("TTS_APP_KEY")),
        ])
        self.access_token, self.access_token_source = _first_non_empty_with_source([
            ("arg:access_token", access_token),
            ("config:DOUBAO_TTS_ACCESS_TOKEN", DOUBAO_TTS_ACCESS_TOKEN),
            ("env:DOUBAO_TTS_ACCESS_TOKEN", os.getenv("DOUBAO_TTS_ACCESS_TOKEN")),
            ("env:DOUBAO_TTS_AK", os.getenv("DOUBAO_TTS_AK")),
            ("env:DOUBAO_TTS_ACCESS_KEY", os.getenv("DOUBAO_TTS_ACCESS_KEY")),
            ("env:TTS_ACCESS_KEY", os.getenv("TTS_ACCESS_KEY")),
        ])
        self.resource_id = resource_id
        self.timeout = timeout
        
        if not self.app_id:
            logger.warning("未设置 app_id，请在 config.py 或环境变量 DOUBAO_TTS_APP_ID 中设置")
        if not self.access_token:
            logger.warning("未设置 access_token，请在 config.py 或环境变量 DOUBAO_TTS_ACCESS_TOKEN 中设置")
    
    def _resolve_credentials_for_resource(self, resource_id: str) -> tuple[str, str, str, str]:
        if resource_id == "seed-tts-2.0":
            app_id, app_id_source = _first_non_empty_with_source([
                ("env:DOUBAO_TTS_APP_ID_TTS2", os.getenv("DOUBAO_TTS_APP_ID_TTS2")),
                ("env:DOUBAO_TTS_APP_KEY_TTS2", os.getenv("DOUBAO_TTS_APP_KEY_TTS2")),
                ("env:DOUBAO_TTS_APP_ID_2", os.getenv("DOUBAO_TTS_APP_ID_2")),
                ("fallback:self.app_id", self.app_id),
            ])
            access_token, access_token_source = _first_non_empty_with_source([
                ("env:DOUBAO_TTS_ACCESS_TOKEN_TTS2", os.getenv("DOUBAO_TTS_ACCESS_TOKEN_TTS2")),
                ("env:DOUBAO_TTS_AK_TTS2", os.getenv("DOUBAO_TTS_AK_TTS2")),
                ("env:DOUBAO_TTS_ACCESS_TOKEN_2", os.getenv("DOUBAO_TTS_ACCESS_TOKEN_2")),
                ("env:DOUBAO_TTS_AK_2", os.getenv("DOUBAO_TTS_AK_2")),
                ("fallback:self.access_token", self.access_token),
            ])
            return app_id, access_token, app_id_source, access_token_source
        return self.app_id, self.access_token, self.app_id_source, self.access_token_source

    def _get_headers(self, request_id: Optional[str] = None, resource_id: Optional[str] = None) -> dict:
        """获取 V3 请求头"""
        actual_resource_id = resource_id or self.resource_id
        app_id, access_token, _, _ = self._resolve_credentials_for_resource(actual_resource_id)
        if not app_id or not access_token:
            raise ValueError(
                "豆包TTS鉴权缺失：请配置 DOUBAO_TTS_APP_ID 与 DOUBAO_TTS_AK/DOUBAO_TTS_ACCESS_TOKEN"
            )
        headers = {
            "Content-Type": "application/json",
            "X-Api-App-Id": app_id,
            "X-Api-App-Key": app_id,
            "X-Api-Access-Key": access_token,
            "X-Api-Resource-Id": actual_resource_id,
        }
        if request_id:
            headers["X-Api-Request-Id"] = request_id
        return headers
    
    def _build_request_payload(
        self,
        text: str,
        config: TTSConfig,
        context_texts: Optional[list[str]] = None,
        version: str = "1.0",
    ) -> dict:
        """
        构建 V3 请求体
        
        Args:
            text: 要合成的文本
            config: TTS 配置
            context_texts: 上下文指令 (2.0专用)
            version: API版本 "1.0" 或 "2.0"
        
        Returns:
            请求体字典
        """
        # 音频参数
        audio_params = {
            "format": config.encoding.value if isinstance(config.encoding, AudioEncoding) else config.encoding,
            "sample_rate": config.sample_rate,
        }
        
        # 语速转换: speed_ratio [0.1, 2.0] -> speech_rate [-50, 100]
        # 1.0 = 0, 2.0 = 100, 0.5 = -50
        speech_rate = int((config.speed_ratio - 1.0) * 100)
        speech_rate = max(-50, min(100, speech_rate))
        audio_params["speech_rate"] = speech_rate
        
        # 音量转换: loudness_ratio [0.5, 2.0] -> loudness_rate [-50, 100]
        loudness_rate = int((config.loudness_ratio - 1.0) * 100)
        loudness_rate = max(-50, min(100, loudness_rate))
        audio_params["loudness_rate"] = loudness_rate
        
        # 情感设置 - 仅1.0版本使用emotion参数
        if version == "1.0" and config.enable_emotion and config.emotion:
            audio_params["emotion"] = config.emotion
            if config.emotion_scale:
                audio_params["emotion_scale"] = config.emotion_scale
        
        # 构建请求体
        payload = {
            "user": {
                "uid": "novel_split_user",
            },
            "req_params": {
                "text": text,
                "speaker": config.voice_type,
                "audio_params": audio_params,
            },
        }
        
        # 附加参数
        additions = {}
        
        # 语种设置
        if config.explicit_language:
            additions["explicit_language"] = config.explicit_language

        # 2.0版本：使用context_texts和section_id
        if version == "2.0":
            # 优先使用传入的context_texts，其次使用config中的
            ctx = context_texts or config.context_texts
            if ctx:
                additions["context_texts"] = ctx
            if config.section_id:
                additions["section_id"] = config.section_id
        else:
            # 1.0版本：也支持context_texts（兼容性保留）
            if context_texts:
                additions["context_texts"] = context_texts
        
        # 模型版本
        if config.model:
            payload["req_params"]["model"] = config.model
        
        if additions:
            payload["req_params"]["additions"] = json.dumps(additions)
        
        return payload

    
    def synthesize(
        self,
        text: str,
        config: TTSConfig,
        output_path: Optional[str] = None,
        context_texts: Optional[list[str]] = None,
    ) -> TTSResult:
        """
        同步合成语音 (V3 流式接口)
        
        Args:
            text: 要合成的文本
            config: TTS 配置
            output_path: 输出文件路径 (可选)，如果指定则保存音频到文件
        
        Returns:
            TTSResult: 合成结果
        """
        config.voice_type = _normalize_voice_type(config.voice_type)
        req_id = str(uuid.uuid4())
        
        # 构建请求
        payload = self._build_request_payload(text, config, context_texts=context_texts)
        
        logger.info(f"🔊 开始合成语音: reqid={req_id[:8]}..., resource_id={self.resource_id}, voice={config.voice_type}")
        logger.info(f"🔊 合成文本: {text[:100]}...")
        if context_texts:
            logger.info(f"🔊 上下文: {context_texts[0][:100] if context_texts else '(无)'}...")
        
        try:
            # 使用流式请求
            with httpx.Client(timeout=self.timeout) as client:
                with client.stream(
                    "POST",
                    self.API_URL,
                    headers=self._get_headers(req_id),
                    json=payload,
                ) as response:
                    # 获取 logid 用于问题追踪
                    log_id = response.headers.get("X-Tt-Logid", "")
                    
                    # 检查 HTTP 状态
                    if response.status_code != 200:
                        error_text = response.read().decode("utf-8", errors="ignore")
                        logger.error(f"🔊 HTTP 错误: status={response.status_code}, body={error_text[:200]}")
                        _, _, app_id_source, access_token_source = self._resolve_credentials_for_resource(self.resource_id)
                        return TTSResult.from_error(
                            response.status_code,
                            f"HTTP {response.status_code}: {error_text[:200]} (resource_id={self.resource_id}, app_id_source={app_id_source}, access_token_source={access_token_source})",
                            req_id,
                        )
                    
                    # 收集所有音频数据
                    audio_chunks = []
                    last_error = None
                    
                    for line in response.iter_lines():
                        if not line:
                            continue
                        
                        try:
                            data = json.loads(line)
                            code = data.get("code", 0)
                            message = data.get("message", "")
                            
                            # 成功结束标记
                            if code == 20000000:
                                logger.debug(f"🔊 合成结束: {message}")
                                break
                            
                            # 错误处理
                            if code != 0:
                                last_error = (code, message)
                                logger.error(f"🔊 合成错误: code={code}, message={message}")
                                break
                            
                            # 获取音频数据
                            audio_base64 = data.get("data")
                            if audio_base64:
                                audio_chunk = base64.b64decode(audio_base64)
                                audio_chunks.append(audio_chunk)
                                
                        except json.JSONDecodeError as e:
                            logger.warning(f"🔊 JSON 解析警告: {e}, line={line[:100]}")
                            continue
                    
                    # 检查是否有错误
                    if last_error:
                        return TTSResult.from_error(last_error[0], last_error[1], req_id)
                    
                    # 合并音频数据
                    if not audio_chunks:
                        logger.error(f"🔊 未收到音频数据: reqid={req_id}")
                        return TTSResult.from_error(-1, "未收到音频数据", req_id)
                    
                    audio_data = b"".join(audio_chunks)
                    
                    logger.info(f"🔊 合成成功: reqid={req_id[:8]}..., size={len(audio_data)} bytes, chunks={len(audio_chunks)}")
                    
                    # 保存到文件
                    saved_path = None
                    if output_path:
                        saved_path = self._save_audio(audio_data, output_path, config.encoding)
                    
                    return TTSResult.from_success(
                        audio_data=audio_data,
                        request_id=req_id,
                        audio_path=saved_path,
                    )
                
        except httpx.TimeoutException:
            logger.error(f"🔊 请求超时: reqid={req_id}")
            return TTSResult.from_error(-1, "请求超时", req_id)
        except httpx.HTTPError as e:
            logger.error(f"🔊 HTTP 错误: {e}")
            return TTSResult.from_error(-1, f"HTTP 错误: {str(e)}", req_id)
        except Exception as e:
            logger.error(f"🔊 未知错误: {e}")
            return TTSResult.from_error(-1, f"未知错误: {str(e)}", req_id)
    
    def synthesize_auto(
        self,
        text: str,
        config: TTSConfig,
        output_path: Optional[str] = None,
    ) -> TTSResult:
        """
        自动检测版本进行语音合成（推荐使用）
        
        根据音色自动选择1.0或2.0版本，并使用对应的参数：
        - 1.0音色：使用 emotion 参数控制情绪
        - 2.0音色：使用 context_texts 参数控制情绪
        
        Args:
            text: 要合成的文本
            config: TTS配置（包含音色、情绪指令等）
            output_path: 输出文件路径（可选）
            
        Returns:
            TTSResult: 合成结果
            
        示例:
            # 1.0 多情感音色
            config = TTSConfig(
                voice_type="zh_female_gaolengyujie_emo_v2_mars_bigtts",
                emotion="angry",
                emotion_scale=4,
            )
            result = tts.synthesize_auto("你太过分了！", config)
            
            # 2.0 通用音色
            config = TTSConfig(
                voice_type="zh_female_xiaohe_uranus_bigtts",
                context_texts=["请用愤怒质问的语气说话"],
            )
            result = tts.synthesize_auto("你太过分了！", config)
        """
        config.voice_type = _normalize_voice_type(config.voice_type)
        version = config.api_version or detect_voice_version(config.voice_type)
        is_clone = _is_clone_voice(config.voice_type)
        resource_id = get_resource_id(version, is_clone=is_clone)
        
        req_id = str(uuid.uuid4())
        
        # 构建请求，传入版本信息
        payload = self._build_request_payload(text, config, version=version)
        
        logger.info(f"🔊 [Auto] 开始合成: reqid={req_id[:8]}..., version={version}, resource_id={resource_id}, voice={config.voice_type}")
        logger.info(f"🔊 合成文本: {text[:100]}...")
        
        # 日志显示使用的参数
        if version == "2.0" and config.context_texts:
            logger.info(f"🔊 情绪指令: {config.context_texts[0][:100]}...")
        elif version == "1.0" and config.emotion:
            logger.info(f"🔊 情绪参数: emotion={config.emotion}, scale={config.emotion_scale}")
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                with client.stream(
                    "POST",
                    self.API_URL,
                    headers=self._get_headers(req_id, resource_id=resource_id),
                    json=payload,
                ) as response:
                    log_id = response.headers.get("X-Tt-Logid", "")
                    
                    if response.status_code != 200:
                        error_text = response.read().decode("utf-8", errors="ignore")
                        logger.error(f"🔊 HTTP 错误: status={response.status_code}, body={error_text[:200]}")
                        _, _, app_id_source, access_token_source = self._resolve_credentials_for_resource(resource_id)
                        return TTSResult.from_error(
                            response.status_code,
                            f"HTTP {response.status_code}: {error_text[:200]} (resource_id={resource_id}, app_id_source={app_id_source}, access_token_source={access_token_source})",
                            req_id,
                        )
                    
                    audio_chunks = []
                    last_error = None
                    
                    for line in response.iter_lines():
                        if not line:
                            continue
                        
                        try:
                            data = json.loads(line)
                            code = data.get("code", 0)
                            message = data.get("message", "")
                            
                            if code == 20000000:
                                logger.debug(f"🔊 合成结束: {message}")
                                break
                            
                            if code != 0:
                                last_error = (code, message)
                                logger.error(f"🔊 合成错误: code={code}, message={message}")
                                break
                            
                            audio_base64 = data.get("data")
                            if audio_base64:
                                audio_chunk = base64.b64decode(audio_base64)
                                audio_chunks.append(audio_chunk)
                                
                        except json.JSONDecodeError as e:
                            logger.warning(f"🔊 JSON 解析警告: {e}, line={line[:100]}")
                            continue
                    
                    if last_error:
                        if (
                            last_error[1]
                            and "resource id is mismatched with speaker related resource" in str(last_error[1]).lower()
                        ):
                            alt_resource_id = get_resource_id(version, is_clone=not is_clone)
                            if alt_resource_id and alt_resource_id != resource_id:
                                retry = self._synthesize_auto_with_resource(
                                    text=text,
                                    config=config,
                                    output_path=output_path,
                                    version=version,
                                    resource_id=alt_resource_id,
                                )
                                if retry.success:
                                    return retry
                        return TTSResult.from_error(last_error[0], last_error[1], req_id)
                    
                    if not audio_chunks:
                        logger.error(f"🔊 未收到音频数据: reqid={req_id}")
                        return TTSResult.from_error(-1, "未收到音频数据", req_id)
                    
                    audio_data = b"".join(audio_chunks)
                    
                    logger.info(f"🔊 [Auto] 合成成功: reqid={req_id[:8]}..., version={version}, size={len(audio_data)} bytes")
                    
                    saved_path = None
                    if output_path:
                        saved_path = self._save_audio(audio_data, output_path, config.encoding)
                    
                    return TTSResult.from_success(
                        audio_data=audio_data,
                        request_id=req_id,
                        audio_path=saved_path,
                    )
                
        except httpx.TimeoutException:
            logger.error(f"🔊 请求超时: reqid={req_id}")
            return TTSResult.from_error(-1, "请求超时", req_id)
        except httpx.HTTPError as e:
            logger.error(f"🔊 HTTP 错误: {e}")
            return TTSResult.from_error(-1, f"HTTP 错误: {str(e)}", req_id)
        except Exception as e:
            logger.error(f"🔊 未知错误: {e}")
            return TTSResult.from_error(-1, f"未知错误: {str(e)}", req_id)

    def _synthesize_auto_with_resource(
        self,
        text: str,
        config: TTSConfig,
        output_path: Optional[str],
        version: str,
        resource_id: str,
    ) -> TTSResult:
        req_id = str(uuid.uuid4())
        payload = self._build_request_payload(text, config, version=version)

        logger.info(
            f"🔊 [Auto-Retry] 开始合成: reqid={req_id[:8]}..., version={version}, resource_id={resource_id}, voice={config.voice_type}"
        )

        try:
            with httpx.Client(timeout=self.timeout) as client:
                with client.stream(
                    "POST",
                    self.API_URL,
                    headers=self._get_headers(req_id, resource_id=resource_id),
                    json=payload,
                ) as response:
                    if response.status_code != 200:
                        error_text = response.read().decode("utf-8", errors="ignore")
                        logger.error(
                            f"🔊 [Auto-Retry] HTTP 错误: status={response.status_code}, body={error_text[:200]}"
                        )
                        _, _, app_id_source, access_token_source = self._resolve_credentials_for_resource(resource_id)
                        return TTSResult.from_error(
                            response.status_code,
                            f"HTTP {response.status_code}: {error_text[:200]} (resource_id={resource_id}, app_id_source={app_id_source}, access_token_source={access_token_source})",
                            req_id,
                        )

                    audio_chunks = []
                    last_error = None

                    for line in response.iter_lines():
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            code = data.get("code", 0)
                            message = data.get("message", "")

                            if code == 20000000:
                                break
                            if code != 0:
                                last_error = (code, message)
                                break
                            audio_base64 = data.get("data")
                            if audio_base64:
                                audio_chunks.append(base64.b64decode(audio_base64))
                        except json.JSONDecodeError:
                            continue

                    if last_error:
                        return TTSResult.from_error(last_error[0], last_error[1], req_id)
                    if not audio_chunks:
                        return TTSResult.from_error(-1, "未收到音频数据", req_id)

                    audio_data = b"".join(audio_chunks)
                    saved_path = None
                    if output_path:
                        saved_path = self._save_audio(audio_data, output_path, config.encoding)

                    return TTSResult.from_success(
                        audio_data=audio_data,
                        request_id=req_id,
                        audio_path=saved_path,
                    )
        except Exception as e:
            return TTSResult.from_error(-1, f"未知错误: {str(e)}", req_id)

    
    async def synthesize_async(
        self,
        text: str,
        config: TTSConfig,
        output_path: Optional[str] = None,
    ) -> TTSResult:
        """
        异步合成语音 (V3 流式接口)
        
        Args:
            text: 要合成的文本
            config: TTS 配置
            output_path: 输出文件路径 (可选)
        
        Returns:
            TTSResult: 合成结果
        """
        req_id = str(uuid.uuid4())
        payload = self._build_request_payload(text, config)
        
        logger.info(f"🔊 [异步] 开始合成: reqid={req_id[:8]}..., voice={config.voice_type}")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    self.API_URL,
                    headers=self._get_headers(req_id),
                    json=payload,
                ) as response:
                    log_id = response.headers.get("X-Tt-Logid", "")
                    
                    if response.status_code != 200:
                        error_text = (await response.aread()).decode("utf-8", errors="ignore")
                        return TTSResult.from_error(
                            response.status_code,
                            f"HTTP {response.status_code}: {error_text[:200]} (resource_id={self.resource_id}, app_id_source={getattr(self, 'app_id_source', '')}, access_token_source={getattr(self, 'access_token_source', '')})",
                            req_id,
                        )
                    
                    audio_chunks = []
                    last_error = None
                    
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        
                        try:
                            data = json.loads(line)
                            code = data.get("code", 0)
                            message = data.get("message", "")
                            
                            if code == 20000000:
                                break
                            
                            if code != 0:
                                last_error = (code, message)
                                break
                            
                            audio_base64 = data.get("data")
                            if audio_base64:
                                audio_chunk = base64.b64decode(audio_base64)
                                audio_chunks.append(audio_chunk)
                                
                        except json.JSONDecodeError:
                            continue
                    
                    if last_error:
                        return TTSResult.from_error(last_error[0], last_error[1], req_id)
                    
                    if not audio_chunks:
                        return TTSResult.from_error(-1, "未收到音频数据", req_id)
                    
                    audio_data = b"".join(audio_chunks)
                    
                    logger.info(f"🔊 [异步] 合成成功: reqid={req_id[:8]}..., size={len(audio_data)} bytes")
                    
                    saved_path = None
                    if output_path:
                        saved_path = self._save_audio(audio_data, output_path, config.encoding)
                    
                    return TTSResult.from_success(
                        audio_data=audio_data,
                        request_id=req_id,
                        audio_path=saved_path,
                    )
                
        except httpx.TimeoutException:
            return TTSResult.from_error(-1, "请求超时", req_id)
        except httpx.HTTPError as e:
            return TTSResult.from_error(-1, f"HTTP 错误: {str(e)}", req_id)
        except Exception as e:
            return TTSResult.from_error(-1, f"未知错误: {str(e)}", req_id)
    
    def _save_audio(
        self,
        audio_data: bytes,
        output_path: str,
        encoding: AudioEncoding,
    ) -> str:
        """
        保存音频到文件
        
        Args:
            audio_data: 音频二进制数据
            output_path: 输出路径
            encoding: 音频编码格式
        
        Returns:
            实际保存的文件路径
        """
        path = Path(output_path)
        
        # 确保目录存在
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # 添加正确的扩展名
        ext_map = {
            AudioEncoding.MP3: ".mp3",
            AudioEncoding.WAV: ".wav",
            AudioEncoding.PCM: ".pcm",
            AudioEncoding.OGG_OPUS: ".ogg",
        }
        expected_ext = ext_map.get(encoding, ".mp3")
        
        if not path.suffix or path.suffix.lower() != expected_ext:
            path = path.with_suffix(expected_ext)
        
        with open(path, "wb") as f:
            f.write(audio_data)
        
        logger.info(f"🔊 音频已保存: {path}")
        return str(path)
    
    def synthesize_to_file(
        self,
        text: str,
        config: TTSConfig,
        output_dir: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> TTSResult:
        """
        合成语音并保存到文件的便捷方法
        
        Args:
            text: 要合成的文本
            config: TTS 配置
            output_dir: 输出目录，默认使用临时目录
            filename: 文件名 (不含扩展名)，默认使用 UUID
        
        Returns:
            TTSResult: 合成结果，audio_path 包含文件路径
        """
        # 确定输出目录
        if output_dir:
            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
        else:
            out_dir = Path(tempfile.gettempdir()) / "doubao_tts"
            out_dir.mkdir(parents=True, exist_ok=True)
        
        # 确定文件名
        name = filename or str(uuid.uuid4())[:8]
        
        # 根据编码确定扩展名
        ext_map = {
            AudioEncoding.MP3: ".mp3",
            AudioEncoding.WAV: ".wav",
            AudioEncoding.PCM: ".pcm",
            AudioEncoding.OGG_OPUS: ".ogg",
        }
        ext = ext_map.get(config.encoding, ".mp3")
        
        output_path = str(out_dir / f"{name}{ext}")
        
        return self.synthesize(text, config, output_path=output_path)


# 便捷函数
def quick_synthesize(
    text: str,
    voice_type: str,
    output_path: Optional[str] = None,
    app_id: Optional[str] = None,
    access_token: Optional[str] = None,
    speed_ratio: float = 1.0,
    encoding: str = "mp3",
) -> TTSResult:
    """
    快速合成语音的便捷函数
    
    Args:
        text: 要合成的文本
        voice_type: 音色类型
        output_path: 输出文件路径 (可选)
        app_id: 应用 ID (可选，默认从配置读取)
        access_token: 访问令牌 (可选，默认从配置读取)
        speed_ratio: 语速，默认 1.0
        encoding: 音频格式，默认 "mp3"
    
    Returns:
        TTSResult: 合成结果
    
    Example:
        ```python
        from backend.doubao_tts_v2 import quick_synthesize
        
        result = quick_synthesize(
            text="你好，世界！",
            voice_type="zh_female_cancan_mars_bigtts",
            output_path="hello.mp3",
        )
        
        if result.success:
            print(f"音频已保存到: {result.audio_path}")
        ```
    """
    service = DoubaoTTSService(app_id=app_id, access_token=access_token)
    
    config = TTSConfig(
        voice_type=voice_type,
        encoding=AudioEncoding(encoding) if isinstance(encoding, str) else encoding,
        speed_ratio=speed_ratio,
    )
    
    return service.synthesize(text, config, output_path=output_path)


# ============================================================================
# 多轮对话TTS会话管理
# ============================================================================

from dataclasses import dataclass, field
from typing import List
from datetime import datetime, timedelta


@dataclass
class TTSSynthesisItem:
    """单次合成记录"""
    index: int                      # 序号
    text: str                       # 合成文本
    voice_type: str                 # 音色
    version: str                    # API版本 "1.0" | "2.0"
    session_id: str                 # 本次session_id
    context_texts: Optional[list[str]] = None  # 2.0情绪指令
    emotion: Optional[str] = None   # 1.0情绪参数
    audio_path: Optional[str] = None  # 音频路径
    success: bool = True            # 是否成功
    timestamp: datetime = field(default_factory=datetime.now)


class MultiTurnTTSSession:
    """
    多轮对话TTS会话管理器
    
    支持:
    - 自动识别音色版本（1.0/2.0）
    - 1.0使用emotion参数，2.0使用context_texts参数
    - 2.0音色自动维护session_id链式上下文
    - 混合使用1.0和2.0音色
    
    示例:
        ```python
        from backend.doubao_tts_v2 import DoubaoTTSService, MultiTurnTTSSession
        
        tts = DoubaoTTSService()
        session = MultiTurnTTSSession(tts)
        
        # 2.0音色
        session.synthesize(
            text="今天是我的生日...",
            voice_type="zh_female_xiaohe_uranus_bigtts",
            emotion_instruction="请用悲伤的语气说话",
        )
        
        # 1.0多情感音色
        session.synthesize(
            text="对不起，我忘了...",
            voice_type="zh_male_lengkugege_emo_v2_mars_bigtts",
            emotion="sad",
            emotion_scale=4,
        )
        
        # 获取所有合成记录
        for item in session.history:
            print(f"{item.index}: {item.text[:20]}... ({item.version})")
        ```
    """
    
    # 上下文有效期限制
    MAX_CONTEXT_ROUNDS = 30     # 最多保留30轮上下文
    MAX_CONTEXT_MINUTES = 10    # 上下文最长有效10分钟
    
    def __init__(
        self,
        tts_service: DoubaoTTSService,
        output_dir: Optional[str] = None,
    ):
        """
        初始化多轮对话会话
        
        Args:
            tts_service: TTS服务实例
            output_dir: 音频输出目录（可选）
        """
        self.tts = tts_service
        self.output_dir = output_dir
        self.history: List[TTSSynthesisItem] = []
        self._session_start_time = datetime.now()
        
        # 2.0上下文链：只记录2.0音色的session_id
        self._v2_session_chain: List[str] = []
    
    def synthesize(
        self,
        text: str,
        voice_type: str,
        emotion_instruction: Optional[str] = None,  # 2.0自然语言情绪指令
        emotion: Optional[str] = None,              # 1.0情绪枚举
        emotion_scale: Optional[float] = None,      # 1.0情绪强度
        speed_ratio: float = 1.0,
        output_filename: Optional[str] = None,
    ) -> TTSResult:
        """
        合成一句语音，自动处理版本和上下文
        
        Args:
            text: 要合成的文本
            voice_type: 音色类型
            emotion_instruction: 2.0情绪指令（自然语言），如"请用悲伤的语气说话"
            emotion: 1.0情绪参数（枚举值），如"sad", "angry"
            emotion_scale: 1.0情绪强度，1-5
            speed_ratio: 语速，0.1-2.0
            output_filename: 输出文件名（不含路径），如果设置output_dir则自动保存
            
        Returns:
            TTSResult: 合成结果
        """
        # 检测版本
        version = detect_voice_version(voice_type)
        
        # 检查上下文是否过期
        self._cleanup_expired_context()
        
        # 获取上一个2.0的session_id（用于上下文引用）
        last_v2_session = self._v2_session_chain[-1] if self._v2_session_chain else None
        
        # 构建配置
        config = TTSConfig(
            voice_type=voice_type,
            speed_ratio=speed_ratio,
        )
        
        # 根据版本设置参数
        if version == "2.0":
            # 2.0：使用context_texts和section_id
            if emotion_instruction:
                config.context_texts = [emotion_instruction]
            if last_v2_session:
                config.section_id = last_v2_session
            logger.info(f"🎭 [多轮] 2.0模式: instruction='{emotion_instruction}', section_id={last_v2_session[:8] if last_v2_session else 'None'}...")
        else:
            # 1.0：使用emotion参数
            if emotion:
                config.emotion = emotion
                config.emotion_scale = emotion_scale
            logger.info(f"🎭 [多轮] 1.0模式: emotion={emotion}, scale={emotion_scale}")
        
        # 确定输出路径
        output_path = None
        if self.output_dir and output_filename:
            output_path = str(Path(self.output_dir) / output_filename)
        elif self.output_dir:
            # 自动生成文件名
            output_path = str(Path(self.output_dir) / f"turn_{len(self.history) + 1:03d}.mp3")
        
        # 调用合成
        result = self.tts.synthesize_auto(text, config, output_path=output_path)
        
        # 记录历史
        item = TTSSynthesisItem(
            index=len(self.history) + 1,
            text=text,
            voice_type=voice_type,
            version=version,
            session_id=result.request_id or "",
            context_texts=config.context_texts,
            emotion=emotion,
            audio_path=result.audio_path,
            success=result.success,
        )
        self.history.append(item)
        
        # 如果是2.0且成功，加入上下文链
        if version == "2.0" and result.success and result.request_id:
            self._v2_session_chain.append(result.request_id)
            # 限制链长度
            if len(self._v2_session_chain) > self.MAX_CONTEXT_ROUNDS:
                self._v2_session_chain = self._v2_session_chain[-self.MAX_CONTEXT_ROUNDS:]
        
        return result
    
    def _cleanup_expired_context(self):
        """清理过期的上下文"""
        if not self._v2_session_chain:
            return
        
        # 检查是否超过10分钟
        elapsed = datetime.now() - self._session_start_time
        if elapsed > timedelta(minutes=self.MAX_CONTEXT_MINUTES):
            logger.info(f"🔄 [多轮] 上下文已过期({elapsed.seconds // 60}分钟)，重置会话")
            self.reset_context()
    
    def reset_context(self):
        """重置上下文链（保留历史记录）"""
        self._v2_session_chain = []
        self._session_start_time = datetime.now()
        logger.info("🔄 [多轮] 上下文已重置")
    
    def reset(self):
        """完全重置会话（清除历史和上下文）"""
        self.history = []
        self._v2_session_chain = []
        self._session_start_time = datetime.now()
        logger.info("🔄 [多轮] 会话已完全重置")
    
    @property
    def turn_count(self) -> int:
        """当前轮次数"""
        return len(self.history)
    
    @property
    def v2_context_depth(self) -> int:
        """当前2.0上下文链深度"""
        return len(self._v2_session_chain)
    
    def get_summary(self) -> str:
        """获取会话摘要"""
        if not self.history:
            return "空会话"
        
        v1_count = sum(1 for item in self.history if item.version == "1.0")
        v2_count = sum(1 for item in self.history if item.version == "2.0")
        success_count = sum(1 for item in self.history if item.success)
        
        return (
            f"总轮次: {len(self.history)}, "
            f"1.0: {v1_count}, 2.0: {v2_count}, "
            f"成功: {success_count}/{len(self.history)}, "
            f"上下文深度: {self.v2_context_depth}"
        )
