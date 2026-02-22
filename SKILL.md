---
name: restaurant-ai-agent
description: 餐厅AI代理用于处理多渠道客户互动，包括菜品查询推荐、外卖订单管理、餐桌预订，支持微信、抖音、美团、淘宝、电话等渠道
dependency:
  python:
    - gspread>=6.0.0
    - oauth2client>=4.1.3
---

# 餐厅AI代理

## 任务目标
- 本Skill用于: 餐厅客服自动化，通过AI代理处理多渠道客户互动
- 能力包含: 菜单查询与推荐、外卖订单创建与跟踪、餐桌预订管理、客户咨询解答
- 触发条件: 客户通过微信、抖音、美团、淘宝、电话等渠道发起点餐、预订或咨询请求

## 前置准备
- 依赖说明: scripts脚本所需的依赖包
  ```
  gspread>=6.0.0
  oauth2client>=4.1.3
  ```

- 数据源准备:
  - 创建Google Sheet，包含三个工作表: `Menu`、`Orders`、`Reservations`
  - 按照 [references/data-sheets-structure.md](references/data-sheets-structure.md) 设置表头和初始数据
  - 在Google Cloud Console创建项目，启用Google Sheets API
  - 创建Service Account，下载JSON密钥文件（credentials.json）
  - 在Google Sheet中添加service account客户端邮箱为"编辑者"

- 环境变量配置:
  - 将Google Sheets凭证JSON文件路径作为参数传递给脚本
  - 将Google Sheet URL作为参数传递给脚本

## 操作步骤

### 标准流程

#### 1. 消息接入与意图识别
- 接收客户消息，识别渠道来源（微信/抖音/美团/淘宝/电话）
- 分析消息意图，分类为:
  - 点餐意图: 包含"点"、"买"、"外卖"、"菜单"等关键词
  - 预订意图: 包含"预订"、"订桌"、"位置"等关键词
  - 咨询意图: 包含"什么"、"有没有"、"多少钱"等疑问词
  - 查询意图: 包含"订单"、"预订状态"、"查询"等关键词

#### 2. 信息提取与验证
- 根据意图提取关键信息（菜品、数量、联系方式、日期、时间、人数等）
- 验证信息完整性:
  - 点餐需要: 客户姓名、电话、地址、菜品清单
  - 预订需要: 客户姓名、电话、日期、时段、人数
  - 查询需要: 订单ID/预订ID或电话号码

#### 3. 脚本调用执行

**菜单查询与推荐**:
- 调用 `scripts/menu_manager.py` 查询菜单:
  ```bash
  python scripts/menu_manager.py \
    --credentials /path/to/credentials.json \
    --sheet-url "https://docs.google.com/spreadsheets/d/..." \
    --action query \
    --query-type category \
    --query-value "热菜"
  ```
- 调用 `scripts/menu_manager.py` 推荐菜品:
  ```bash
  python scripts/menu_manager.py \
    --credentials /path/to/credentials.json \
    --sheet-url "https://docs.google.com/spreadsheets/d/..." \
    --action recommend \
    --category "热菜" \
    --budget 50 \
    --count 3
  ```

**订单创建与查询**:
- 调用 `scripts/order_manager.py` 创建订单:
  ```bash
  python scripts/order_manager.py \
    --credentials /path/to/credentials.json \
    --sheet-url "https://docs.google.com/spreadsheets/d/..." \
    --action create \
    --customer-name "张三" \
    --phone "13800138000" \
    --address "北京市朝阳区建国路88号" \
    --items '[{"菜品ID":"M001","数量":1},{"菜品ID":"M002","数量":1}]' \
    --total-amount 66.00 \
    --channel "微信"
  ```
- 调用 `scripts/order_manager.py` 查询订单:
  ```bash
  python scripts/order_manager.py \
    --credentials /path/to/credentials.json \
    --sheet-url "https://docs.google.com/spreadsheets/d/..." \
    --action query \
    --order-id "ORD20250115001"
  ```

**预订创建与查询**:
- 调用 `scripts/reservation_manager.py` 查询可用时段:
  ```bash
  python scripts/reservation_manager.py \
    --credentials /path/to/credentials.json \
    --sheet-url "https://docs.google.com/spreadsheets/d/..." \
    --action query-slots \
    --date "2025-01-20"
  ```
