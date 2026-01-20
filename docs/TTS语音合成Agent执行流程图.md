# 🎤 TTS 语音合成 Agent 执行流程图

> 本文档描述 TTS Agent 的完整执行流程、架构设计和组件交互关系。

---

## 一、系统架构总览

```mermaid
graph TB
    subgraph "TTS Agent 系统架构"
        Controller["TTSPipelineController<br/>流水线控制器"]
        
        subgraph "智能体层"
            DA["DialogueAnalyzerAgent<br/>对话分析智能体"]
            VM["VoiceMatcherAgent<br/>音色匹配智能体"]
        end
        
        subgraph "工具层"
            Tools1["save_dialogue_result"]
            Tools2["get_available_voices"]
            Tools3["generate_voice_preview"]
            Tools4["recommend_voice_for_character"]
            Tools5["tts_preview"]
            Tools6["tts_synthesize_batch"]
            Tools7["audio_merge"]
        end
        
        subgraph "数据层"
            Service["TTSSessionService<br/>业务服务"]
            Repo["TTSSessionRepository<br/>数据仓库"]
            DB[(SQLite DB)]
        end
        
        subgraph "外部服务"
            TTS["豆包 TTS 2.0<br/>语音合成服务"]
            LLM["DeepAgent<br/>大语言模型"]
        end
    end
    
    Controller --> DA
    Controller --> VM
    DA --> Tools1
    DA --> LLM
    VM --> Tools2
    VM --> Tools3
    VM --> Tools4
    VM --> LLM
    Controller --> Tools5
    Controller --> Tools6
    Controller --> Tools7
    Tools5 --> TTS
    Tools6 --> TTS
    Service --> Repo
    Repo --> DB
    Controller --> Service
```

---

## 二、三阶段流水线执行流程

```mermaid
flowchart TD
    Start([用户输入]) --> S1

    subgraph S1["阶段一：对话分析"]
        S1_1[接收用户输入] --> S1_2{识别输入类型}
        S1_2 -->|主题 topic| S1_3[AI 生成对话]
        S1_2 -->|长文 article| S1_4[AI 提取对话]
        S1_2 -->|对话 dialogue| S1_5[AI 解析格式]
        S1_3 --> S1_6[生成对话列表]
        S1_4 --> S1_6
        S1_5 --> S1_6
        S1_6 --> S1_7[调用 save_dialogue_result 工具]
        S1_7 --> S1_8[保存到数据库]
    end

    S1_8 --> S1_Ready([DIALOGUE_READY])
    S1_Ready --> S2

    subgraph S2["阶段二：音色匹配"]
        S2_1[加载对话列表] --> S2_2[提取角色列表]
        S2_2 --> S2_3[分析角色特征]
        S2_3 --> S2_4[查询可用音色]
        S2_4 --> S2_5[AI 匹配最佳音色]
        S2_5 --> S2_6[生成试听音频]
        S2_6 --> S2_7[调用 save_voice_mapping_result 工具]
        S2_7 --> S2_8[保存到数据库]
    end

    S2_8 --> S2_Ready([VOICE_READY])
    S2_Ready --> S3

    subgraph S3["阶段三：批量合成"]
        S3_1[加载对话列表和音色映射] --> S3_2[构建合成任务]
        S3_2 --> S3_3[批量调用 TTS API]
        S3_3 --> S3_4[生成各句音频文件]
        S3_4 --> S3_5[音频合并处理]
        S3_5 --> S3_6[保存合成结果]
    end

    S3_6 --> Complete([COMPLETED])

    style S1 fill:#e1f5fe
    style S2 fill:#fff3e0
    style S3 fill:#e8f5e9
```

---

## 三、会话状态流转图

