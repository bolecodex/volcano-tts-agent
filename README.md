# TTS Agent Standalone

一个“输入要求 → 生成对话 → 音色匹配 → 合成音频”的三阶段语音合成项目，支持本地 FastAPI 服务运行，也支持通过 AgentKit 部署到云端 Runtime，并配合 TOS 静态站点前端访问。

## 功能

- 阶段一：对话分析（可流式输出）
- 阶段二：音色匹配（可流式输出，支持更换音色/试听）
- 阶段三：批量合成与合并（支持返回可播放链接）
- 前端：React + Vite，支持生产构建（`frontend/dist`）

## 本地运行

### 1) 安装依赖

```bash
pip install -r requirements.txt
cd frontend && npm install
```

### 2) 配置环境变量

项目会读取根目录 `.env`（已在 `.gitignore` 中忽略），常用配置如下（按需填写）：

后端（FastAPI）：

- `DOUBAO_TTS_APP_ID`
- `DOUBAO_TTS_ACCESS_TOKEN`
- `DOUBAO_TTS_SECRET_KEY`
- `DOUBAO_TTS_CLUSTER`
- `LLM_API_KEY`
- `LLM_BASE_URL`
- `LLM_MODEL`
- `CORS_ORIGINS`（逗号分隔）

前端（Vite）：

- `VITE_TTS_API_BASE_URL`：云端网关地址（例如 `https://<your-apigw-domain>`）；本地开发可不填
- `VITE_TTS_API_KEY`：云端网关 `key_auth` 的 runtime api key；本地开发可不填

### 3) 启动服务

```bash
python run.py --host 127.0.0.1 --port 8766
cd frontend && npm run dev -- --host 127.0.0.1 --port 5173
```

### 4) 访问

- 前端开发页：http://127.0.0.1:5173
- API 文档：http://127.0.0.1:8766/docs
- 健康检查：http://127.0.0.1:8766/api/tts/health

## 生产构建（前端）

```bash
cd frontend
npm run build
```

构建产物输出到 `frontend/dist/`（该目录为生成物，默认不建议提交到仓库）。

## AgentKit 部署（云端 Runtime）

项目入口为 [tts_agentkit.py](file:///Users/bytedance/Documents/%E5%AE%9E%E9%AA%8C/tts_agent_standalone/tts_agentkit.py)，部署参数见 [agentkit.yaml](file:///Users/bytedance/Documents/%E5%AE%9E%E9%AA%8C/tts_agent_standalone/agentkit.yaml)。

常见做法是在你已有的 AgentKit CLI 环境中执行部署，例如：

```bash
source .venv_agentkit/bin/activate
agentkit deploy
```

云端网关若使用 `key_auth`，请求头需要带：

`Authorization: Bearer <RUNTIME_API_KEY>`

## TOS 音频链接（可选）

当你希望云端返回可直接播放的音频链接时，可在 Runtime 环境中配置：

- `TOS_UPLOAD_ENABLED=1`
- `TOS_BUCKET`
- `TOS_PREFIX`（可选，默认 `tts-agent-output`）
- `TOS_URL_EXPIRES`（可选，默认 3600 秒）
- `TOS_ENDPOINT`
- `TOS_REGION`
- `TOS_ACCESS_KEY` / `TOS_SECRET_KEY`（或复用 `VOLCENGINE_ACCESS_KEY` / `VOLCENGINE_SECRET_KEY`）

## 项目结构

```
tts_agent_standalone/
├── agent/                      # 三阶段流水线与工具
├── backend/                    # FastAPI 服务（/api/tts）
├── frontend/                   # React 前端（Vite）
│   └── src/pages/TTSAgent/      # 主页面与组件
├── tts_agentkit.py             # AgentKit 入口
├── agentkit.yaml               # AgentKit 部署配置
├── requirements.txt
└── run.py
```

## API

更完整的接口说明见 [TTS_Agent_接口指南.md](file:///Users/bytedance/Documents/%E5%AE%9E%E9%AA%8C/tts_agent_standalone/docs/TTS_Agent_%E6%8E%A5%E5%8F%A3%E6%8C%87%E5%8D%97.md)。
