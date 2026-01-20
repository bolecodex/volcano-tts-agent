# TTS Agent 接口指南

本文档描述本项目后端（FastAPI）对外暴露的 HTTP API 规范与调用示例。

## Base URL

- 本地开发（默认）：`http://127.0.0.1:8766/api/tts`
- AgentKit（API 网关）：`https://<your-apigw-domain>/api/tts`

## 鉴权

本地开发通常不需要鉴权。

AgentKit 网关（`key_auth`）需要在请求头带：

- `Authorization: Bearer <RUNTIME_API_KEY>`

示例：

```bash
curl -sS -H "Authorization: Bearer <KEY>" \
  "https://<your-apigw-domain>/api/tts/health"
```

## 返回结构约定

大多数接口返回 JSON，常见字段：

- `success`: boolean
- `error`: string（失败时）
- `session_id`: string

流式接口（SSE）返回 `text/event-stream`，每条消息格式为 `data: <json>\n\n`。

## 接口列表

以下接口挂载在 `/api/tts` 下，路由实现见 [tts_api.py](file:///Users/bytedance/Documents/%E5%AE%9E%E9%AA%8C/tts_agent_standalone/backend/api/tts_api.py)。

### 健康检查

- `GET /health`
  - 返回：`{"status":"ok","service":"tts-agent"}`

### 会话管理

- `POST /sessions`
  - Body（可选）：
    - `user_input`: string
    - `project_id`: number
  - 返回：`{ success, session_id, status }`

- `GET /sessions?limit=50&status=<status>`
  - Query：
    - `limit`: 1~200，默认 50
    - `status`: 可选，过滤会话状态
  - 返回：`{ success, sessions }`

- `GET /sessions/{session_id}`
  - 返回：`{ success, data }`

- `DELETE /sessions/{session_id}`
  - 返回：`{ success }`

### 阶段一：对话分析

- `POST /sessions/{session_id}/analyze`（非流式）
  - Body：
    - `user_input`: string

- `POST /sessions/{session_id}/analyze/stream`（流式，SSE）
  - Body：
    - `user_input`: string
  - SSE 消息：
    - `{"type":"chunk","content":"..."}`（多条）
    - `{"type":"result","data":{...}}`（最后一条）

示例（curl 流式读取）：

```bash
curl -N \
  -H "Authorization: Bearer <KEY>" \
  -H "Content-Type: application/json" \
  -d '{"user_input":"写一段两个人的对话"}' \
  "https://<your-apigw-domain>/api/tts/sessions/<SESSION_ID>/analyze/stream"
```

### 阶段一：对话编辑

- `POST /sessions/{session_id}/refine`
  - Body：
    - `instruction`: string
    - `target_indices`: number[]（可选）

- `PUT /sessions/{session_id}/dialogues`
  - Body：
    - `dialogue_list`: object[]（每条对话的结构由前端/流程生成）

- `POST /sessions/{session_id}/confirm-stage1`

### 阶段二：音色匹配

- `POST /sessions/{session_id}/match`（非流式）

- `POST /sessions/{session_id}/match/stream`（流式，SSE）
  - SSE 消息：
    - `{"type":"chunk","content":"..."}`（多条）
    - `{"type":"result","data":{...}}`（最后一条）

- `POST /sessions/{session_id}/rematch`
  - Body：
    - `instruction`: string
    - `target_characters`: string[]（可选）

- `POST /sessions/{session_id}/change-voice`
  - Body：
    - `character`: string
    - `voice_id`: string
    - `voice_name`: string（可选）

- `POST /sessions/{session_id}/confirm-stage2`

### 阶段三：批量合成

- `POST /sessions/{session_id}/synthesize`

### 音频下载

- `GET /audio/{session_id}/{filename}`
  - 返回：`audio/mpeg`（`FileResponse`）

- `GET /sessions/{session_id}/merged-audio`
  - 返回：`audio/mpeg`（`FileResponse`）

### 音色查询

- `GET /voices?category=<category>&gender=<gender>&limit=50`
  - Query：
    - `category`: 可选
    - `gender`: 可选
    - `limit`: 1~200，默认 50
  - 返回：`{ success, voices, total }`

- `GET /voices/{voice_id}`
  - 返回：`{ success, voice }`

- `GET /voice-categories`
  - 返回：`{ success, categories }`

### 试听

- `POST /preview`
  - Body：
    - `voice_id`: string
    - `text`: string（可选）
  - 返回：`audio/mpeg`（`FileResponse`）

示例：

```bash
curl -L \
  -H "Authorization: Bearer <KEY>" \
  -H "Content-Type: application/json" \
  -d '{"voice_id":"xxx","text":"你好，这是一段试听文本。"}' \
  "https://<your-apigw-domain>/api/tts/preview" \
  -o preview.mp3
```
