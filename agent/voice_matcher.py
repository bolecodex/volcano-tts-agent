# -*- coding: utf-8 -*-
"""
🎤 VoiceMatcherAgent - 音色匹配 Agent

负责为角色匹配最佳音色
"""

import os
import re
import json
import uuid
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable

os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")
os.environ.setdefault("LANGSMITH_TRACING", "false")

from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.tools import tool

from .prompts import VOICE_MATCHER_SYSTEM_PROMPT
from .models import VoiceMapping
from .templates import ALL_VOICES, format_all_voices_brief
from .tools import tts_preview

logger = logging.getLogger(__name__)


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """从文本中提取 JSON 对象"""
    if not text:
        return None
    
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    
    code_block_pattern = r'```(?:json)?\s*\n?([\s\S]*?)\n?```'
    matches = re.findall(code_block_pattern, text)
    for match in matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue
    
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    
    start = text.find('[')
    end = text.rfind(']')
    if start != -1 and end != -1 and end > start:
        try:
            return {"voice_mapping": json.loads(text[start:end + 1])}
        except json.JSONDecodeError:
            pass
    
    return None


@tool
def save_voice_mapping(voice_mapping_json: str) -> str:
    """
    保存音色匹配结果
    
    Args:
        voice_mapping_json: JSON 格式的音色映射
    
    Returns:
        保存结果确认
    """
    try:
        data = json.loads(voice_mapping_json)
        
        if isinstance(data, dict) and "voice_mapping" in data:
            voice_mapping = data["voice_mapping"]
        elif isinstance(data, list):
            voice_mapping = data
        else:
            return json.dumps({
                "success": False,
                "error": "格式不正确，请确保包含 voice_mapping 字段",
            }, ensure_ascii=False)
        
        valid_mappings = []
        for mapping in voice_mapping:
            if isinstance(mapping, dict) and "character" in mapping and "voice_id" in mapping:
                valid_mappings.append(mapping)
        
        if valid_mappings:
            return json.dumps({
                "success": True,
                "message": f"✅ 已保存 {len(valid_mappings)} 个音色映射",
                "count": len(valid_mappings),
                "data": {"voice_mapping": valid_mappings},
            }, ensure_ascii=False)
        else:
            return json.dumps({
                "success": False,
                "error": "音色映射中没有有效的条目",
            }, ensure_ascii=False)
            
    except json.JSONDecodeError as e:
        return json.dumps({
            "success": False,
            "error": f"JSON 解析失败: {e}",
        }, ensure_ascii=False)


VOICE_MATCHER_TOOLS = [save_voice_mapping, tts_preview]