- 调用 `scripts/reservation_manager.py` 创建预订:
  ```bash
  python scripts/reservation_manager.py \
    --credentials /path/to/credentials.json \
    --sheet-url "https://docs.google.com/spreadsheets/d/..." \
    --action create \
    --customer-name "李四" \
    --phone "13900139000" \
    --date "2025-01-20" \
    --time-slot "19:00-21:00" \
    --party-size 4 \
    --channel "微信"
  ```

#### 4. 响应生成与确认
- 根据脚本返回结果生成自然语言回复
- 对于订单和预订操作，向用户展示摘要并请求确认
- 确认后执行最终操作并返回结果

### 可选分支
- 当 **信息不完整**: 主动询问缺失信息，直到收集完整
- 当 **菜品不可售**: 推荐替代菜品或询问其他选择
- 当 **时段已满**: 提供其他可用时段选项
- 当 **订单/预订查询失败**: 提示用户检查订单ID或电话号码
- 当 **数据写入失败**: 提示系统繁忙，建议稍后重试

## 资源索引
- 必要脚本:
  - [scripts/menu_manager.py](scripts/menu_manager.py) (用途: 菜单查询、菜品推荐、可用性检查)
  - [scripts/order_manager.py](scripts/order_manager.py) (用途: 订单创建、订单查询、状态更新)
  - [scripts/reservation_manager.py](scripts/reservation_manager.py) (用途: 时段查询、预订创建、预订查询、取消预订)
  - [scripts/message_adapter.py](scripts/message_adapter.py) (用途: 多渠道消息格式统一、响应格式化、统一处理器)

- 领域参考:
  - [references/data-sheets-structure.md](references/data-sheets-structure.md) (何时读取: 初始化数据表、理解字段定义、验证数据格式)
  - [references/workflow-guide.md](references/workflow-guide.md) (何时读取: 处理复杂场景、异常情况、多渠道适配)
  - [references/multi-channel-integration.md](references/multi-channel-integration.md) (何时读取: 接入新渠道、配置Webhook、部署服务器)

## 注意事项
- 脚本参数中的 `credentials` 和 `sheet-url` 是必需的，必须从外部获取
- 所有动态数据（客户信息、菜品清单、预订详情）通过参数传递，不硬编码
- 在执行订单或预订操作前，必须向用户展示摘要并请求确认
- 优先使用脚本进行数据操作，避免直接操作Google Sheets
- 处理不同渠道消息时，适配相应的表达习惯和格式要求
- 当脚本返回错误时，提供友好的错误说明和解决方案

## 多渠道快速接入

### 接入架构
采用统一消息层设计:
1. **消息接收层**: 各平台Webhook/API接收消息
2. **消息适配层**: 使用 `scripts/message_adapter.py` 统一消息格式
3. **AI代理层**: 处理业务逻辑并生成响应
4. **响应分发层**: 将响应格式化为各平台格式

### 接入步骤
1. **注册平台开发者账号**（微信/抖音/美团/淘宝）
2. **配置Webhook服务器**（云服务器或Serverless）
3. **实现消息处理器**（参考 `references/multi-channel-integration.md`）
4. **集成message_adapter.py**实现消息格式统一
5. **测试并上线**

### 快速开始
```bash
# 1. 使用message_adapter.py处理消息
from scripts.message_adapter import MessageAdapter, UnifiedAgentHandler, Channel

adapter = MessageAdapter(credentials_json="path/to/credentials.json", sheet_url="your-sheet-url")
handler = UnifiedAgentHandler(adapter)

# 2. 接收各平台消息后调用
response = handler.process_message(raw_message, Channel.WECHAT)
```

### 代码模板
各平台接入代码模板详见 [references/multi-channel-integration.md](references/multi-channel-integration.md)，包含:
- 微信公众号接入（Flask示例）
- 抖音开放平台接入
- 美团商家开放平台接入
- 淘宝千牛接入
- 电话语音识别接入（阿里云/腾讯云）

### 部署方案
- **云服务器部署**: 使用Flask/FastAPI + Nginx
- **Serverless部署**: 阿里云FC、腾讯云SCF（推荐，成本低）

详细接入指南请参考 [references/multi-channel-integration.md](references/multi-channel-integration.md)

## 使用示例

