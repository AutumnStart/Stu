#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整体消耗列分析工具
以"整体消耗"列为锚点，分析Excel文件中的列结构和数据分布

作者: AI Assistant
版本: v1.0
"""

import pandas as pd
import os
import glob
from datetime import datetime

def find_latest_excel_file(folder_path):
    """
    在指定文件夹中查找最新的Excel文件
    """
    try:
        excel_pattern = os.path.join(folder_path, "*.xlsx")
        excel_files = glob.glob(excel_pattern)
        
        # 过滤掉临时文件（以~$开头的文件）
        excel_files = [f for f in excel_files if not os.path.basename(f).startswith('~$')]
        
        if not excel_files:
            print(f"❌ 在 {folder_path} 文件夹中未找到Excel文件")
            return None
            
        latest_file = max(excel_files, key=os.path.getmtime)
        print(f"✅ 找到最新Excel文件: {os.path.basename(latest_file)}")
        return latest_file
        
    except Exception as e:
        print(f"❌ 查找Excel文件时出错: {e}")
        return None

def analyze_consumption_column(file_path):
    """
    以"整体消耗"列为锚点分析Excel文件结构
    """
    try:
        print(f"📖 正在分析Excel文件: {os.path.basename(file_path)}")
        
        # 读取Excel文件
        df = pd.read_excel(file_path)
        print(f"📊 数据维度: {df.shape[0]} 行 × {df.shape[1]} 列")
        print()
        
        # 查找"整体消耗"列的位置
        columns = list(df.columns)
        consumption_col = '整体消耗'
        
        if consumption_col not in columns:
            print(f"❌ 未找到'{consumption_col}'列")
            return
        
        consumption_index = columns.index(consumption_col)
        print(f"🎯 '{consumption_col}'列位置: 第 {consumption_index + 1} 列 (索引: {consumption_index})")
        print()
        
        # 显示以"整体消耗"为锚点的列结构
        print("📋 以'整体消耗'为锚点的列结构:")
        print("=" * 60)
        
        # 显示前面的列
        start_range = max(0, consumption_index - 5)
        end_range = min(len(columns), consumption_index + 6)
        
        for i in range(start_range, end_range):
            col_name = columns[i]
            position = i + 1
            
            if i == consumption_index:
                print(f"  {position:2d}. 🎯 {col_name} ← 锚点列")
            else:
                distance = i - consumption_index
                if distance < 0:
                    print(f"  {position:2d}. 📍 {col_name} (锚点前 {abs(distance)} 列)")
                else:
                    print(f"  {position:2d}. 📍 {col_name} (锚点后 {distance} 列)")
        
        print("=" * 60)
        print()
        
        # 分析"整体消耗"列的数据
        print(f"📈 '{consumption_col}'列数据分析:")
        consumption_data = pd.to_numeric(df[consumption_col], errors='coerce')
        valid_data = consumption_data.dropna()
        
        if len(valid_data) > 0:
            stats = valid_data.describe()
            print(f"  📊 统计信息:")
            print(f"      有效数据行数: {len(valid_data)}")
            print(f"      最小值: {stats['min']:.2f}")
            print(f"      最大值: {stats['max']:.2f}")
            print(f"      平均值: {stats['mean']:.2f}")
            print(f"      中位数: {stats['50%']:.2f}")
            print(f"      标准差: {stats['std']:.2f}")
            print()
            
            # 数据分布区间
            print(f"  📊 数据分布区间:")
            ranges = [
                (0, 100, "0-100"),
                (100, 500, "100-500"),
                (500, 1000, "500-1000"),
                (1000, 5000, "1000-5000"),
                (5000, 10000, "5000-10000"),
                (10000, float('inf'), "10000+")
            ]
            
            for min_val, max_val, label in ranges:
                if max_val == float('inf'):
                    count = len(valid_data[valid_data >= min_val])
                else:
                    count = len(valid_data[(valid_data >= min_val) & (valid_data < max_val)])
                percentage = (count / len(valid_data)) * 100
                print(f"      {label:>10}: {count:4d} 行 ({percentage:5.1f}%)")
            
            print()
            
            # 显示前10个数据样本
            print(f"  📋 前10个数据样本: {list(valid_data.head(10))}")
            
        else:
            print(f"  ❌ '{consumption_col}'列没有有效的数值数据")
        
        print()
        
        # 显示相邻列的信息
        print("🔍 相邻列详细信息:")
        adjacent_range = range(max(0, consumption_index - 2), min(len(columns), consumption_index + 3))
        
        for i in adjacent_range:
            col_name = columns[i]
            col_data = df[col_name]
            
            print(f"\n  列 {i+1}: {col_name}")
            if i == consumption_index:
                print(f"    🎯 这是锚点列")
            
            # 尝试分析列的数据类型和内容
            non_null_count = col_data.count()
            total_count = len(col_data)
            null_count = total_count - non_null_count
            
            print(f"    📊 数据概况: {non_null_count}/{total_count} 非空值 ({null_count} 个空值)")
            
            # 显示前5个非空值样本
            sample_data = col_data.dropna().head(5).tolist()
            print(f"    📋 样本数据: {sample_data}")
        
        return True
        
    except Exception as e:
        print(f"❌ 分析Excel文件时出错: {e}")
        return False

def main():
    """
    主函数
    """
    print("=" * 60)
    print("    整体消耗列分析工具")
    print("    以'整体消耗'列为锚点分析Excel文件结构")
    print("=" * 60)
    print()
    
    # 获取脚本所在目录的父目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    # 设置文件夹路径
    form_folder = os.path.join(project_root, "form")
    
    print(f"📁 源文件夹: {form_folder}")
    print()
    
    # 查找最新的Excel文件
    latest_file = find_latest_excel_file(form_folder)
    if not latest_file:
        print("❌ 未找到Excel文件，程序退出")
        return False
    
    # 分析"整体消耗"列
    success = analyze_consumption_column(latest_file)
    
    if success:
        print("\n🎉 分析完成！")
    else:
        print("\n❌ 分析失败")
    
    return success

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断程序")
    except Exception as e:
        print(f"\n❌ 程序执行出错: {e}")
        import traceback
        traceback.print_exc()