#!/usr/bin/env python3
"""
消息适配器 - 统一多渠道消息格式
将各平台消息转换为统一格式，并调用AI代理处理
"""

import json
import time
from typing import Dict, Any
from enum import Enum


class Channel(Enum):
    """渠道枚举"""
    WECHAT = "微信"
    DOUYIN = "抖音"
    MEITUAN = "美团"
    TAOBAO = "淘宝"
    PHONE = "电话"


class MessageType(Enum):
    """消息类型枚举"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


class MessageAdapter:
    """消息适配器基类"""
    
    def __init__(self, credentials_json: str, sheet_url: str):
        """
        初始化适配器
        
        参数:
            credentials_json: Google Sheets凭证文件路径
            sheet_url: Google Sheet URL
        """
        self.credentials_json = credentials_json
        self.sheet_url = sheet_url
    
    def standardize_message(self, raw_message: Dict[str, Any], channel: Channel) -> Dict[str, Any]:
        """
        将原始消息转换为统一格式
        
        参数:
            raw_message: 原始消息（各平台格式）
            channel: 渠道类型
            
        返回:
            统一格式的消息
        """
        # 各渠道解析逻辑
        if channel == Channel.WECHAT:
            return self._parse_wechat_message(raw_message)
        elif channel == Channel.DOUYIN:
            return self._parse_douyin_message(raw_message)
        elif channel == Channel.MEITUAN:
            return self._parse_meituan_message(raw_message)
        elif channel == Channel.TAOBAO:
            return self._parse_taobao_message(raw_message)
        elif channel == Channel.PHONE:
            return self._parse_phone_message(raw_message)
        else:
            raise ValueError(f"不支持的渠道: {channel}")
    
    def _parse_wechat_message(self, raw_msg: Dict[str, Any]) -> Dict[str, Any]:
        """解析微信公众号消息"""
        return {
            "channel": Channel.WECHAT.value,
            "user_id": raw_msg.get('FromUserName', ''),
            "message_type": self._map_msg_type(raw_msg.get('MsgType', 'text')),
            "content": raw_msg.get('Content', ''),
            "timestamp": int(raw_msg.get('CreateTime', time.time())),
            "extra": {
                "msg_id": raw_msg.get('MsgId', ''),
                "original_msg": raw_msg
            }
        }
    
    def _parse_douyin_message(self, raw_msg: Dict[str, Any]) -> Dict[str, Any]:
        """解析抖音消息"""
        return {
            "channel": Channel.DOUYIN.value,
            "user_id": raw_msg.get('user_id', ''),
            "message_type": MessageType.TEXT.value,  # 抖音主要支持文本
            "content": raw_msg.get('content', ''),
            "timestamp": raw_msg.get('timestamp', int(time.time())),
            "extra": {
                "open_id": raw_msg.get('open_id', ''),
                "original_msg": raw_msg
            }
        }
    
    def _parse_meituan_message(self, raw_msg: Dict[str, Any]) -> Dict[str, Any]:
        """解析美团消息"""
        return {
            "channel": Channel.MEITUAN.value,
            "user_id": raw_msg.get('userId', ''),
            "message_type": MessageType.TEXT.value,
            "content": raw_msg.get('content', ''),
            "timestamp": raw_msg.get('timestamp', int(time.time())),
            "extra": {
                "order_id": raw_msg.get('orderId', ''),
                "original_msg": raw_msg
            }
        }
    
    def _parse_taobao_message(self, raw_msg: Dict[str, Any]) -> Dict[str, Any]:
        """解析淘宝消息"""
        return {
            "channel": Channel.TAOBAO.value,
            "user_id": raw_msg.get('buyerId', ''),
            "message_type": MessageType.TEXT.value,
            "content": raw_msg.get('content', ''),
            "timestamp": raw_msg.get('timestamp', int(time.time())),
            "extra": {
                "trade_id": raw_msg.get('tradeId', ''),
                "original_msg": raw_msg
            }
        }
    
    def _parse_phone_message(self, raw_msg: Dict[str, Any]) -> Dict[str, Any]:
        """解析电话消息（语音转文本后）"""
        return {
            "channel": Channel.PHONE.value,
            "user_id": raw_msg.get('caller_number', ''),
            "message_type": MessageType.TEXT.value,
            "content": raw_msg.get('transcribed_text', ''),
            "timestamp": raw_msg.get('call_time', int(time.time())),
            "extra": {
                "call_id": raw_msg.get('call_id', ''),
                "duration": raw_msg.get('duration', 0),
                "original_msg": raw_msg
            }
        }
    
    def _map_msg_type(self, wechat_type: str) -> str:
        """映射微信消息类型"""
        type_map = {
            'text': MessageType.TEXT.value,
            'image': MessageType.IMAGE.value,
            'voice': MessageType.AUDIO.value,
            'video': MessageType.VIDEO.value
        }
        return type_map.get(wechat_type, MessageType.TEXT.value)


class ResponseFormatter:
    """响应格式化器"""
    
    @staticmethod
    def format_for_channel(response: str, channel: Channel, user_id: str) -> Dict[str, Any]:
        """
        将AI代理响应格式化为特定渠道格式
        
        参数:
            response: AI代理的回复内容
            channel: 目标渠道
            user_id: 用户ID
            
        返回:
            渠道特定的响应格式
        """
        base_response = {
            "success": True,
            "message": response,
            "timestamp": int(time.time())
        }
        
        if channel == Channel.WECHAT:
            return ResponseFormatter._format_wechat(response, user_id)
        elif channel == Channel.DOUYIN:
            return ResponseFormatter._format_douyin(response)
        elif channel == Channel.MEITUAN:
            return ResponseFormatter._format_meituan(response)
        elif channel == Channel.TAOBAO:
            return ResponseFormatter._format_taobao(response)
        elif channel == Channel.PHONE:
            return ResponseFormatter._format_phone(response)
        else:
            return base_response
    
    @staticmethod
    def _format_wechat(message: str, to_user: str) -> Dict[str, Any]:
        """格式化微信响应"""
        return {
            "ToUserName": to_user,
            "FromUserName": "gh_XXXXXXXXXXXXXXXX",  # 公众号原始ID
            "CreateTime": int(time.time()),
            "MsgType": "text",
            "Content": message
        }
    
    @staticmethod
    def _format_douyin(message: str) -> Dict[str, Any]:
        """格式化抖音响应"""
        return {
            "status": "success",
            "reply": message,
            "msg_type": "text"
        }
    
    @staticmethod
    def _format_meituan(message: str) -> Dict[str, Any]:
        """格式化美团响应"""
        return {
            "code": 0,
            "msg": "success",
            "data": {
                "reply": message
            }
        }
    
    @staticmethod
    def _format_taobao(message: str) -> Dict[str, Any]:
        """格式化淘宝响应"""
        return {
            "success": True,
            "reply": message,
            "msg_type": "text"
        }
    
    @staticmethod
    def _format_phone(message: str) -> Dict[str, Any]:
        """格式化电话响应（需要TTS转换）"""
        return {
            "type": "text_to_speech",
            "text": message,
            "voice_type": "xiaoyun"  # 阿里云TTS音色
        }


class UnifiedAgentHandler:
    """统一AI代理处理器"""
    
    def __init__(self, adapter: MessageAdapter):
        """
        初始化处理器
        
        参数:
            adapter: 消息适配器
        """
        self.adapter = adapter
    
    def process_message(self, raw_message: Dict[str, Any], channel: Channel) -> Dict[str, Any]:
        """
        处理消息的完整流程
        
        参数:
            raw_message: 原始消息
            channel: 渠道类型
            
        返回:
            渠道特定的响应
        """
        # 1. 标准化消息
        unified_msg = self.adapter.standardize_message(raw_message, channel)
        
        # 2. 调用AI代理处理（这里需要集成智能体逻辑）
        ai_response = self._call_ai_agent(unified_msg)
        
        # 3. 格式化响应
        formatted_response = ResponseFormatter.format_for_channel(
            ai_response,
            channel,
            unified_msg['user_id']
        )
        
        return formatted_response
    
    def _call_ai_agent(self, unified_msg: Dict[str, Any]) -> str:
        """
        调用AI代理
        
        参数:
            unified_msg: 统一格式的消息
            
        返回:
            AI代理的回复
        """
        # TODO: 这里需要集成实际的AI智能体
        # 可以是调用restaurant-ai-agent的脚本，或者是直接与智能体对话
        
        content = unified_msg['content']
        channel = unified_msg['channel']
        
        # 模拟AI代理逻辑
        # 实际实现中，这里应该调用智能体的推理能力
        response = f"【{channel}】收到消息: {content}"
        
        return response


# 使用示例
if __name__ == '__main__':
    # 初始化
    adapter = MessageAdapter(
        credentials_json="/path/to/credentials.json",
        sheet_url="https://docs.google.com/spreadsheets/d/..."
    )
    handler = UnifiedAgentHandler(adapter)
    
    # 测试微信消息
    wechat_msg = {
        "FromUserName": "oXXXXXXXXXXXXXXXXXXXX",
        "ToUserName": "gh_XXXXXXXXXXXXXXXX",
        "CreateTime": "1705382400",
        "MsgType": "text",
        "Content": "我要点宫保鸡丁",
        "MsgId": "1234567890"
    }
    
    response = handler.process_message(wechat_msg, Channel.WECHAT)
    print("微信响应:", json.dumps(response, ensure_ascii=False, indent=2))
    
    # 测试抖音消息
    douyin_msg = {
        "user_id": "123456",
        "content": "明晚7点预订4人桌",
        "timestamp": 1705382400
    }
    
    response = handler.process_message(douyin_msg, Channel.DOUYIN)
    print("抖音响应:", json.dumps(response, ensure_ascii=False, indent=2))