```mermaid
stateDiagram-v2
    [*] --> CREATED: 创建会话
    
    CREATED --> ANALYZING: stage1_analyze()
    ANALYZING --> DIALOGUE_READY: 分析完成
    ANALYZING --> ERROR: 分析失败
    
    DIALOGUE_READY --> DIALOGUE_READY: stage1_refine() / stage1_update()
    DIALOGUE_READY --> MATCHING: stage2_match()
    
    MATCHING --> VOICE_READY: 匹配完成
    MATCHING --> ERROR: 匹配失败
    
    VOICE_READY --> VOICE_READY: stage2_rematch() / stage2_change_voice()
    VOICE_READY --> SYNTHESIZING: stage3_synthesize()
    
    SYNTHESIZING --> COMPLETED: 合成完成
    SYNTHESIZING --> ERROR: 合成失败
    
    COMPLETED --> [*]
    ERROR --> [*]
    
    note right of DIALOGUE_READY
        支持对话式修改
        支持手动更新对话列表
    end note
    
    note right of VOICE_READY
        支持重新匹配音色
        支持手动更换音色
    end note
```

---

## 四、核心组件交互时序图

```mermaid
sequenceDiagram
    participant User as 用户/API
    participant Ctrl as TTSPipelineController
    participant DA as DialogueAnalyzerAgent
    participant VM as VoiceMatcherAgent
    participant TTS as 豆包 TTS API
    participant DB as 数据库

    %% 阶段一
    User->>Ctrl: stage1_analyze(user_input)
    Ctrl->>DB: 创建/加载会话
    Ctrl->>Ctrl: 更新状态 → ANALYZING
    Ctrl->>DA: analyze(user_input)
    DA->>DA: 构建 System Prompt
    DA->>DA: 调用 LLM 分析
    DA->>DA: 调用 save_dialogue_result 工具
    DA-->>Ctrl: 返回对话列表
    Ctrl->>DB: 保存对话列表
    Ctrl->>Ctrl: 更新状态 → DIALOGUE_READY
    Ctrl-->>User: 返回分析结果

    %% 阶段二
    User->>Ctrl: stage2_match()
    Ctrl->>Ctrl: 更新状态 → MATCHING
    Ctrl->>VM: match(dialogue_list)
    VM->>VM: 构建匹配 Prompt
    VM->>VM: 调用 get_available_voices
    VM->>VM: 调用 recommend_voice_for_character
    VM->>TTS: generate_voice_preview
    TTS-->>VM: 返回试听音频
    VM->>VM: 调用 save_voice_mapping_result 工具
    VM-->>Ctrl: 返回音色映射
    Ctrl->>DB: 保存音色映射
    Ctrl->>Ctrl: 更新状态 → VOICE_READY
    Ctrl-->>User: 返回匹配结果

    %% 阶段三
    User->>Ctrl: stage3_synthesize()
    Ctrl->>Ctrl: 更新状态 → SYNTHESIZING
    loop 每句对话
        Ctrl->>TTS: tts_synthesize_batch
        TTS-->>Ctrl: 返回音频文件
    end
    Ctrl->>Ctrl: audio_merge 合并音频
    Ctrl->>DB: 保存合成结果
    Ctrl->>Ctrl: 更新状态 → COMPLETED
    Ctrl-->>User: 返回合成结果
```

---

## 五、数据模型关系图

```mermaid
erDiagram
    TTSSession ||--o{ TTSDialogueItem : contains
    TTSSession ||--o{ TTSVoiceMapping : contains
    
    TTSSession {
        int id PK
        string session_id UK
        string status
        string user_input
        string input_type
        string output_dir
        string merged_audio_path
        int total_duration_ms
        string error
        string error_stage
        datetime created_at
        datetime updated_at
    }
    
    TTSDialogueItem {
        int id PK
        int session_id FK
        int item_index
        string character
        string character_desc
        string text
        string instruction
        string context
        string audio_path
        int duration_ms
    }
    
    TTSVoiceMapping {
        int id PK
        int session_id FK
        string character UK
        string voice_id
        string voice_name
        string reason
        string preview_audio
        string preview_text
    }
```

---

## 六、DialogueAnalyzerAgent 内部流程

