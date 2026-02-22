#!/usr/bin/env python3
"""
订单管理脚本
功能: 创建订单、查询订单、更新订单状态
"""

import json
import sys
import argparse
from datetime import datetime
from typing import List, Dict


def create_order(credentials_json, sheet_url, customer_name, phone, address, items, total_amount, channel, notes=None):
    """
    创建新订单
    
    参数:
        credentials_json: Google Sheets API凭证文件路径
        sheet_url: Google Sheet URL
        customer_name: 客户姓名
        phone: 电话号码
        address: 配送地址
        items: 菜品清单 (JSON字符串，格式: [{"菜品ID":"M001","数量":2},...])
        total_amount: 总金额
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
        worksheet = sh.worksheet("Orders")
        
        # 生成订单ID: ORD + 日期 + 序号
        today = datetime.now().strftime("%Y%m%d")
        existing_orders = worksheet.get_all_records()
        
        # 计算今日订单数量
        today_order_count = sum(1 for order in existing_orders if order.get('订单ID', '').startswith(f'ORD{today}'))
        order_id = f"ORD{today}{str(today_order_count + 1).zfill(3)}"
        
        # 获取当前时间
        order_date = datetime.now().isoformat()
        
        # 准备订单数据
        # 确保items是JSON字符串
        if isinstance(items, list):
            items_json = json.dumps(items, ensure_ascii=False)
        else:
            items_json = items
        
        order_data = {
            "订单ID": order_id,
            "客户姓名": customer_name,
            "电话号码": phone,
            "配送地址": address,
            "菜品清单": items_json,
            "总金额": total_amount,
            "下单日期": order_date,
            "订单状态": "待确认",
            "渠道来源": channel,
            "备注": notes if notes else ""
        }
        
        # 转换为列表（按表头顺序）
        headers = worksheet.row_values(1)
        order_row = [order_data.get(header, "") for header in headers]
        
        # 写入订单
        worksheet.append_row(order_row)
        
        return json.dumps({
            "success": True,
            "data": {
                "订单ID": order_id,
                "订单状态": "待确认"
            },
            "message": "订单创建成功"
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"创建订单失败: {str(e)}"
        }, ensure_ascii=False)


def query_order(credentials_json, sheet_url, order_id=None, phone=None):
    """
    查询订单
    
    参数:
        credentials_json: Google Sheets API凭证文件路径
        sheet_url: Google Sheet URL
        order_id: 订单ID（可选）
        phone: 电话号码（可选）
    
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
        worksheet = sh.worksheet("Orders")
        
        # 获取所有数据
        all_orders = worksheet.get_all_records()
        
        # 根据条件筛选
        if order_id:
            result = [order for order in all_orders if order.get('订单ID', '') == order_id]
        elif phone:
            result = [order for order in all_orders if order.get('电话号码', '') == phone]
        else:
            return json.dumps({
                "success": False,
                "error": "请提供订单ID或电话号码"
            }, ensure_ascii=False)
        
        return json.dumps({
            "success": True,
            "data": result,
            "total": len(result)
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"查询订单失败: {str(e)}"
        }, ensure_ascii=False)


