# 🎤 TTS Agent Standalone

语音合成智能体独立项目 - 基于豆包 TTS 2.0 的智能语音合成系统。

## 📋 功能特性

- **三阶段智能流水线**
  - 阶段一：对话分析 - 智能识别输入类型，生成结构化对话列表
  - 阶段二：音色匹配 - AI 智能为角色匹配最佳音色
  - 阶段三：批量合成 - 高效批量合成语音并自动合并

- **完整的 Web 界面**
  - 现代化 React 前端
  - 实时流式交互
  - 音色试听与预览

- **RESTful API**
  - 完整的 API 接口
  - SSE 流式响应
  - Swagger 文档

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 安装前端依赖
cd frontend && npm install
```

### 2. 配置环境变量

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑 .env 文件，填入你的 API 凭据
```

### 3. 启动服务

```bash
# 启动后端服务
python run.py

# 启动前端开发服务器（新终端）
cd frontend && npm run dev
```

### 4. 访问服务

- 前端页面: http://localhost:5173
- API 文档: http://localhost:8766/docs
- 健康检查: http://localhost:8766/api/tts/health

## 📁 项目结构

```
tts_agent_standalone/
├── agent/                  # Agent 模块
│   ├── dialogue_analyzer.py   # 对话分析 Agent
│   ├── voice_matcher.py       # 音色匹配 Agent
│   ├── controller.py          # 流水线控制器
│   ├── tools.py               # TTS 工具
│   └── ...
├── backend/                # 后端服务
│   ├── api/                   # API 路由
│   ├── models/                # 数据模型
│   ├── services/              # 服务层
│   └── server.py              # FastAPI 服务器
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── components/        # React 组件
│   │   ├── hooks/             # 自定义 Hooks
│   │   ├── services/          # API 服务
│   │   └── pages/             # 页面
│   └── ...
├── data/                   # 数据目录
├── requirements.txt        # Python 依赖
├── run.py                  # 启动脚本
└── README.md
```

## 🔧 API 接口

### 会话管理

- `POST /api/tts/sessions` - 创建会话
- `GET /api/tts/sessions` - 列出会话
- `GET /api/tts/sessions/{id}` - 获取会话详情
- `DELETE /api/tts/sessions/{id}` - 删除会话

### 阶段一：对话分析

- `POST /api/tts/sessions/{id}/analyze` - 分析对话
- `POST /api/tts/sessions/{id}/analyze/stream` - 流式分析
- `POST /api/tts/sessions/{id}/refine` - 修改对话
- `PUT /api/tts/sessions/{id}/dialogues` - 更新对话列表

### 阶段二：音色匹配

- `POST /api/tts/sessions/{id}/match` - 匹配音色
- `POST /api/tts/sessions/{id}/match/stream` - 流式匹配
- `POST /api/tts/sessions/{id}/rematch` - 重新匹配
- `POST /api/tts/sessions/{id}/change-voice` - 更换音色

### 阶段三：批量合成

- `POST /api/tts/sessions/{id}/synthesize` - 批量合成

### 音色管理

- `GET /api/tts/voices` - 获取音色列表
- `GET /api/tts/voices/{id}` - 获取音色详情
- `POST /api/tts/preview` - 音色试听

## 📄 License

MIT License