```mermaid
flowchart TD
    subgraph "DialogueAnalyzerAgent 执行流程"
        Start([接收用户输入]) --> Build[构建 System Prompt]
        Build --> Call[调用 DeepAgent]
        
        Call --> Process{LLM 处理}
        Process --> Think[思考分析]
        Think --> Identify[识别输入类型]
        
        Identify -->|topic| Generate[生成对话内容]
        Identify -->|article| Extract[提取对话内容]
        Identify -->|dialogue| Parse[解析对话格式]
        
        Generate --> Format[格式化对话列表]
        Extract --> Format
        Parse --> Format
        
        Format --> Tool[调用 save_dialogue_result 工具]
        Tool --> Validate{验证 JSON}
        
        Validate -->|成功| Return[返回结构化结果]
        Validate -->|失败| Retry[重试解析]
        Retry --> Tool
        
        Return --> End([输出对话列表])
    end

    style Generate fill:#bbdefb
    style Extract fill:#c8e6c9
    style Parse fill:#fff9c4
```

---

## 七、VoiceMatcherAgent 内部流程

```mermaid
flowchart TD
    subgraph "VoiceMatcherAgent 执行流程"
        Start([接收对话列表]) --> Extract[提取角色列表]
        Extract --> Analyze[分析角色特征]
        
        Analyze --> Query[查询可用音色库]
        Query --> Tools1[get_available_voices]
        Query --> Tools2[recommend_voice_for_character]
        
        Tools1 --> Match[AI 匹配决策]
        Tools2 --> Match
        
        Match --> Preview[生成试听音频]
        Preview --> Tools3[generate_voice_preview]
        Tools3 --> TTS[调用 TTS API]
        TTS --> Audio[获取音频文件]
        
        Audio --> Build[构建音色映射]
        Build --> Tool[调用 save_voice_mapping_result 工具]
        Tool --> Validate{验证结果}
        
        Validate -->|成功| Return[返回音色映射]
        Validate -->|失败| Retry[重试]
        Retry --> Match
        
        Return --> End([输出音色映射])
    end

    style Match fill:#ffccbc
    style Preview fill:#d1c4e9
```

---

## 八、工具调用关系图

```mermaid
graph LR
    subgraph "对话分析工具"
        T1[save_dialogue_result]
    end
    
    subgraph "音色匹配工具"
        T2[save_voice_mapping_result]
        T3[get_available_voices]
        T4[generate_voice_preview]
        T5[recommend_voice_for_character]
    end
    
    subgraph "TTS 合成工具"
        T6[tts_preview]
        T7[tts_synthesize]
        T8[tts_synthesize_batch]
        T9[audio_merge]
        T10[get_voice_list]
    end
    
    DA[DialogueAnalyzerAgent] --> T1
    VM[VoiceMatcherAgent] --> T2
    VM --> T3
    VM --> T4
    VM --> T5
    
    Ctrl[TTSPipelineController] --> T6
    Ctrl --> T7
    Ctrl --> T8
    Ctrl --> T9
    Ctrl --> T10
    
    T4 --> TTS[豆包 TTS API]
    T6 --> TTS
    T7 --> TTS
    T8 --> TTS
    
    style DA fill:#e3f2fd
    style VM fill:#fff3e0
    style Ctrl fill:#e8f5e9
    style TTS fill:#fce4ec
```

---

## 九、使用方式

### 方式一：使用流水线控制器（推荐）

```python
from agents.tts_agent import create_tts_pipeline

pipeline = create_tts_pipeline()

# 阶段一：分析输入
result = await pipeline.stage1_analyze("职场面试")
print(result["dialogue_list"])

# 阶段二：匹配音色
result = await pipeline.stage2_match()
print(result["voice_mapping"])

# 阶段三：批量合成
result = await pipeline.stage3_synthesize()
print(result["merged_audio"])
```

### 方式二：直接使用 Agent

```python
from agents.tts_agent import DialogueAnalyzerAgent, VoiceMatcherAgent

# 对话分析
analyzer = DialogueAnalyzerAgent()
result = await analyzer.analyze("恋人分手")

# 音色匹配
matcher = VoiceMatcherAgent()
result = await matcher.match(dialogue_list)
```