def update_order_status(credentials_json, sheet_url, order_id, new_status):
    """
    更新订单状态
    
    参数:
        credentials_json: Google Sheets API凭证文件路径
        sheet_url: Google Sheet URL
        order_id: 订单ID
        new_status: 新状态（待确认/制作中/配送中/已完成/已取消）
    
    返回:
        更新结果JSON字符串
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
        worksheet = sh.worksheet("Orders")
        
        # 查找订单行
        all_orders = worksheet.get_all_records()
        order_row_idx = None
        
        for idx, order in enumerate(all_orders, start=2):  # 从第2行开始（第1行是表头）
            if order.get('订单ID', '') == order_id:
                order_row_idx = idx
                break
        
        if not order_row_idx:
            return json.dumps({
                "success": False,
                "error": f"未找到订单: {order_id}"
            }, ensure_ascii=False)
        
        # 获取表头，找到"订单状态"列索引
        headers = worksheet.row_values(1)
        status_col_idx = headers.index("订单状态") + 1  # 1-based
        
        # 更新状态
        worksheet.update_cell(order_row_idx, status_col_idx, new_status)
        
        return json.dumps({
            "success": True,
            "data": {
                "订单ID": order_id,
                "新状态": new_status
            },
            "message": "订单状态更新成功"
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"更新订单状态失败: {str(e)}"
        }, ensure_ascii=False)


def validate_order(items: List[Dict]) -> Dict:
    """
    验证订单数据
    
    参数:
        items: 菜品清单列表
    
    返回:
        验证结果
    """
    if not items:
        return {"valid": False, "error": "菜品清单不能为空"}
    
    for item in items:
        if "菜品ID" not in item or "数量" not in item:
            return {"valid": False, "error": "每个菜品项必须包含'菜品ID'和'数量'"}
        
        if not isinstance(item["数量"], int) or item["数量"] <= 0:
            return {"valid": False, "error": "数量必须是正整数"}
    
    return {"valid": True}


def main():
    parser = argparse.ArgumentParser(description='订单管理工具')
    parser.add_argument('--credentials', required=True, help='Google Sheets API凭证文件路径')
    parser.add_argument('--sheet-url', required=True, help='Google Sheet URL')
    parser.add_argument('--action', required=True, choices=['create', 'query', 'update'], help='操作类型')
    
    # 创建订单参数
    parser.add_argument('--customer-name', help='客户姓名')
    parser.add_argument('--phone', help='电话号码')
    parser.add_argument('--address', help='配送地址')
    parser.add_argument('--items', help='菜品清单（JSON字符串）')
    parser.add_argument('--total-amount', type=float, help='总金额')
    parser.add_argument('--channel', help='渠道来源')
    parser.add_argument('--notes', help='备注')
    
    # 查询订单参数
    parser.add_argument('--order-id', help='订单ID')
    
    # 更新订单状态参数
    parser.add_argument('--new-status', choices=['待确认', '制作中', '配送中', '已完成', '已取消'], help='新状态')
    
    args = parser.parse_args()
    
    if args.action == 'create':
        # 验证必要参数
        required_fields = ['customer_name', 'phone', 'address', 'items', 'total_amount', 'channel']
        missing = [field for field in required_fields if not getattr(args, field)]
        
        if missing:
            print(json.dumps({
                "success": False,
                "error": f"缺少必要参数: {', '.join(missing)}"
            }, ensure_ascii=False))
            sys.exit(1)
        
        # 验证菜品清单
        try:
            items_data = json.loads(args.items)
        except json.JSONDecodeError:
            print(json.dumps({
                "success": False,
                "error": "菜品清单格式错误，必须是有效的JSON"
            }, ensure_ascii=False))
            sys.exit(1)
        
        validation = validate_order(items_data)
        if not validation["valid"]:
            print(json.dumps({"success": False, "error": validation["error"]}, ensure_ascii=False))
            sys.exit(1)
        
        result = create_order(
            args.credentials,
            args.sheet_url,
            args.customer_name,
            args.phone,
            args.address,
            items_data,
            args.total_amount,
            args.channel,
            args.notes
        )
    
    elif args.action == 'query':
        if not args.order_id and not args.phone:
            print(json.dumps({
                "success": False,
                "error": "请提供订单ID或电话号码"
            }, ensure_ascii=False))
            sys.exit(1)
        
        result = query_order(args.credentials, args.sheet_url, args.order_id, args.phone)
    
    elif args.action == 'update':
        if not args.order_id or not args.new_status:
            print(json.dumps({
                "success": False,
                "error": "请提供订单ID和新状态"
            }, ensure_ascii=False))
            sys.exit(1)
        
        result = update_order_status(args.credentials, args.sheet_url, args.order_id, args.new_status)
    
    print(result)


if __name__ == '__main__':
    main()