class VoiceMatcherAgent:
    """音色匹配 Agent"""
    
    def __init__(
        self,
        model: Optional[str] = None,
        checkpointer=None,
        verbose: bool = True,
    ):
        self.verbose = verbose
        self.model_name = model
        
        # 创建 LLM
        from .llm_config import LLMConfig, get_llm_config
        base_config = get_llm_config()
        
        streaming_config = LLMConfig(
            provider=base_config.provider,
            model=model or base_config.model,
            api_key=base_config.api_key,
            base_url=base_config.base_url,
            temperature=0.5,
            max_tokens=32000,
            streaming=True,
            extra_params=base_config.extra_params,
        )
        self.llm = streaming_config.create_llm()
        
        if checkpointer is None:
            checkpointer = InMemorySaver()
        self.checkpointer = checkpointer
        
        self._agent = None
        self._create_agent()
        
        self._thread_id = f"voice_session_{uuid.uuid4().hex[:8]}"
        self._last_result: Optional[Dict[str, Any]] = None
    
    def _log(self, message: str):
        if self.verbose:
            print(message)
    
    def _build_system_prompt(self) -> str:
        prompt = VOICE_MATCHER_SYSTEM_PROMPT
        prompt += "\n\n## 可用音色列表\n\n"
        prompt += format_all_voices_brief()
        return prompt
    
    def _create_agent(self):
        try:
            from langgraph.prebuilt import create_react_agent
            
            self._agent = create_react_agent(
                model=self.llm,
                tools=VOICE_MATCHER_TOOLS,
                prompt=self._build_system_prompt(),
                checkpointer=self.checkpointer,
            )
            self._log("🚀 音色匹配 Agent 已启动")
        except ImportError as e:
            self._log(f"⚠️ 无法导入 langgraph: {e}")
            self._agent = None
    
    def new_session(self) -> str:
        self._thread_id = f"voice_session_{uuid.uuid4().hex[:8]}"
        self._last_result = None
        self._log(f"🗑️ 已开启新对话! ID: {self._thread_id}")
        return self._thread_id
    
    def _stream_direct(self, prompt: str, system_prompt: Optional[str] = None):
        """直接调用 LLM 流式输出"""
        from langchain_core.messages import HumanMessage, SystemMessage
        
        messages = []
        
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        else:
            messages.append(SystemMessage(content=self._build_system_prompt()))
        
        messages.append(HumanMessage(content=prompt))
        
        for chunk in self.llm.stream(messages):
            if hasattr(chunk, 'content') and chunk.content:
                yield chunk.content
    
    async def match(
        self,
        dialogue_list: List[Dict[str, Any]],
        output_dir: str,
        on_chunk: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """
        为对话列表中的角色匹配音色
        
        Args:
            dialogue_list: 对话列表
            output_dir: 输出目录
            on_chunk: 流式内容回调
        
        Returns:
            音色映射结果
        """
        # 提取唯一角色
        characters = {}
        for item in dialogue_list:
            char = item.get("character", "")
            if char and char not in characters:
                characters[char] = {
                    "character": char,
                    "character_desc": item.get("character_desc", ""),
                    "first_line": item.get("text", "")[:50],
                }
        
        prompt = f"""请为以下角色匹配最佳音色。

## 角色列表
```json
{json.dumps(list(characters.values()), ensure_ascii=False, indent=2)}
```

## 输出要求
请根据角色描述和首句台词，为每个角色匹配最合适的音色。直接输出以下 JSON 格式：

```json
{{
  "voice_mapping": [
    {{
      "character": "角色名",
      "voice_id": "音色ID",
      "voice_name": "音色名称",
      "reason": "匹配理由"
    }}
  ]
}}
```

请直接输出 JSON 内容。"""
        
        self.new_session()
        
        response_parts: List[str] = []
        for chunk in self._stream_direct(prompt):
            response_parts.append(chunk)
            if on_chunk:
                on_chunk(chunk)
        
        response_text = "".join(response_parts)
        return self._parse_json_result(response_text, characters)
    
    def _parse_json_result(
        self,
        response_text: str,
        characters: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """从 LLM 响应中解析 JSON 结果"""
        extracted = extract_json_from_text(response_text)
        
        if extracted:
            voice_mapping = extracted.get("voice_mapping", [])
            if isinstance(extracted, list):
                voice_mapping = extracted
            
            # 补充试听文本
            for mapping in voice_mapping:
                char = mapping.get("character", "")
                if char in characters:
                    mapping["preview_text"] = characters[char].get("first_line", "")
            
            logger.info(f"✅ 成功解析 {len(voice_mapping)} 个音色映射")
            
            self._last_result = {
                "success": True,
                "voice_mapping": voice_mapping,
            }
            return self._last_result
        
        logger.error(f"❌ JSON 解析失败")
        return {
            "success": False,
            "error": "无法从响应中提取音色映射",
            "raw_response": response_text[:1000] if response_text else "(空响应)",
        }
    
    async def rematch(
        self,
        voice_mapping: List[Dict[str, Any]],
        dialogue_list: List[Dict[str, Any]],
        instruction: str,
        target_characters: Optional[List[str]] = None,
        output_dir: str = None,
    ) -> Dict[str, Any]:
        """对话式重新匹配"""
        chars_info = ""
        if target_characters:
            chars_info = f"请重点关注角色: {', '.join(target_characters)}"
        
        prompt = f"""请根据以下指令重新匹配音色：

## 当前音色映射
```json
{json.dumps(voice_mapping, ensure_ascii=False, indent=2)}
```

## 修改指令
{instruction}

{chars_info}

修改完成后，输出完整的 JSON 音色映射。"""
        
        response_parts: List[str] = []
        for chunk in self._stream_direct(prompt):
            response_parts.append(chunk)
        
        response_text = "".join(response_parts)
        extracted = extract_json_from_text(response_text)
        
        if extracted:
            new_mapping = extracted.get("voice_mapping", [])
            if isinstance(extracted, list):
                new_mapping = extracted
            
            self._last_result = {
                "success": True,
                "voice_mapping": new_mapping,
            }
            return self._last_result
        
        return {
            "success": False,
            "error": "无法从响应中提取修改后的音色映射",
        }


def create_voice_matcher(
    model: Optional[str] = None,
    checkpointer=None,
    verbose: bool = True,
) -> VoiceMatcherAgent:
    """创建音色匹配 Agent"""
    return VoiceMatcherAgent(
        model=model,
        checkpointer=checkpointer,
        verbose=verbose,
    )


__all__ = [
    "VoiceMatcherAgent",
    "create_voice_matcher",
    "VOICE_MATCHER_TOOLS",
]