### 方式三：命令行使用

```bash
# 交互模式
python -m agents.tts_agent -i

# 单次分析
python -m agents.tts_agent -q "职场面试"

# 完整流水线
python -m agents.tts_agent --pipeline "职场面试"

# 查看音色列表
python -m agents.tts_agent --voices
```

---

## 十、文件结构

```
agents/tts_agent/
├── __init__.py              # 模块入口，导出所有组件
├── __main__.py              # 命令行入口
├── controller.py            # TTSPipelineController 流水线控制器
├── dialogue_analyzer.py     # DialogueAnalyzerAgent 对话分析智能体
├── voice_matcher.py         # VoiceMatcherAgent 音色匹配智能体
├── models.py                # 数据模型定义
├── prompts.py               # 提示词模板
├── templates.py            # 音色模板和辅助函数
├── tools.py                 # TTS 工具函数
├── db_service.py            # 业务逻辑服务层
└── session_repository.py    # 数据库 CRUD 仓库
```

---

## 十一、豆包 TTS 2.0 服务执行流程

### 11.1 服务架构总览

```mermaid
graph TB
    subgraph "豆包 TTS 2.0 服务架构"
        subgraph "应用层"
            Agent["TTS Agent"]
            Tools["TTS Tools"]
            API["TTS Router (FastAPI)"]
        end
        
        subgraph "服务层"
            Service["DoubaoTTSService<br/>语音合成服务"]
        end
        
        subgraph "模型层"
            Config["TTSConfig<br/>配置参数"]
            Result["TTSResult<br/>合成结果"]
            Models["VoicePresets<br/>音色预设"]
        end
        
        subgraph "外部服务"
            V3API["火山引擎 TTS V3 API<br/>openspeech.bytedance.com"]
        end
    end
    
    Agent --> Tools
    Tools --> Service
    API --> Service
    Service --> Config
    Service --> Result
    Service --> V3API
    Config --> Models
    
    style Service fill:#e3f2fd
    style V3API fill:#fce4ec
```

---

### 11.2 同步合成流程详解

```mermaid
flowchart TD
    Start([synthesize 调用]) --> GenReqId[生成请求 UUID]
    GenReqId --> BuildPayload[构建请求体]
    
    subgraph "请求体构建 _build_request_payload"
        BuildPayload --> Audio[构建 audio_params]
        Audio --> Speed[语速转换<br/>speed_ratio → speech_rate]
        Speed --> Volume[音量转换<br/>loudness_ratio → loudness_rate]
        Volume --> Emotion{是否启用情感?}
        Emotion -->|是| EmotionSet[设置 emotion 和 emotion_scale]
        Emotion -->|否| Language{是否设置语种?}
        EmotionSet --> Language
        Language -->|是| LangSet[设置 explicit_language]
        Language -->|否| Context{是否有上下文?}
        LangSet --> Context
        Context -->|是| CtxSet[设置 context_texts]
        Context -->|否| Assemble[组装完整 payload]
        CtxSet --> Assemble
    end
    
    Assemble --> Headers[构建请求头]
    
    subgraph "请求头 _get_headers"
        Headers --> AppId[X-Api-App-Id]
        Headers --> Token[X-Api-Access-Key]
        Headers --> ResId[X-Api-Resource-Id]
        Headers --> ReqId[X-Api-Request-Id]
    end
    
    ReqId --> StreamReq[发起流式 HTTP POST 请求]
    StreamReq --> CheckStatus{HTTP 状态码}
    
    CheckStatus -->|200| StreamRead[流式读取响应]
    CheckStatus -->|错误| HttpError[返回 HTTP 错误]
    
    subgraph "流式响应处理"
        StreamRead --> IterLines[遍历响应行]
        IterLines --> ParseJson[解析 JSON]
        ParseJson --> CheckCode{检查 code}
        CheckCode -->|0| GetData[获取 audio base64 数据]
        CheckCode -->|20000000| Done[合成完成]
        CheckCode -->|其他| ApiError[API 错误]
        GetData --> Decode[Base64 解码]
        Decode --> Collect[收集音频块]
        Collect --> IterLines
    end
    
    Done --> Merge[合并所有音频块]
    Merge --> SaveCheck{是否保存文件?}
    SaveCheck -->|是| Save[保存到文件 _save_audio]
    SaveCheck -->|否| Return[返回 TTSResult]
    Save --> Return
    
    HttpError --> Return
    ApiError --> Return
    
    Return --> End([返回结果])

    style BuildPayload fill:#e8f5e9
    style Headers fill:#fff3e0
    style StreamRead fill:#e3f2fd
```

