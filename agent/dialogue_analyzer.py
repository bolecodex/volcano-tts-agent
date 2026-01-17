# -*- coding: utf-8 -*-
"""
🎤 DialogueAnalyzerAgent - 对话分析 Agent

负责分析用户输入，识别输入类型，生成标准化的对话列表
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

from .prompts import DIALOGUE_ANALYZER_SYSTEM_PROMPT
from .models import DialogueItem, InputType, parse_dialogue_list

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
            return {"dialogue_list": json.loads(text[start:end + 1])}
        except json.JSONDecodeError:
            pass
    
    return None


@tool
def save_dialogue_result(dialogue_list_json: str) -> str:
    """
    保存对话分析结果
    
    Args:
        dialogue_list_json: JSON 格式的对话列表
    
    Returns:
        保存结果确认
    """
    try:
        data = json.loads(dialogue_list_json)
        
        if isinstance(data, dict) and "dialogue_list" in data:
            dialogue_list = data["dialogue_list"]
            input_type = data.get("input_type", "unknown")
            
            valid_items = []
            for item in dialogue_list:
                if isinstance(item, dict) and "character" in item and "text" in item:
                    valid_items.append(item)
            
            if valid_items:
                return json.dumps({
                    "success": True,
                    "message": f"✅ 已保存 {len(valid_items)} 条对话记录",
                    "input_type": input_type,
                    "count": len(valid_items),
                    "data": data,
                }, ensure_ascii=False)
            else:
                return json.dumps({
                    "success": False,
                    "error": "对话列表中没有有效的条目",
                }, ensure_ascii=False)
        
        elif isinstance(data, list):
            return json.dumps({
                "success": True,
                "message": f"✅ 已保存 {len(data)} 条对话记录",
                "input_type": "unknown",
                "count": len(data),
                "data": {"dialogue_list": data},
            }, ensure_ascii=False)
        
        else:
            return json.dumps({
                "success": False,
                "error": "格式不正确，请确保包含 dialogue_list 字段",
            }, ensure_ascii=False)
            
    except json.JSONDecodeError as e:
        return json.dumps({
            "success": False,
            "error": f"JSON 解析失败: {e}",
        }, ensure_ascii=False)


DIALOGUE_ANALYZER_TOOLS = [save_dialogue_result]


class DialogueAnalyzerAgent:
    """对话分析 Agent"""
    
    def __init__(
        self,
        model: Optional[str] = None,
        checkpointer=None,
        verbose: bool = True,
        context_file: Optional[str] = None,
    ):
        self.verbose = verbose
        self.model_name = model
        
        self.context_content = ""
        if context_file and os.path.exists(context_file):
            with open(context_file, "r", encoding="utf-8") as f:
                self.context_content = f.read()
        
        # 创建 LLM
        from .llm_config import LLMConfig, get_llm_config
        base_config = get_llm_config()
        
        streaming_config = LLMConfig(
            provider=base_config.provider,
            model=model or base_config.model,
            api_key=base_config.api_key,
            base_url=base_config.base_url,
            temperature=0.7,
            max_tokens=65536,
            streaming=True,
            extra_params=base_config.extra_params,
        )
        self.llm = streaming_config.create_llm()
        
        if checkpointer is None:
            checkpointer = InMemorySaver()
        self.checkpointer = checkpointer
        
        self._agent = None
        self._create_agent()
        
        self._thread_id = f"dialogue_session_{uuid.uuid4().hex[:8]}"
        self._last_result: Optional[Dict[str, Any]] = None
    
    def _log(self, message: str):
        if self.verbose:
            print(message)
    
    def _build_system_prompt(self) -> str:
        prompt = DIALOGUE_ANALYZER_SYSTEM_PROMPT
        if self.context_content:
            prompt += "\n\n## 参考：豆包2.0指令格式\n\n"
            prompt += self.context_content[:3000] + "\n..."
        return prompt
    
    def _create_agent(self):
        try:
            from langgraph.prebuilt import create_react_agent
            
            self._agent = create_react_agent(
                model=self.llm,
                tools=DIALOGUE_ANALYZER_TOOLS,
                prompt=self._build_system_prompt(),
                checkpointer=self.checkpointer,
            )
            self._log("🚀 对话分析 Agent 已启动")
        except ImportError as e:
            self._log(f"⚠️ 无法导入 langgraph: {e}")
            self._agent = None
    
    @property
    def agent(self):
        return self._agent
    
    @property
    def thread_id(self) -> str:
        return self._thread_id
    
    @thread_id.setter
    def thread_id(self, value: str):
        self._thread_id = value
    
    def new_session(self) -> str:
        self._thread_id = f"dialogue_session_{uuid.uuid4().hex[:8]}"
        self._last_result = None
        self._log(f"🗑️ 已开启新对话! ID: {self._thread_id}")
        return self._thread_id
    
    def chat(self, message: str, thread_id: Optional[str] = None) -> str:
        if self._agent is None:
            return "❌ Agent 未初始化"
        
        if thread_id:
            self._thread_id = thread_id
        
        config = {"configurable": {"thread_id": self._thread_id}}
        
        result = self._agent.invoke(
            {"messages": [{"role": "user", "content": message}]},
            config=config
        )
        
        if "messages" in result:
            return result["messages"][-1].content
        return str(result)
    
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
    
    async def analyze(self, user_input: str) -> Dict[str, Any]:
        """分析用户输入"""
        return await self.analyze_stream(user_input, on_chunk=None)
    
    async def analyze_stream(
        self,
        user_input: str,
        on_chunk: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """分析用户输入（流式输出）"""
        prompt = f"""请分析以下输入，生成对话列表。

