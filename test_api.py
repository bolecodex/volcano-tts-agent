# -*- coding: utf-8 -*-
"""
TTS Agent API 接口测试脚本

测试项目：
1. 创建会话
2. 对话分析（推理）
3. 会话列表
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:8766"

# 测试结果收集
results = []

def log_result(test_name: str, success: bool, details: dict = None, error: str = None, duration: float = 0):
    """记录测试结果"""
    result = {
        "test": test_name,
        "success": success,
        "duration_ms": round(duration * 1000, 2),
        "details": details,
        "error": error,
    }
    results.append(result)
    
    status = "✅ 通过" if success else "❌ 失败"
    print(f"\n{status} {test_name} ({result['duration_ms']}ms)")
    if details:
        print(f"   详情: {json.dumps(details, ensure_ascii=False, indent=2)[:500]}")
    if error:
        print(f"   错误: {error}")

def test_health():
    """测试健康检查接口"""
    start = time.time()
    try:
        resp = requests.get(f"{BASE_URL}/api/health")
        duration = time.time() - start
        
        if resp.status_code == 200 and resp.json().get("status") == "ok":
            log_result("健康检查 /api/health", True, resp.json(), duration=duration)
        else:
            log_result("健康检查 /api/health", False, error=f"状态码: {resp.status_code}", duration=duration)
    except Exception as e:
        log_result("健康检查 /api/health", False, error=str(e), duration=time.time() - start)

def test_tts_health():
    """测试 TTS 健康检查接口"""
    start = time.time()
    try:
        resp = requests.get(f"{BASE_URL}/api/tts/health")
        duration = time.time() - start
        
        if resp.status_code == 200:
            log_result("TTS 健康检查 /api/tts/health", True, resp.json(), duration=duration)
        else:
            log_result("TTS 健康检查 /api/tts/health", False, error=f"状态码: {resp.status_code}", duration=duration)
    except Exception as e:
        log_result("TTS 健康检查 /api/tts/health", False, error=str(e), duration=time.time() - start)

def test_create_session():
    """测试创建会话接口"""
    start = time.time()
    try:
        resp = requests.post(f"{BASE_URL}/api/tts/sessions", json={})
        duration = time.time() - start
        
        data = resp.json()
        if resp.status_code == 200 and data.get("success") and data.get("session_id"):
            log_result("创建会话 POST /api/tts/sessions", True, {
                "session_id": data["session_id"],
                "status": data.get("status"),
            }, duration=duration)
            return data["session_id"]
        else:
            log_result("创建会话 POST /api/tts/sessions", False, error=str(data), duration=duration)
            return None
    except Exception as e:
        log_result("创建会话 POST /api/tts/sessions", False, error=str(e), duration=time.time() - start)
        return None

def test_get_session(session_id: str):
    """测试获取会话详情"""
    start = time.time()
    try:
        resp = requests.get(f"{BASE_URL}/api/tts/sessions/{session_id}")
        duration = time.time() - start
        
        data = resp.json()
        if resp.status_code == 200 and data.get("success"):
            session_data = data.get("data", {})
            log_result(f"获取会话详情 GET /api/tts/sessions/{session_id[:8]}...", True, {
                "session_id": session_data.get("session_id"),
                "status": session_data.get("status"),
                "dialogue_count": len(session_data.get("dialogue_list", [])),
            }, duration=duration)
        else:
            log_result(f"获取会话详情 GET /api/tts/sessions/{session_id[:8]}...", False, error=str(data), duration=duration)
    except Exception as e:
        log_result(f"获取会话详情", False, error=str(e), duration=time.time() - start)

def test_analyze_dialogue(session_id: str):
    """测试对话分析（推理）接口"""
    start = time.time()
    test_input = """小明：今天天气真好啊！
