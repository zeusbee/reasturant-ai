# 多渠道接入架构指南

## 目录
1. [整体架构](#整体架构)
2. [接入方式](#接入方式)
3. [快速接入步骤](#快速接入步骤)
4. [各平台接入指南](#各平台接入指南)
5. [消息格式统一](#消息格式统一)

---

## 整体架构

### 统一接入层设计

```
┌─────────────────────────────────────────────────────────┐
│                     客户层                              │
├──────────┬──────────┬──────────┬──────────┬────────────┤
│   微信   │   抖音   │   美团   │   淘宝   │   电话     │
└────┬─────┴────┬─────┴────┬─────┴────┬─────┴────┬──────┘
     │          │          │          │          │
┌────▼──────────▼──────────▼──────────▼──────────▼──────┐
│                 消息适配层 (Webhook/API)                │
├─────────────────────────────────────────────────────┤
│  - 微信: 公众号/小程序 Webhook                         │
│  - 抖音: 开放平台 Webhook                             │
│  - 美团: 商家开放平台 API                             │
│  - 淘宝: 千牛开放平台 API                             │
│  - 电话: 语音识别服务 + 转文本                         │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│              消息标准化处理器                            │
├─────────────────────────────────────────────────────┤
│  1. 统一消息格式                                       │
│  2. 提取元数据 (用户ID、渠道标识、时间戳)             │
│  3. 文本标准化 (表情符号处理、特殊字符过滤)           │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│              AI 代理层 (Skill)                          │
├─────────────────────────────────────────────────────┤
│  - 意图识别                                            │
│  - 信息提取                                            │
│  - 脚本调用 (menu/order/reservation)                  │
│  - 响应生成                                            │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│            响应分发层                                   │
├─────────────────────────────────────────────────────┤
│  - 根据渠道标识选择对应的回复方式                       │
│  - 格式转换 (适配各平台消息格式)                       │
└─────────────────────┬───────────────────────────────────┘
                      │
┌────┬──────────┬─────┴────┬──────────┬────────────────────┐
│ 微信│  抖音    │  美团    │  淘宝    │  电话              │
└────┴──────────┴──────────┴──────────┴────────────────────┘
```

---

## 接入方式

### 方式一: Webhook 集成（推荐）

**适用**: 微信、抖音、美团、淘宝

**优势**:
- 实时性高，消息即时到达
- 无需轮询，节省资源
- 平台主动推送，延迟低

**实现**:
```
平台服务器 ──HTTP POST──> 你的服务器 ──处理──> AI代理
                                      │
                                      └──> 调用scripts/
```

### 方式二: API 轮询（备选）

**适用**: 某些不支持Webhook的平台

**实现**:
```
定时任务 ──> 调用平台API获取消息 ──> 处理 ──> AI代理
```

---

## 快速接入步骤

### 通用接入流程

#### 步骤1: 注册平台开发者账号
- 微信: [微信公众平台](https://mp.weixin.qq.com/)
- 抖音: [抖音开放平台](https://developer.open-douyin.com/)
- 美团: [美团商家开放平台](https://open.meituan.com/)
- 淘宝: [淘宝开放平台](https://open.taobao.com/)

#### 步骤2: 创建应用并获取凭证
- 应用ID (AppID)
- 应用密钥 (AppSecret)
- 访问令牌 (AccessToken)
- 服务器配置URL (Webhook地址)

#### 步骤3: 配置Webhook/回调地址
- 在平台后台填入你的服务器URL
- 服务器需要处理平台的验证请求
- 服务器接收消息并转发到AI代理

#### 步骤4: 实现消息适配器
- 将平台消息格式转换为统一格式
- 调用AI代理处理
- 将AI代理响应转换为平台消息格式

#### 步骤5: 测试与上线
- 使用平台提供的测试工具
- 验证消息收发功能
- 上线并监控

---

## 各平台接入指南

### 1. 微信公众号接入

#### 必备条件
- 已认证的微信公众号
- 服务器有公网IP（或使用内网穿透工具如ngrok）

#### 接入步骤

**1. 获取服务器配置**
```bash
# 在微信公众平台 -> 开发 -> 基本配置
- AppID: wxXXXXXXXXXXXXXXX
- AppSecret: XXXXXXXXXXXXXXXXXXXXXXXXXXXXX
- Token: your_token
- EncodingAESKey: your_aes_key
```

**2. 配置Webhook服务器**
```python
# flask_server.py (示例)
from flask import Flask, request, jsonify
import xml.etree.ElementTree as ET
import hashlib
import requests

app = Flask(__name__)

WECHAT_APPID = "wxXXXXXXXXXXXXXXX"
WECHAT_APPSECRET = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
YOUR_TOKEN = "your_token"

# 微信消息处理
@app.route('/wechat', methods=['GET', 'POST'])
def wechat_handler():
    # 1. 验证服务器配置 (GET请求)
    if request.method == 'GET':
        signature = request.args.get('signature')
        timestamp = request.args.get('timestamp')
        nonce = request.args.get('nonce')
        echostr = request.args.get('echostr')
        
        # 验证签名
        if verify_signature(signature, timestamp, nonce, YOUR_TOKEN):
            return echostr
        return "验证失败", 403
    
    # 2. 处理消息 (POST请求)
    if request.method == 'POST':
        # 解析XML消息
        xml_data = request.data
        msg = parse_wechat_message(xml_data)
        
        # 转换为统一格式
        unified_msg = {
            "channel": "微信",
            "user_id": msg['FromUserName'],
            "message_type": msg['MsgType'],
            "content": msg.get('Content', ''),
            "timestamp": msg['CreateTime']
        }
        
        # 调用AI代理处理
        response = call_ai_agent(unified_msg)
        
        # 转换为微信消息格式
        reply_xml = format_wechat_reply(msg['FromUserName'], response)
        
        return reply_xml, 200, {'Content-Type': 'application/xml'}

def verify_signature(signature, timestamp, nonce, token):
    """验证微信签名"""
    params = sorted([token, timestamp, nonce])
    sign_str = ''.join(params)
    return hashlib.sha1(sign_str.encode()).hexdigest() == signature

def parse_wechat_message(xml_data):
    """解析微信XML消息"""
    root = ET.fromstring(xml_data)
    return {child.tag: child.text for child in root}

def format_wechat_reply(to_user, content):
    """格式化微信回复消息"""
    return f"""
    <xml>
        <ToUserName><![CDATA[{to_user}]]></ToUserName>
        <FromUserName><![CDATA[gh_XXXXXXXXXXXXXXXX]]></FromUserName>
        <CreateTime>{int(time.time())}</CreateTime>
        <MsgType><![CDATA[text]]></MsgType>
        <Content><![CDATA[{content}]]></Content>
    </xml>
    """

def call_ai_agent(message):
    """调用AI代理（这里可以调用scripts或直接集成智能体）"""
    # 实际实现中，这里调用restaurant-ai-agent的脚本或智能体
    return "这是AI代理的回复"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

**3. 部署服务器**
```bash
# 安装依赖
pip install flask requests

# 启动服务
python flask_server.py

# 使用ngrok暴露公网地址（测试用）
ngrok http 5000
# 获取的URL填入微信公众平台
```

---

### 2. 抖音接入

#### 接入步骤

**1. 获取开发者凭证**
```bash
# 抖音开放平台
- AppKey: your_app_key
- AppSecret: your_app_secret
- Webhook URL: https://your-domain.com/douyin
```

**2. 配置Webhook**
```python
@app.route('/douyin', methods=['POST'])
def douyin_handler():
    # 抖音消息是JSON格式
    data = request.json
    
    # 转换为统一格式
    unified_msg = {
        "channel": "抖音",
        "user_id": data.get('user_id'),
        "message_type": data.get('msg_type'),
        "content": data.get('content', ''),
        "timestamp": data.get('timestamp')
    }
    
    # 调用AI代理
    response = call_ai_agent(unified_msg)
    
    # 转换为抖音回复格式
    return jsonify({
        "status": "success",
        "reply": response
    })
```

---

### 3. 美团接入

#### 接入步骤

**1. 获取商家凭证**
```bash
# 美团商家开放平台
- AppKey: your_app_key
- AppSecret: your_app_secret
```

**2. 配置消息推送**
```python
@app.route('/meituan', methods=['POST'])
def meituan_handler():
    # 美团需要签名验证
    signature = request.headers.get('Signature')
    timestamp = request.headers.get('Timestamp')
    
    if not verify_meituan_signature(signature, timestamp):
        return "签名验证失败", 403
    
    data = request.json
    
    unified_msg = {
        "channel": "美团",
        "user_id": data.get('userId'),
        "message_type": data.get('msgType'),
        "content": data.get('content', ''),
        "timestamp": data.get('timestamp')
    }
    
    response = call_ai_agent(unified_msg)
    
    return jsonify({
        "code": 0,
        "msg": "success",
        "data": {"reply": response}
    })
```

---

### 4. 淘宝接入

#### 接入步骤

**1. 获取千牛凭证**
```bash
# 淘宝开放平台
- AppKey: your_app_key
- AppSecret: your_app_secret
- SessionKey: user_session_key
```

**2. 配置消息接收**
```python
@app.route('/taobao', methods=['POST'])
def taobao_handler():
    data = request.json
    
    unified_msg = {
        "channel": "淘宝",
        "user_id": data.get('buyerId'),
        "message_type": data.get('msgType'),
        "content": data.get('content', ''),
        "timestamp": data.get('timestamp')
    }
    
    response = call_ai_agent(unified_msg)
    
    return jsonify({
        "success": True,
        "reply": response
    })
```

---

### 5. 电话接入

#### 方案一: 使用第三方语音识别服务

**推荐服务商**:
- 阿里云智能语音交互
- 腾讯云语音识别
- 科大讯飞语音识别

**接入步骤**:
```python
# 使用阿里云语音识别示例
from aliyunsdkcore.client import AcsClient
from aliyunsdknls_cloud_meta.request import RecognizeRequest

client = AcsClient(
    'your-access-key-id',
    'your-access-key-secret',
    'cn-shanghai'
)

def transcribe_audio(audio_file):
    """将语音转换为文本"""
    request = RecognizeRequest()
    request.set_Format('wav')
    request.set_SampleRate('16000')
    request.set_AudioFile(audio_file)
    
    response = client.do_action_with_exception(request)
    
    unified_msg = {
        "channel": "电话",
        "user_id": "phone_caller",
        "message_type": "text",
        "content": response.get('Result', ''),
        "timestamp": int(time.time())
    }
    
    return unified_msg

# 处理电话通话
@app.route('/phone/webhook', methods=['POST'])
def phone_handler():
    audio_data = request.files.get('audio')
    
    # 1. 语音转文本
    text_msg = transcribe_audio(audio_data)
    
    # 2. 调用AI代理
    response = call_ai_agent(text_msg)
    
    # 3. 文本转语音 (TTS)
    audio_reply = text_to_speech(response)
    
    return jsonify({"audio_url": audio_reply})
```

**方案二: 集成呼叫中心系统**
- 使用企业级呼叫中心（如容联云、七陌）
- 提供完整的电话接入、转接、录音功能

---

## 消息格式统一

### 统一消息格式

所有渠道的消息都转换为以下格式:

```json
{
  "channel": "微信/抖音/美团/淘宝/电话",
  "user_id": "用户唯一标识",
  "message_type": "text/image/audio",
  "content": "消息内容",
  "timestamp": 1705382400,
  "extra": {
    "original_msg": "原始消息（用于日志）"
  }
}
```

### 统一响应格式

AI代理返回的响应格式:

```json
{
  "success": true,
  "message": "回复内容",
  "actions": [
    {
      "type": "create_order",
      "params": {...}
    }
  ],
  "attachments": []
}
```

---

## 部署方案

### 方案一: 云服务器部署

```bash
# 服务器配置
- 1核2G云服务器（阿里云/腾讯云/华为云）
- Ubuntu 20.04
- Python 3.8+
- Nginx反向代理

# 部署步骤
1. 购买云服务器
2. 安装Python和依赖
3. 部署Flask应用
4. 配置Nginx
5. 购买域名并配置SSL
6. 配置各平台Webhook地址
```

### 方案二: 使用Serverless（推荐）

**优势**:
- 无需管理服务器
- 按量付费，成本更低
- 自动扩容

**平台选择**:
- 阿里云函数计算 (FC)
- 腾讯云函数 (SCF)
- AWS Lambda

**示例（阿里云FC）**:
```python
# index.py
import json

def handler(event, context):
    # 解析事件
    body = json.loads(event.get('body', '{}'))
    
    # 统一处理
    unified_msg = standardize_message(body)
    
    # 调用AI代理
    response = call_ai_agent(unified_msg)
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(response)
    }
```

---

## 快速接入检查清单

### 微信接入
- [ ] 注册微信公众号
- [ ] 获取AppID和AppSecret
- [ ] 配置服务器URL
- [ ] 实现消息签名验证
- [ ] 实现消息接收和回复
- [ ] 测试消息收发

### 抖音接入
- [ ] 注册抖音开放平台账号
- [ ] 创建应用获取AppKey和AppSecret
- [ ] 配置Webhook地址
- [ ] 实现消息处理
- [ ] 测试消息收发

### 美团接入
- [ ] 注册美团商家开放平台
- [ ] 获取商家AppKey和AppSecret
- [ ] 配置消息推送
- [ ] 实现签名验证
- [ ] 测试消息收发

### 淘宝接入
- [ ] 注册淘宝开放平台
- [ ] 获取AppKey和AppSecret
- [ ] 配置消息接收地址
- [ ] 实现消息处理
- [ ] 测试消息收发

### 电话接入
- [ ] 选择语音识别服务商
- [ ] 获取API凭证
- [ ] 实现语音转文本
- [ ] 实现文本转语音
- [ ] 测试通话

---

## 注意事项

1. **安全性**
   - 所有Webhook必须验证签名
   - 敏感信息（AppSecret）不要硬编码
   - 使用HTTPS加密传输

2. **稳定性**
   - 添加消息重试机制
   - 实现错误处理和日志记录
   - 监控服务状态

3. **性能**
   - 使用异步处理提高响应速度
   - 考虑使用消息队列（Redis/RabbitMQ）
   - 缓存常用数据

4. **合规性**
   - 遵守各平台的使用规范
   - 用户隐私保护
   - 数据安全存储

---

## 下一步

1. 选择第一个接入渠道（建议从微信开始）
2. 按照对应平台的接入指南实施
3. 测试消息收发功能
4. 集成restaurant-ai-agent的脚本
5. 逐步扩展到其他渠道

需要针对某个具体平台的详细接入代码示例吗？
