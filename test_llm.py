# -*- coding: utf-8 -*-
"""
测试火山引擎 LLM API 配置
"""

from agent.llm_config import create_llm, get_llm_config

def test_llm():
    """测试 LLM 调用"""
    config = get_llm_config()
    print(f"配置信息:")
    print(f"  - Model: {config.get_model_name()}")
    print(f"  - Base URL: {config.base_url}")
    print(f"  - API Key: {config.api_key[:8]}...{config.api_key[-4:]}")
    print()
    
    print("正在创建 LLM 实例...")
    llm = create_llm()
    
    print("正在发送测试请求...")
    response = llm.invoke("你好，请用一句话介绍你自己。")
    
    print(f"\n✅ 测试成功!")
    print(f"回复: {response.content}")

if __name__ == "__main__":
    test_llm()