小红：是啊，我们去公园玩吧。
小明：好主意！我去拿野餐垫。"""
    
    try:
        resp = requests.post(
            f"{BASE_URL}/api/tts/sessions/{session_id}/analyze",
            json={"user_input": test_input},
            timeout=120  # LLM 调用可能需要较长时间
        )
        duration = time.time() - start
        
        data = resp.json()
        if resp.status_code == 200 and data.get("success"):
            dialogue_list = data.get("dialogue_list", [])
            log_result(f"对话分析（推理） POST /api/tts/sessions/.../analyze", True, {
                "dialogue_count": len(dialogue_list),
                "characters": list(set(d.get("character", "") for d in dialogue_list)),
                "sample": dialogue_list[0] if dialogue_list else None,
            }, duration=duration)
            return True
        else:
            log_result(f"对话分析（推理） POST /api/tts/sessions/.../analyze", False, 
                      error=data.get("detail", str(data)), duration=duration)
            return False
    except Exception as e:
        log_result(f"对话分析（推理）", False, error=str(e), duration=time.time() - start)
        return False

def test_list_sessions():
    """测试会话列表接口"""
    start = time.time()
    try:
        resp = requests.get(f"{BASE_URL}/api/tts/sessions")
        duration = time.time() - start
        
        data = resp.json()
        if resp.status_code == 200 and data.get("success"):
            sessions = data.get("sessions", [])
            log_result("会话列表 GET /api/tts/sessions", True, {
                "session_count": len(sessions),
                "sessions": [{"id": s.get("session_id", s.get("id", ""))[:8] + "...", 
                             "status": s.get("status")} for s in sessions[:5]],
            }, duration=duration)
            return sessions
        else:
            log_result("会话列表 GET /api/tts/sessions", False, error=str(data), duration=duration)
            return []
    except Exception as e:
        log_result("会话列表 GET /api/tts/sessions", False, error=str(e), duration=time.time() - start)
        return []

def test_list_voices():
    """测试音色列表接口"""
    start = time.time()
    try:
        resp = requests.get(f"{BASE_URL}/api/tts/voices?limit=5")
        duration = time.time() - start
        
        data = resp.json()
        if resp.status_code == 200 and data.get("success"):
            voices = data.get("voices", [])
            log_result("音色列表 GET /api/tts/voices", True, {
                "total_voices": data.get("total"),
                "sample_voices": [v.get("name", v.get("id", "")) for v in voices[:3]],
            }, duration=duration)
        else:
            log_result("音色列表 GET /api/tts/voices", False, error=str(data), duration=duration)
    except Exception as e:
        log_result("音色列表 GET /api/tts/voices", False, error=str(e), duration=time.time() - start)

def generate_report():
    """生成测试报告"""
    print("\n" + "=" * 60)
    print("                    测试报告")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API 地址: {BASE_URL}")
    print("-" * 60)
    
    passed = sum(1 for r in results if r["success"])
    failed = len(results) - passed
    total_time = sum(r["duration_ms"] for r in results)
    
    print(f"\n📊 测试统计:")
    print(f"   总测试数: {len(results)}")
    print(f"   通过: {passed} ✅")
    print(f"   失败: {failed} ❌")
    print(f"   通过率: {passed/len(results)*100:.1f}%")
    print(f"   总耗时: {total_time:.2f}ms")
    
    print("\n📋 测试详情:")
    print("-" * 60)
    for r in results:
        status = "✅" if r["success"] else "❌"
        print(f"{status} {r['test']}: {r['duration_ms']}ms")
        if r["error"]:
            print(f"   ⚠️ 错误: {r['error'][:100]}")
    
    print("\n" + "=" * 60)
    
    if failed == 0:
        print("🎉 所有测试通过！")
    else:
        print(f"⚠️ 有 {failed} 个测试失败，请检查。")
    
    print("=" * 60)

def main():
    """主测试流程"""
    print("=" * 60)
    print("        TTS Agent API 接口测试")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试服务: {BASE_URL}")
    print("-" * 60)
    
    # 1. 健康检查
    print("\n🔍 测试健康检查接口...")
    test_health()
    test_tts_health()
    
    # 2. 创建会话
    print("\n🔍 测试创建会话接口...")
    session_id = test_create_session()
    
    if session_id:
        # 3. 获取会话详情
        print("\n🔍 测试获取会话详情接口...")
        test_get_session(session_id)
        
        # 4. 对话分析（推理）
        print("\n🔍 测试对话分析（推理）接口...")
        print("   ⏳ 正在调用 LLM 进行推理，请稍候...")
        test_analyze_dialogue(session_id)
        
        # 5. 再次获取会话详情（验证对话列表是否生成）
        print("\n🔍 验证对话列表生成...")
        test_get_session(session_id)
    
    # 6. 会话列表
    print("\n🔍 测试会话列表接口...")
    test_list_sessions()
    
    # 7. 音色列表
    print("\n🔍 测试音色列表接口...")
    test_list_voices()
    
    # 生成报告
    generate_report()

if __name__ == "__main__":
    main()
