#!/usr/bin/env python3
"""
预订管理脚本
功能: 查询可用时段、创建预订、查询预订
"""

import json
import sys
import argparse
from datetime import datetime, timedelta
from typing import Dict, List


def query_available_slots(credentials_json, sheet_url, date, max_capacity=50):
    """
    查询可用时段
    
    参数:
        credentials_json: Google Sheets API凭证文件路径
        sheet_url: Google Sheet URL
        date: 预订日期 (YYYY-MM-DD)
        max_capacity: 餐厅最大容量
    
    返回:
        可用时段列表JSON字符串
    """
    try:
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials
        
        # 认证
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_json, scope)
        gc = gspread.authorize(credentials)
        
        # 打开表格
        sh = gc.open_by_url(sheet_url)
        worksheet = sh.worksheet("Reservations")
        
        # 获取所有预订记录
        all_reservations = worksheet.get_all_records()
        
        # 筛选该日期的已确认预订
        date_reservations = [
            res for res in all_reservations 
            if res.get('预订日期', '') == date 
            and res.get('预订状态', '') in ['待确认', '已确认']
        ]
        
        # 定义营业时段 (11:00-22:00，每2小时一个时段)
        time_slots = [
            "11:00-13:00",
            "13:00-15:00",
            "17:00-19:00",
            "19:00-21:00",
            "21:00-23:00"
        ]
        
        # 计算每个时段的已占用人数
        slot_occupancy = {slot: 0 for slot in time_slots}
        
        for res in date_reservations:
            slot = res.get('时段', '')
            party_size = int(res.get('人数', 0))
            if slot in slot_occupancy:
                slot_occupancy[slot] += party_size
        
        # 计算可用时段
        available_slots = []
        for slot in time_slots:
            occupied = slot_occupancy[slot]
            available = max_capacity - occupied
            available_slots.append({
                "时段": slot,
                "已占用": occupied,
                "剩余容量": available
            })
        
        return json.dumps({
            "success": True,
            "data": available_slots,
            "date": date
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"查询可用时段失败: {str(e)}"
        }, ensure_ascii=False)


def create_reservation(credentials_json, sheet_url, customer_name, phone, date, time_slot, party_size, channel, notes=None):
    """
    创建预订
    
    参数:
        credentials_json: Google Sheets API凭证文件路径
        sheet_url: Google Sheet URL
        customer_name: 客户姓名
        phone: 电话号码
        date: 预订日期 (YYYY-MM-DD)
        time_slot: 时间段 (HH:MM-HH:MM)
        party_size: 人数
        channel: 渠道来源
        notes: 备注（可选）
    
    返回:
        创建结果JSON字符串
    """
    try:
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials
        
        # 认证
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_json, scope)
        gc = gspread.authorize(credentials)
        
        # 打开表格
        sh = gc.open_by_url(sheet_url)
        worksheet = sh.worksheet("Reservations")
        
        # 验证时段是否可用
        available_result = query_available_slots(credentials_json, sheet_url, date)
        available_data = json.loads(available_result)
        
        if not available_data.get("success"):
            return available_result
        
        slot_info = None
        for slot in available_data.get("data", []):
            if slot["时段"] == time_slot:
                slot_info = slot
                break
        
        if not slot_info:
            return json.dumps({
                "success": False,
                "error": f"无效的时间段: {time_slot}"
            }, ensure_ascii=False)
        
        if slot_info["剩余容量"] < party_size:
            return json.dumps({
                "success": False,
                "error": f"该时段剩余容量不足，剩余 {slot_info['剩余容量']} 人，需要 {party_size} 人"
            }, ensure_ascii=False)
        
        # 生成预订ID: RES + 日期 + 序号
        res_date_str = date.replace('-', '')
        existing_reservations = worksheet.get_all_records()
        today_count = sum(1 for res in existing_reservations if res.get('预订ID', '').startswith(f'RES{res_date_str}'))
        reservation_id = f"RES{res_date_str}{str(today_count + 1).zfill(3)}"
        
        # 获取当前时间
        created_at = datetime.now().isoformat()
        
        # 准备预订数据
        reservation_data = {
            "预订ID": reservation_id,
            "客户姓名": customer_name,
            "电话号码": phone,
            "预订日期": date,
            "时段": time_slot,
            "人数": party_size,
            "预订状态": "已确认",
            "渠道来源": channel,
            "备注": notes if notes else "",
            "创建时间": created_at
        }
        
        # 转换为列表（按表头顺序）
        headers = worksheet.row_values(1)
        reservation_row = [reservation_data.get(header, "") for header in headers]
        
        # 写入预订
        worksheet.append_row(reservation_row)
        
        return json.dumps({
            "success": True,
            "data": {
                "预订ID": reservation_id,
                "预订状态": "已确认"
            },
            "message": "预订创建成功"
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"创建预订失败: {str(e)}"
        }, ensure_ascii=False)


def query_reservation(credentials_json, sheet_url, reservation_id=None, phone=None, date=None):
    """
    查询预订
    
    参数:
        credentials_json: Google Sheets API凭证文件路径
        sheet_url: Google Sheet URL
        reservation_id: 预订ID（可选）
        phone: 电话号码（可选）
        date: 预订日期（可选）
    
    返回:
        查询结果JSON字符串
    """
    try:
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials
        
        # 认证
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_json, scope)
        gc = gspread.authorize(credentials)
        
        # 打开表格
        sh = gc.open_by_url(sheet_url)
        worksheet = sh.worksheet("Reservations")
        
        # 获取所有数据
        all_reservations = worksheet.get_all_records()
        
        # 根据条件筛选
        if reservation_id:
            result = [res for res in all_reservations if res.get('预订ID', '') == reservation_id]
        elif phone and date:
            result = [res for res in all_reservations if res.get('电话号码', '') == phone and res.get('预订日期', '') == date]
        elif phone:
            result = [res for res in all_reservations if res.get('电话号码', '') == phone]
        elif date:
            result = [res for res in all_reservations if res.get('预订日期', '') == date]
        else:
            return json.dumps({
                "success": False,
                "error": "请提供预订ID、电话号码或日期"
            }, ensure_ascii=False)
        
        return json.dumps({
            "success": True,
            "data": result,
            "total": len(result)
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"查询预订失败: {str(e)}"
        }, ensure_ascii=False)


