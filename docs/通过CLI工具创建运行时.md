
文档中心
火山方舟大模型服务平台
豆包语音
扣子
API网关
云服务器
火山方舟大模型服务平台
豆包语音
扣子
API网关
云服务器
文档
备案
控制台
z
zhaoweibo.0820 / eps_yxd_group
账号管理
账号ID : 2108323502
联邦登陆
企业认证
费用中心
可用余额¥ 0.00
充值汇款
账户总览
账单详情
费用分析
发票管理
权限与安全
安全设置
访问控制
操作审计
API 访问密钥
工具与其他
公测申请
资源管理
配额中心
伙伴控制台
待办事项
待支付
0
待续费
0
待处理工单
0
未读消息
0
AgentKit
文档指南
请输入

文档首页

AgentKit

用户指南

智能体运行时

通过CLI工具创建运行时

复制全文
我的收藏
通过CLI工具创建运行时
本文以预置CLI Agent模版为例，介绍如何在本地使用AgentKit CLI工具将本地代码部署到云上AgentKit智能体运行时。​
背景介绍​
AgentKit CLI是一个命令行工具，用于简化Agent应用的全生命周期管理，包括初始化、配置、构建、部署和运维。当前CLI已预置以下Agent示例模板供您选择，您也可以使用自研代码：​
Basic Agent App：最简单的Agent应用，快速上手。​
Basic Stream Agent App：支持流式输出的Agent应用，使用VeADK。​
前提条件​
已安装Python，且版本不低于3.10。查看Python版本的命令示例：python --version。​
已开通AgentKit服务，已开通镜像仓库服务。​
已开通火山方舟模型服务，并获取API Key和推理接入点ID。详情请参见获取API Key和什么是推理接入点。​
登录平台控制台获取AK/SK，进入 API访问密钥 页面，创建并获取 Access Key ID 和 Secret Access Key，并在本地环境设置环境变量：​
​
export VOLCENGINE_ACCESS_KEY=<your_access_key>​
export VOLCENGINE_SECRET_KEY=<your_secret_key>​
​
步骤一：创建Agent​
推荐您使用uv包管理工具来安装AgentKit SDK，以确保AgentKit SDK安装不会影响系统其他Python项目，也不会被其他项目的依赖影响。其他安装方法，请参见安装AgentKit CLI。​
执行以下命令，下载安装uv和AgentKit SDK。​
​
# 使用curl下载并安装uv​
curl -LsSf https://astral.sh/uv/install.sh | sh​
​
# 初始化uv环境​
uv init --no-workspace​
​
# 使用uv创建一个基于Python 3.12版本的虚拟环境​
uv venv --python 3.12​
​
# 安装AgentKit SDK​
uv add agentkit-sdk-python​
​
# 安装VeADK​
uv add veadk-python​
​
# 激活uv环境​
source .venv/bin/activate​
​
验证AgentKit CLI工具是否可用。​
​
agentkit --version​
​
如果成功显示版本号，说明安装完成。​
​​​
​
创建项目目录并初始化应用。​
​
mkdir simple-agent && cd simple-agent​
#使用CLI预置代码时，执行本命令创建目录并初始化应用​
agentkit init​
#使用自研代码初始化应用时，执行本命令创建目录并初始化应用并将my_agent.py替换为代码文件名​
agentkit init --from-agent ./my_agent.py ​
​
使用CLI预置代码时，会显示如下可用列表：​
​​​
本文以选择AgentKit预置模板“1（Basic Agent APP）”为例，自动生成以下文件：​
simple_agent.py ：Agent应用入口文件。​
requirements.txt：Python依赖。​
agentkit.yaml ：配置文件。​
.dockerignore：构建Docker时需要忽略的文件或目录。​
（可选）使用交互式配置向导设置部署参数：​
​
agentkit config​
​
配置向导会引导您完成以下设置，按Enter键表示使用默认配置：​
​
参数​
说明​
通用配置​
应用名称​
Agent应用名称，默认为simple_app。​
入口文件​
Agent应用入口文件，默认为simple_agent.py。​
应用描述​
应用的描述信息。​
Python 版本​
默认为 3.12。​
依赖文件​
默认为requirements.txt。​
环境变量​
配置智能体运行时可读取的环境变量。​
MODEL_AGENT_NAME=方舟模型接入点 ID（可选）​
MODEL_AGENT_API_KEY=方舟模型 API Key（必填）​
部署模式​
支持三种部署模式，本例中选择cloud。​
local：本地构建和部署。​
hybird： 本地构建，云端部署。​
cloud：云端构建和部署。​
云端部署配置​
Region​
指定本地代码（Agent）上传至CR镜像仓库的地域，默认为cn-beijing。​
CR镜像仓库​
CR实例名称、命名空间和仓库名，默认自动生成。​
​
配置完成后，会将以上内容写入agentkit.yaml配置文件。您也可以执行cat agentkit.yaml命令进入配置文件，查看Agent源数据信息。​
步骤二：部署Agent​
执行以下命令，将应用构建并部署到AgentKit智能体运行时。​
​
agentkit launch​
​
说明​
首次部署大约需要 2～3 分钟，请耐心等待。​
当回显智能体运行时状态为Ready时，则表示创建成功。​
​​​
登录AgentKit控制台，可以查看已部署的智能体运行时实例及其详细信息。​
​​​
步骤三：调试Agent​
创建成功后，支持通过控制台或通过curl命令验证Agent是否正常工作。详情请参见调试Agent。​
步骤四：观测Agent​
调试成功后，您可以在“数据观测”页面查看Agent的运行时监控、会话分析、Trace分析、模型监控、日志分析。详情请参见观测概览。​
相关操作​
查看智能体运行时运行状态​
​
agentkit status​
​
回显如下，表示正常运行：​
​​​
清理资源​
删除智能体运行时实例，请谨慎操作。按“y”键确认后会删除智能体运行时及相关资源。​
​
agentkit destroy​
​
回显如下，表示删除成功：​
​​​
最近更新时间：2026.01.12 10:53:37
这个页面对您有帮助吗？
有用
无用
上一篇：
运行时概述
通过控制台创建运行时
下一篇
背景介绍
前提条件
步骤一：创建Agent
步骤二：部署Agent
步骤三：调试Agent
步骤四：观测Agent
相关操作
查看智能体运行时运行状态
清理资源