## 输入内容
{user_input}

## 输出要求
请按照系统提示词的要求，识别输入类型并直接输出以下 JSON 格式：

```json
{{
  "input_type": "topic|article|dialogue",
  "dialogue_list": [
    {{
      "index": 1,
      "character": "角色名",
      "character_desc": "角色描述（性别、年龄、身份等）",
      "text": "台词内容",
      "instruction": "[#语音指令]",
      "context": "场景上下文描述"
    }}
  ]
}}
```

请直接输出 JSON 内容，不要调用任何工具。"""
        
        self.new_session()
        
        response_parts: List[str] = []
        for chunk in self._stream_direct(prompt):
            response_parts.append(chunk)
            if on_chunk:
                on_chunk(chunk)
        
        response_text = "".join(response_parts)
        return self._parse_json_result(response_text)
    
    def _parse_json_result(self, response_text: str) -> Dict[str, Any]:
        """从 LLM 响应中解析 JSON 结果"""
        logger.info(f"📝 LLM 响应长度: {len(response_text)} 字符")
        
        extracted = extract_json_from_text(response_text)
        if extracted:
            dialogue_list = extracted.get("dialogue_list", [])
            if isinstance(extracted, list):
                dialogue_list = extracted
            
            input_type = extracted.get("input_type", "unknown")
            
            logger.info(f"✅ 成功解析 {len(dialogue_list)} 条对话, 输入类型: {input_type}")
            
            self._last_result = {
                "success": True,
                "input_type": input_type,
                "dialogue_list": dialogue_list,
            }
            return self._last_result
        
        logger.error(f"❌ JSON 解析失败")
        return {
            "success": False,
            "error": "无法从响应中提取对话列表",
            "raw_response": response_text[:1000] if response_text else "(空响应)",
        }
    
    async def refine(
        self,
        dialogue_list: List[Dict[str, Any]],
        instruction: str,
        target_indices: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """对话式修改"""
        indices_info = ""
        if target_indices:
            indices_info = f"请重点修改第 {', '.join(map(str, target_indices))} 条对话。"
        
        prompt = f"""请根据以下指令修改对话列表：

## 当前对话列表
```json
{json.dumps(dialogue_list, ensure_ascii=False, indent=2)}
```

## 修改指令
{instruction}

{indices_info}

修改完成后，输出完整的 JSON 对话列表。"""
        
        response_parts: List[str] = []
        for chunk in self._stream_direct(prompt):
            response_parts.append(chunk)
        
        response_text = "".join(response_parts)
        extracted = extract_json_from_text(response_text)
        
        if extracted:
            new_list = extracted.get("dialogue_list", [])
            if isinstance(extracted, list):
                new_list = extracted
            
            self._last_result = {
                "success": True,
                "dialogue_list": new_list,
            }
            return self._last_result
        
        return {
            "success": False,
            "error": "无法从响应中提取修改后的对话列表",
        }


def create_dialogue_analyzer(
    model: Optional[str] = None,
    checkpointer=None,
    verbose: bool = True,
    context_file: Optional[str] = None,
) -> DialogueAnalyzerAgent:
    """创建对话分析 Agent"""
    return DialogueAnalyzerAgent(
        model=model,
        checkpointer=checkpointer,
        verbose=verbose,
        context_file=context_file,
    )


__all__ = [
    "DialogueAnalyzerAgent",
    "create_dialogue_analyzer",
    "DIALOGUE_ANALYZER_TOOLS",
    "extract_json_from_text",
]