---

### 11.3 请求体结构

```mermaid
graph TD
    subgraph "V3 API 请求体结构"
        Payload["payload (dict)"]
        
        User["user"]
        ReqParams["req_params"]
        
        UID["uid: 'novel_split_user'"]
        
        Text["text: 合成文本"]
        Speaker["speaker: 音色ID"]
        AudioParams["audio_params"]
        Additions["additions (可选)"]
        Model["model (可选)"]
        
        Format["format: mp3/wav/pcm"]
        SampleRate["sample_rate: 24000"]
        SpeechRate["speech_rate: -50~100"]
        LoudnessRate["loudness_rate: -50~100"]
        Emotion["emotion (可选)"]
        EmotionScale["emotion_scale (可选)"]
        
        ExplicitLang["explicit_language (可选)"]
        ContextTexts["context_texts (可选)"]
        
        Payload --> User
        Payload --> ReqParams
        
        User --> UID
        
        ReqParams --> Text
        ReqParams --> Speaker
        ReqParams --> AudioParams
        ReqParams --> Additions
        ReqParams --> Model
        
        AudioParams --> Format
        AudioParams --> SampleRate
        AudioParams --> SpeechRate
        AudioParams --> LoudnessRate
        AudioParams --> Emotion
        AudioParams --> EmotionScale
        
        Additions --> ExplicitLang
        Additions --> ContextTexts
    end
    
    style Payload fill:#ffecb3
    style AudioParams fill:#c8e6c9
    style Additions fill:#bbdefb
```

---

### 11.4 资源 ID 与音色类型映射

```mermaid
graph LR
    subgraph "资源 ID 映射"
        TTS1["seed-tts-1.0<br/>豆包语音合成 1.0"]
        TTS2["seed-tts-2.0<br/>豆包语音合成 2.0"]
        ICL1["seed-icl-1.0<br/>声音复刻 1.0"]
        ICL2["seed-icl-2.0<br/>声音复刻 2.0"]
    end
    
    subgraph "音色类型举例"
        V2_Female["zh_female_*_uranus_bigtts<br/>2.0 女声"]
        V2_Male["zh_male_*_uranus_bigtts<br/>2.0 男声"]
        V1_Female["zh_female_*_mars_bigtts<br/>1.0 女声"]
        Emo["*_emo_v2_mars_bigtts<br/>多情感音色"]
        ICL["ICL_zh_*_tob<br/>角色扮演音色"]
    end
    
    TTS2 --> V2_Female
    TTS2 --> V2_Male
    TTS1 --> V1_Female
    TTS1 --> Emo
    ICL1 --> ICL
    
    style TTS2 fill:#c8e6c9
    style TTS1 fill:#fff9c4
    style ICL1 fill:#bbdefb
```

---

### 11.5 错误处理流程