鼠标选中内容，快速反馈问题
选中存在疑惑的内容，即可快速反馈问题，我们将会跟进处理
不再提示
好的，知道了

全天候售后服务
7x24小时专业工程师品质服务

极速服务应答
秒级应答为业务保驾护航

客户价值为先
从服务价值到创造客户价值

全方位安全保障
打造一朵“透明可信”的云
logo
关于我们
为什么选火山
文档中心
联系我们
人才招聘
云信任中心
友情链接
产品
云服务器
GPU云服务器
机器学习平台
客户数据平台 VeCDP
飞连
视频直播
全部产品
解决方案
汽车行业
金融行业
文娱行业
医疗健康行业
传媒行业
智慧文旅
大消费
服务与支持
备案服务
服务咨询
建议与反馈
廉洁舞弊举报
举报平台
联系我们
业务咨询：service@volcengine.com
市场合作：marketing@volcengine.com
电话：400-850-0030
地址：北京市海淀区北三环西路甲18号院大钟寺广场1号楼

微信公众号

抖音号

视频号
© 北京火山引擎科技有限公司 2025 版权所有
代理域名注册服务机构：新网数码 商中在线
服务条款
隐私政策
更多协议

京公网安备11010802032137号
京ICP备20018813号-3
营业执照
增值电信业务经营许可证京B2-20202418，A2.B1.B2-20202637
网络文化经营许可证：京网文（2023）4872-140号
