#!/usr/bin/env python3
"""
菜单管理脚本
功能: 查询菜单、推荐菜品
"""

import json
import sys
import argparse


def query_menu(credentials_json, sheet_url, query_type=None, query_value=None):
    """
    查询菜单数据
    
    参数:
        credentials_json: Google Sheets API凭证文件路径
        sheet_url: Google Sheet URL
        query_type: 查询类型 (category/price/name/all)
        query_value: 查询值
    
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
        worksheet = sh.worksheet("Menu")
        
        # 获取所有数据
        all_data = worksheet.get_all_records()
        
        # 过滤已下架菜品
        available_items = [item for item in all_data if item.get('是否可售', '').lower() == 'true']
        
        # 根据查询类型过滤
        if query_type == "category":
            result = [item for item in available_items if item.get('类别', '') == query_value]
        elif query_type == "price":
            max_price = float(query_value)
            result = [item for item in available_items if float(item.get('价格', 0)) <= max_price]
        elif query_type == "name":
            result = [item for item in available_items if query_value.lower() in item.get('名称', '').lower()]
        elif query_type == "all" or query_type is None:
            result = available_items
        else:
            return json.dumps({"error": f"不支持的查询类型: {query_type}"}, ensure_ascii=False)
        
        return json.dumps({
            "success": True,
            "data": result,
            "total": len(result)
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"查询菜单失败: {str(e)}"
        }, ensure_ascii=False)


def recommend_dish(credentials_json, sheet_url, category=None, budget=None, count=3):
    """
    推荐菜品
    
    参数:
        credentials_json: Google Sheets API凭证文件路径
        sheet_url: Google Sheet URL
        category: 菜品类别（可选）
        budget: 预算上限（可选）
        count: 推荐数量
    
    返回:
        推荐结果JSON字符串
    """
    try:
        # 查询可用菜品
        if category:
            result_json = query_menu(credentials_json, sheet_url, "category", category)
        else:
            result_json = query_menu(credentials_json, sheet_url, "all")
        
        result = json.loads(result_json)
        
        if not result.get("success"):
            return result_json
        
        dishes = result.get("data", [])
        
        # 按预算过滤
        if budget:
            dishes = [dish for dish in dishes if float(dish.get('价格', 0)) <= float(budget)]
        
        # 限制推荐数量
        recommended = dishes[:count]
        
        return json.dumps({
            "success": True,
            "data": recommended,
            "total": len(recommended)
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"推荐菜品失败: {str(e)}"
        }, ensure_ascii=False)


def check_dish_availability(credentials_json, sheet_url, dish_names):
    """
    检查菜品是否可售
    
    参数:
        credentials_json: Google Sheets API凭证文件路径
        sheet_url: Google Sheet URL
        dish_names: 菜品名称列表
    
    返回:
        可用性检查结果JSON字符串
    """
    try:
        result_json = query_menu(credentials_json, sheet_url, "all")
        result = json.loads(result_json)
        
        if not result.get("success"):
            return result_json
        
        all_dishes = {dish['名称']: dish for dish in result.get('data', [])}
        
        availability = {}
        for name in dish_names:
            if name in all_dishes:
                dish = all_dishes[name]
                availability[name] = {
                    "available": True,
                    "price": float(dish.get('价格', 0)),
                    "category": dish.get('类别', '')
                }
            else:
                availability[name] = {
                    "available": False,
                    "reason": "菜品不存在"
                }
        
        return json.dumps({
            "success": True,
            "data": availability
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"检查菜品可用性失败: {str(e)}"
        }, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description='菜单管理工具')
    parser.add_argument('--credentials', required=True, help='Google Sheets API凭证文件路径')
    parser.add_argument('--sheet-url', required=True, help='Google Sheet URL')
    parser.add_argument('--action', required=True, choices=['query', 'recommend', 'check'], help='操作类型')
    parser.add_argument('--query-type', help='查询类型 (category/price/name/all)')
    parser.add_argument('--query-value', help='查询值')
    parser.add_argument('--category', help='推荐菜品类别')
    parser.add_argument('--budget', type=float, help='推荐菜品预算上限')
    parser.add_argument('--count', type=int, default=3, help='推荐菜品数量')
    parser.add_argument('--dishes', help='检查菜品可用性，逗号分隔的菜品名称')
    
    args = parser.parse_args()
    
    if args.action == 'query':
        result = query_menu(args.credentials, args.sheet_url, args.query_type, args.query_value)
    elif args.action == 'recommend':
        result = recommend_dish(args.credentials, args.sheet_url, args.category, args.budget, args.count)
    elif args.action == 'check':
        if not args.dishes:
            print(json.dumps({"success": False, "error": "请指定要检查的菜品名称"}, ensure_ascii=False))
            sys.exit(1)
        dish_names = [name.strip() for name in args.dishes.split(',')]
        result = check_dish_availability(args.credentials, args.sheet_url, dish_names)
    
    print(result)


if __name__ == '__main__':
    main()