### 示例1: 客户通过微信点餐
**用户**: "我要点宫保鸡丁和麻婆豆腐，送到朝阳区建国路88号，电话13800138000"

**执行流程**:
1. AI识别意图: 点餐
2. 提取信息: 菜品=宫保鸡丁、麻婆豆腐，地址=朝阳区建国路88号，电话=13800138000
3. 调用脚本验证菜品:
   ```bash
   python scripts/menu_manager.py \
     --credentials /path/to/credentials.json \
     --sheet-url "https://docs.google.com/spreadsheets/d/..." \
     --action check \
     --dishes "宫保鸡丁,麻婆豆腐"
   ```
4. 计算总价: 38.00 + 28.00 = 66.00
5. 询问客户姓名，用户回答: "张三"
6. 调用脚本创建订单:
   ```bash
   python scripts/order_manager.py \
     --credentials /path/to/credentials.json \
     --sheet-url "https://docs.google.com/spreadsheets/d/..." \
     --action create \
     --customer-name "张三" \
     --phone "13800138000" \
     --address "北京市朝阳区建国路88号" \
     --items '[{"菜品ID":"M001","数量":1},{"菜品ID":"M002","数量":1}]' \
     --total-amount 66.00 \
     --channel "微信"
   ```
7. 返回结果: "订单已创建成功！订单号: ORD20250115001，预计30分钟内送达"

### 示例2: 客户通过抖音预订餐桌
**用户**: "明晚7点要预订4人桌"

**执行流程**:
1. AI识别意图: 预订
2. 提取信息: 日期=明天，时间=19:00，人数=4
3. 调用脚本查询可用时段:
   ```bash
   python scripts/reservation_manager.py \
     --credentials /path/to/credentials.json \
     --sheet-url "https://docs.google.com/spreadsheets/d/..." \
     --action query-slots \
     --date "2025-01-20"
   ```
4. 假设19:00-21:00可用，询问: "2025年1月20日19:00-21:00时段可预订4人桌，请提供您的姓名和联系电话"
5. 用户回答: "王五，13700137000"
6. 调用脚本创建预订:
   ```bash
   python scripts/reservation_manager.py \
     --credentials /path/to/credentials.json \
     --sheet-url "https://docs.google.com/spreadsheets/d/..." \
     --action create \
     --customer-name "王五" \
     --phone "13700137000" \
     --date "2025-01-20" \
     --time-slot "19:00-21:00" \
     --party-size 4 \
     --channel "抖音"
   ```
7. 返回结果: "预订已创建成功！预订号: RES20250116001，我们期待您的光临"

### 示例3: 客户咨询菜品推荐
**用户**: "有什么热菜推荐吗？预算50块钱，推荐2个"

**执行流程**:
1. AI识别意图: 菜品推荐
2. 提取信息: 类别=热菜，预算=50，数量=2
3. 调用脚本推荐菜品:
   ```bash
   python scripts/menu_manager.py \
     --credentials /path/to/credentials.json \
     --sheet-url "https://docs.google.com/spreadsheets/d/..." \
     --action recommend \
     --category "热菜" \
     --budget 50 \
     --count 2
   ```
4. 解析返回结果，生成自然语言回复:
   "我推荐以下热菜（预算50元以内）:
   1. 宫保鸡丁 ¥38.00 - 经典川菜，麻辣鲜香
   2. 麻婆豆腐 ¥28.00 - 嫩滑豆腐，麻辣下饭
   合计 ¥66.00（超出预算），如需调整请告知"
5. 若用户确认点餐，转入示例1的流程

### 示例4: 客户查询订单状态
**用户**: "我的订单ORD20250115001到哪了？"

**执行流程**:
1. AI识别意图: 订单查询
2. 提取信息: 订单ID=ORD20250115001
3. 调用脚本查询订单:
   ```bash
   python scripts/order_manager.py \
     --credentials /path/to/credentials.json \
     --sheet-url "https://docs.google.com/spreadsheets/d/..." \
     --action query \
     --order-id "ORD20250115001"
   ```
4. 解析返回结果，生成回复:
   "订单信息:
   订单号: ORD20250115001
   客户: 张三
   菜品: 宫保鸡丁(1份)、麻婆豆腐(1份)
   总金额: ¥66.00
   状态: 配送中
   预计送达: 10分钟内"
