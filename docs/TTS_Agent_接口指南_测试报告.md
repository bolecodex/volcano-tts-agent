# TTS Agent 接口指南测试报告

测试对象文档：[TTS_Agent_接口指南.md](file:///Users/bytedance/Documents/%E5%AE%9E%E9%AA%8C/tts_agent_standalone/docs/TTS_Agent_%E6%8E%A5%E5%8F%A3%E6%8C%87%E5%8D%97.md)

## 测试信息

- 时间（UTC）：2026-01-19 10:00:43
- 本地 Base URL：`http://127.0.0.1:8766/api/tts`
- 云端 Base URL（API 网关）：`https://sd5mu8fjal76cj6rag3dg.apigateway-cn-beijing.volceapi.com/api/tts`
- 云端鉴权：使用 `Authorization: Bearer <RUNTIME_API_KEY>`（Key 已脱敏：`7lj***v5h`）

## 结论概览

- 本地接口基础可用：健康检查、音色查询、会话创建、对话分析（含流式）均可正常返回。
- 本地阶段二匹配存在异常/不稳定：
  - 非流式 `/match` 在 120s 内超时（可能是外部依赖或处理耗时过长）。
  - 流式 `/match/stream` 立即返回错误 `请先确认对话列表`，与已成功执行的 `/confirm-stage1` 结果不一致，建议排查。
- 云端（AgentKit 网关）鉴权生效：
  - 不带鉴权访问 `/health` 返回 401（`key_auth:missing_api_key`）。
  - 带鉴权访问 `/health` 返回 200。
  - 云端会话创建成功，阶段一流式分析（SSE）可正常返回 chunk。

## 详细结果

### 本地（http://127.0.0.1:8766/api/tts）

| 用例 | 方法 | 路径 | 期望 | 实际 | 备注 |
|---|---|---|---|---|---|
| local_health | GET | /health | 200 JSON | 200 | `{"status":"ok","service":"tts-agent"}` |
| local_voice_categories | GET | /voice-categories | 200 JSON | 200 | 返回 5 个分类 |
| local_voices | GET | /voices?limit=3 | 200 JSON | 200 | 返回 voices[0..2] + total |
| local_create_session | POST | /sessions | 200 JSON | 200 | 返回 session_id |
| local_analyze | POST | /sessions/{id}/analyze | 200 JSON | 200 | 耗时约 88s，返回 dialogue_list 等 |
| local_analyze_stream | POST | /sessions/{id}/analyze/stream | 200 SSE | 200 | `content-type: text/event-stream`，可收到 chunk |
| local_confirm_stage1 | POST | /sessions/{id}/confirm-stage1 | 200 JSON | 200 | 返回 `status: dialogue_ready` |
| local_match | POST | /sessions/{id}/match | 200 JSON | 超时 | 120s 超时（Read timeout） |
| local_match_stream | POST | /sessions/{id}/match/stream | 200 SSE | 200 | SSE 最终返回 `success:false,error:\"请先确认对话列表\"` |

流式预览（本地 analyze/stream 前 6 条 data）：

```text
{"type":"chunk","content":"```"}
{"type":"chunk","content":"json"}
{"type":"chunk","content":"\n"}
{"type":"chunk","content":"{"}
{"type":"chunk","content":"\n"}
{"type":"chunk","content":" "}
```

### 云端（https://sd5mu8fjal76cj6rag3dg.apigateway-cn-beijing.volceapi.com/api/tts）

| 用例 | 方法 | 路径 | 期望 | 实际 | 备注 |
|---|---|---|---|---|---|
| cloud_health_no_auth | GET | /health | 401 | 401 | `Consumer authentication failed.`；`x-auth-failure: key_auth:missing_api_key` |
| cloud_health_with_auth | GET | /health | 200 JSON | 200 | `{"status":"ok","service":"tts-agent"}` |
| cloud_create_session | POST | /sessions | 200 JSON | 200 | 返回 session_id |
| cloud_analyze_stream | POST | /sessions/{id}/analyze/stream | 200 SSE | 200 | `content-type: text/event-stream`，可收到 chunk |

流式预览（云端 analyze/stream 前 6 条 data）：

```text
{"type":"chunk","content":"```"}
{"type":"chunk","content":"json"}
{"type":"chunk","content":"\n"}
{"type":"chunk","content":"{"}
{"type":"chunk","content":"\n"}
{"type":"chunk","content":" "}
```

## 风险与建议

- 本地 `/match` 非流式超时 + `/match/stream` 立即返回“请先确认对话列表”，建议优先排查：
  - `TTSPipelineController.stage2_match` 对 `status/dialogue_list` 的前置条件判断是否一致；
  - 流式实现当前是“先收集 chunks 再一次性输出”，如果想要真正边算边推，需要让 `on_chunk` 直接 `yield`；
  - 若 stage2 依赖外部模型/网络，建议对外部调用增加超时与重试，并在日志中打点阶段耗时。