def cancel_reservation(credentials_json, sheet_url, reservation_id):
    """
    取消预订
    
    参数:
        credentials_json: Google Sheets API凭证文件路径
        sheet_url: Google Sheet URL
        reservation_id: 预订ID
    
    返回:
        取消结果JSON字符串
    """
    try:
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials
        
        # 认证
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_json, scope)
        gc = gspread.authorize(credentials)
        
        # 打开表格
        sh = gc.open_by_url(sheet_url)
        worksheet = sh.worksheet("Reservations")
        
        # 查找预订行
        all_reservations = worksheet.get_all_records()
        res_row_idx = None
        
        for idx, res in enumerate(all_reservations, start=2):  # 从第2行开始
            if res.get('预订ID', '') == reservation_id:
                res_row_idx = idx
                break
        
        if not res_row_idx:
            return json.dumps({
                "success": False,
                "error": f"未找到预订: {reservation_id}"
            }, ensure_ascii=False)
        
        # 获取表头，找到"预订状态"列索引
        headers = worksheet.row_values(1)
        status_col_idx = headers.index("预订状态") + 1  # 1-based
        
        # 更新状态为"已取消"
        worksheet.update_cell(res_row_idx, status_col_idx, "已取消")
        
        return json.dumps({
            "success": True,
            "data": {
                "预订ID": reservation_id,
                "新状态": "已取消"
            },
            "message": "预订已取消"
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"取消预订失败: {str(e)}"
        }, ensure_ascii=False)


def validate_reservation_date(date_str: str) -> bool:
    """
    验证预订日期是否有效
    
    参数:
        date_str: 日期字符串 (YYYY-MM-DD)
    
    返回:
        是否有效
    """
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        return date >= today
    except ValueError:
        return False


def main():
    parser = argparse.ArgumentParser(description='预订管理工具')
    parser.add_argument('--credentials', required=True, help='Google Sheets API凭证文件路径')
    parser.add_argument('--sheet-url', required=True, help='Google Sheet URL')
    parser.add_argument('--action', required=True, choices=['query-slots', 'create', 'query', 'cancel'], help='操作类型')
    
    # 查询可用时段参数
    parser.add_argument('--date', help='预订日期 (YYYY-MM-DD)')
    parser.add_argument('--max-capacity', type=int, default=50, help='餐厅最大容量')
    
    # 创建预订参数
    parser.add_argument('--customer-name', help='客户姓名')
    parser.add_argument('--phone', help='电话号码')
    parser.add_argument('--time-slot', help='时间段 (HH:MM-HH:MM)')
    parser.add_argument('--party-size', type=int, help='人数')
    parser.add_argument('--channel', help='渠道来源')
    parser.add_argument('--notes', help='备注')
    
    # 查询预订参数
    parser.add_argument('--reservation-id', help='预订ID')
    
    args = parser.parse_args()
    
    if args.action == 'query-slots':
        if not args.date:
            print(json.dumps({
                "success": False,
                "error": "请提供预订日期"
            }, ensure_ascii=False))
            sys.exit(1)
        
        # 验证日期
        if not validate_reservation_date(args.date):
            print(json.dumps({
                "success": False,
                "error": "预订日期必须是今天或未来日期"
            }, ensure_ascii=False))
            sys.exit(1)
        
        result = query_available_slots(args.credentials, args.sheet_url, args.date, args.max_capacity)
    
    elif args.action == 'create':
        # 验证必要参数
        required_fields = ['customer_name', 'phone', 'date', 'time_slot', 'party_size', 'channel']
        missing = [field for field in required_fields if not getattr(args, field)]
        
        if missing:
            print(json.dumps({
                "success": False,
                "error": f"缺少必要参数: {', '.join(missing)}"
            }, ensure_ascii=False))
            sys.exit(1)
        
        # 验证日期
        if not validate_reservation_date(args.date):
            print(json.dumps({
                "success": False,
                "error": "预订日期必须是今天或未来日期"
            }, ensure_ascii=False))
            sys.exit(1)
        
        result = create_reservation(
            args.credentials,
            args.sheet_url,
            args.customer_name,
            args.phone,
            args.date,
            args.time_slot,
            args.party_size,
            args.channel,
            args.notes
        )
    
    elif args.action == 'query':
        if not args.reservation_id and not args.phone and not args.date:
            print(json.dumps({
                "success": False,
                "error": "请提供预订ID、电话号码或日期"
            }, ensure_ascii=False))
            sys.exit(1)
        
        result = query_reservation(args.credentials, args.sheet_url, args.reservation_id, args.phone, args.date)
    
    elif args.action == 'cancel':
        if not args.reservation_id:
            print(json.dumps({
                "success": False,
                "error": "请提供预订ID"
            }, ensure_ascii=False))
            sys.exit(1)
        
        result = cancel_reservation(args.credentials, args.sheet_url, args.reservation_id)
    
    print(result)


if __name__ == '__main__':
    main()