```mermaid
flowchart TD
    Request([发起请求]) --> Timeout{超时?}
    Timeout -->|是| TimeoutErr[返回超时错误]
    Timeout -->|否| HttpCheck{HTTP 状态}
    
    HttpCheck -->|非200| HttpErr[返回 HTTP 错误<br/>包含状态码和错误信息]
    HttpCheck -->|200| ParseResp[解析响应]
    
    ParseResp --> JsonCheck{JSON 解析}
    JsonCheck -->|失败| JsonWarn[记录警告<br/>继续处理]
    JsonCheck -->|成功| CodeCheck{检查 code}
    
    CodeCheck -->|0| Success[正常数据]
    CodeCheck -->|20000000| Complete[合成完成]
    CodeCheck -->|其他| ApiErr[返回 API 错误<br/>包含 code 和 message]
    
    Success --> Continue[继续收集数据]
    JsonWarn --> Continue
    
    Continue --> NoData{是否收到数据?}
    NoData -->|否| NoDataErr[返回"未收到音频数据"错误]
    NoData -->|是| Final[返回成功结果]
    
    TimeoutErr --> Result([TTSResult])
    HttpErr --> Result
    ApiErr --> Result
    NoDataErr --> Result
    Final --> Result
    Complete --> Final

    style TimeoutErr fill:#ffcdd2
    style HttpErr fill:#ffcdd2
    style ApiErr fill:#ffcdd2
    style NoDataErr fill:#ffcdd2
    style Final fill:#c8e6c9
```

---

### 11.6 TTSConfig 配置参数详解

```mermaid
graph TB
    subgraph "TTSConfig 配置项"
        Required["必填参数"]
        Audio["音频参数"]
        Emotion["情感参数"]
        Other["其他参数"]
        
        VoiceType["voice_type<br/>音色 ID"]
        
        Encoding["encoding<br/>mp3/wav/pcm/ogg_opus"]
        SpeedRatio["speed_ratio<br/>0.1 ~ 2.0"]
        SampleRate["sample_rate<br/>8000/16000/24000"]
        Bitrate["bitrate<br/>仅 MP3"]
        LoudnessRatio["loudness_ratio<br/>0.5 ~ 2.0"]
        
        EmotionType["emotion<br/>情感类型"]
        EnableEmotion["enable_emotion<br/>是否启用"]
        EmotionScale["emotion_scale<br/>1 ~ 5"]
        
        Model["model<br/>模型版本"]
        ExplicitLang["explicit_language<br/>语种"]
    end
    
    Required --> VoiceType
    
    Audio --> Encoding
    Audio --> SpeedRatio
    Audio --> SampleRate
    Audio --> Bitrate
    Audio --> LoudnessRatio
    
    Emotion --> EmotionType
    Emotion --> EnableEmotion
    Emotion --> EmotionScale
    
    Other --> Model
    Other --> ExplicitLang
    
    style Required fill:#ffcdd2
    style Audio fill:#c8e6c9
    style Emotion fill:#bbdefb
    style Other fill:#fff9c4
```

---

### 11.7 豆包 TTS 服务文件结构

```
backend/doubao_tts_v2/
├── __init__.py          # 模块入口，导出所有组件
├── config.py            # 配置项（APP_ID, ACCESS_TOKEN 等）
├── models.py            # 数据模型（TTSConfig, TTSResult, VoicePresets）
├── service.py           # DoubaoTTSService 核心服务（V3 API 封装）
├── tts_db_models.py     # 数据库模型（SQLAlchemy）
├── tts_api_models.py    # API 请求/响应模型（Pydantic）
├── tts_router.py        # FastAPI 路由器
├── example.py           # 使用示例
└── test_tts.py          # 测试脚本
```

---

### 11.8 使用示例

```python
from backend.doubao_tts_v2 import DoubaoTTSService, TTSConfig, VoicePresets

# 创建服务实例
tts = DoubaoTTSService(
    app_id="your_app_id",
    access_token="your_access_token",
    resource_id="seed-tts-2.0",  # 使用 2.0 模型
)

# 配置音色和参数
config = TTSConfig(
    voice_type=VoicePresets.VIVI_2,  # Vivi 2.0 女声
    encoding="mp3",
    speed_ratio=1.0,
    loudness_ratio=1.0,
)

# 同步合成
result = tts.synthesize(
    text="你好，我是豆包语音助手。",
    config=config,
    output_path="output.mp3",
)

if result.success:
    print(f"合成成功: {result.audio_path}")
else:
    print(f"合成失败: {result.error_message}")
```
