#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
素材高消耗筛选工具
High Cost Materials Filter

功能：从form文件夹读取Excel数据，筛选整体消耗>10000的素材，输出素材名称到控制台
作者：MiniMax Agent
版本：v1.0
"""

import os
import pandas as pd
import glob
import re
from datetime import datetime

def get_latest_excel_file(directory="form"):
    """获取指定目录中最新的Excel文件"""
    print(f"📂 正在扫描{directory}文件夹...")
    
    # 查找所有Excel文件
    excel_files = glob.glob(f"{directory}/*.xlsx")
    
    if not excel_files:
        print(f"❌ {directory}文件夹中未找到Excel文件")
        return None
    
    # 过滤掉临时文件（以~$开头的文件）
    excel_files = [f for f in excel_files if not os.path.basename(f).startswith("~$")]
    
    if not excel_files:
        print(f"❌ {directory}文件夹中未找到有效的Excel文件")
        return None
    
    # 按修改时间排序，获取最新的文件
    excel_files.sort(key=os.path.getmtime, reverse=True)
    latest_file = excel_files[0]
    
    print(f"✅ 找到最新数据文件: {latest_file}")
    return latest_file

def format_number_with_commas(value):
    """将数字格式化为带千位分隔符的字符串"""
    return f"{value:,.2f}"

def filter_high_cost_materials(file_path, cost_threshold=10000):
    """筛选整体消耗大于指定阈值的素材，并输出素材名称到控制台"""
    if not file_path or not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return
    
    print(f"📖 正在读取文件: {file_path}")
    try:
        # 读取Excel文件
        df = pd.read_excel(file_path)
        print(f"✅ 成功读取数据 - 共 {len(df)} 条记录")
        
        # 检查是否存在"整体消耗"列
        cost_column = None
        for col_name in ['整体消耗', '消耗', '总消耗', '花费', 'cost']:
            if col_name in df.columns:
                cost_column = col_name
                break
        
        if not cost_column:
            print("❌ 未找到整体消耗相关字段")
            return
        
        print(f"🔍 使用字段: {cost_column}")
        
        # 检查是否存在"素材名称"列
        name_column = None
        for col_name in ['素材名称', '素材标题', '标题', '名称', 'title', 'name']:
            if col_name in df.columns:
                name_column = col_name
                break
        
        if not name_column:
            print("❌ 未找到素材名称相关字段")
            return
        
        print(f"🔍 使用字段: {name_column}")
        
        # 检查是否存在"素材ID"列
        id_column = None
        for col_name in ['素材ID', '素材id', 'material_id', '视频ID']:
            if col_name in df.columns:
                id_column = col_name
                break
        
        if not id_column:
            print("⚠️ 未找到素材ID相关字段，输出结果将不包含素材ID")
        else:
            print(f"🔍 使用字段: {id_column}")
        
        # 处理整体消耗列的格式
        # 如果是对象类型(字符串)，先清理格式
        if df[cost_column].dtype == 'object':
            # 删除逗号、空格和货币符号
            df[cost_column] = df[cost_column].astype(str).str.replace(',', '')
            df[cost_column] = df[cost_column].astype(str).str.replace(' ', '')
            df[cost_column] = df[cost_column].astype(str).str.replace('¥', '')
            df[cost_column] = df[cost_column].astype(str).str.replace('$', '')
            df[cost_column] = df[cost_column].astype(str).str.replace('￥', '')
        
        # 转换为数值类型
        df[cost_column] = pd.to_numeric(df[cost_column], errors='coerce')
        
        # 使用query筛选数据，避免直接使用布尔索引
        high_cost_df = df.query(f"{cost_column} > {cost_threshold}").copy()
        
        if len(high_cost_df) == 0:
            print(f"⚠️ 未找到整体消耗大于{cost_threshold}的素材")
            return
        
        # 手动构建排序的结果
        # 提取消耗值和对应行索引
        cost_values = high_cost_df[cost_column].to_list()
        indices = high_cost_df.index.to_list()
        
        # 创建索引和值的对应关系
        idx_cost_pairs = list(zip(indices, cost_values))
        
        # 按消耗值降序排序
        idx_cost_pairs.sort(key=lambda x: x[1], reverse=True)
        
        # 提取排序后的索引
        sorted_indices = [idx for idx, _ in idx_cost_pairs]
        
        # 按排序后的索引重新排序DataFrame
        high_cost_df = high_cost_df.loc[sorted_indices].copy()
        
        # 输出结果
        print(f"\n💰 找到 {len(high_cost_df)} 个整体消耗大于{cost_threshold}的素材:")
        print("=" * 60)
        print("今日指令:")
        print("=" * 60)
        
        # 使用新的输出格式：素材名称消耗达到"xx,xxx.xx"
        for _, row in high_cost_df.iterrows():
            name = row[name_column] if pd.notna(row[name_column]) else "未命名素材"
            cost = row[cost_column]
            # 格式化消耗金额为带千位分隔符的字符串
            formatted_cost = format_number_with_commas(cost)
            
            # 如果存在ID列，添加ID信息
            if id_column and pd.notna(row[id_column]):
                material_id = row[id_column]
                print(f"  {name}-{material_id}消耗达到\"{formatted_cost}\",请进行裂变")
            else:
                print(f"  {name}消耗达到\"{formatted_cost}\",请进行裂变")
        
        print("=" * 60)
        print(f"✅ 共找到 {len(high_cost_df)} 个高消耗素材")
        
    except Exception as e:
        print(f"❌ 处理数据时出错: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("=" * 60)
    print("🔍 素材高消耗筛选工具")
    print("=" * 60)
    
    # 获取最新的Excel文件
    latest_file = get_latest_excel_file()
    if not latest_file:
        return
    
    # 筛选高消耗素材
    filter_high_cost_materials(latest_file)

if __name__ == "__main__":
    main() 