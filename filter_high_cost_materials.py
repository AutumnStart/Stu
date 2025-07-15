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

def filter_high_cost_materials(file_path):
    """筛选整体消耗大于10000的素材，并输出指令到控制台"""
    if not file_path or not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return
    
    print(f"📖 正在读取文件: {file_path}")
    try:
        # 读取Excel文件
        df = pd.read_excel(file_path)
        print(f"✅ 成功读取数据 - 共 {len(df)} 条记录")
        
        # 查找消耗列
        cost_column = next((col for col in ['整体消耗', '消耗', '总消耗', '花费', 'cost'] if col in df.columns), None)
        if not cost_column:
            print("❌ 未找到整体消耗相关字段")
            return
        assert isinstance(cost_column, str)
        print(f"🔍 使用字段: {cost_column}")
        
        # 查找名称列
        name_column = next((col for col in ['素材名称', '素材标题', '标题', '名称', 'title', 'name'] if col in df.columns), None)
        if not name_column:
            print("❌ 未找到素材名称相关字段")
            return
        assert isinstance(name_column, str)
        print(f"🔍 使用字段: {name_column}")
        
        # 查找ID列
        id_column = next((col for col in ['素材ID', '素材id', 'material_id', '视频ID'] if col in df.columns), None)
        if not id_column:
            print("⚠️ 未找到素材ID相关字段，输出结果将不包含素材ID")
        else:
            print(f"🔍 使用字段: {id_column}")
        
        # 清理消耗列，并转换为数值
        if df[cost_column].dtype == 'object':
            df[cost_column] = df[cost_column].astype(str).str.replace(r'[,\s¥$￥]', '', regex=True)
        df[cost_column] = pd.to_numeric(df[cost_column], errors='coerce')
        df.dropna(subset=[cost_column], inplace=True)
        
        # --- 高消耗素材 (> 10000) ---
        filtered_df = df[df[cost_column] > 10000].copy()
        high_cost_df = filtered_df.sort_values(by=cost_column, ascending=False)  # type: ignore
        
        print("\n" + "=" * 60)
        print("今日指令:")
        print("=" * 60)
        
        if not high_cost_df.empty:
            for _, row in high_cost_df.iterrows():
                name = row[name_column] if pd.notna(row[name_column]) else "未命名素材"  # type: ignore
                cost = row[cost_column]
                formatted_cost = format_number_with_commas(cost)
                material_id = f"-{row[id_column]}" if id_column and pd.notna(row[id_column]) else ""  # type: ignore
                print(f"  {name}{material_id}消耗达到\"{formatted_cost}\",请进行裂变")
        else:
            print("  今日无高消耗素材需要裂变。")
        
        # --- 总结 ---
        print("\n" + "=" * 60)
        if high_cost_df.empty:
            print("✅ 本次分析未找到任何消耗大于10000的素材。")
        else:
            print(f"✅ 分析完成: 共找到 {len(high_cost_df)} 个高消耗素材。")

    except Exception as e:
        print(f"❌ 处理数据时出错: {e}")
        import traceback
        traceback.print_exc()

def find_json_file_for_material(material_name, json_folder='json'):
    """根据素材名称在指定文件夹中查找对应的JSON分析文件。"""
    for root, _, files in os.walk(json_folder):
        for file in files:
            # 构造一个更灵活的匹配，只要文件名（不含扩展名）与素材名完全一致
            if os.path.splitext(file)[0] == material_name and file.endswith('.json'):
                return os.path.join(root, file)
    return None

def filter_materials_by_sop(excel_file):
    """
    根据SOP策略筛选素材。
    - 消耗 > 10000: 裂变
    - 1000 < 消耗 <= 10000: 迭代
    """
    try:
        df = pd.read_excel(excel_file, engine='openpyxl')
    except FileNotFoundError:
        print(f"错误: Excel文件未找到 -> {excel_file}")
        return

    # 根据SOP定义筛选条件
    df['建议操作'] = ''
    fission_condition = df['消耗'] > 10000
    iteration_condition = (df['消耗'] > 1000) & (df['消耗'] <= 10000)

    # 使用 .loc 进行赋值以避免 SettingWithCopyWarning
    df.loc[fission_condition, '建议操作'] = '裂变'
    df.loc[iteration_condition, '建议操作'] = '迭代'

    # 筛选出需要操作的素材
    materials_to_process = df[df['建议操作'] != ''].copy()

    if materials_to_process.empty:
        print("没有找到符合SOP条件的素材。")
        return

    # 为筛选出的素材匹配对应的JSON分析文件路径
    # 使用 .loc 保证赋值的准确性
    materials_to_process['json_file_path'] = materials_to_process['素材名称'].apply(find_json_file_for_material) # type: ignore

    # 过滤掉那些没有找到JSON文件的素材
    final_materials = materials_to_process.dropna(subset=['json_file_path']) # type: ignore

    if final_materials.empty:
        print("找到了符合条件的素材，但未能匹配到任何JSON分析文件。")
        return

    # 保存到CSV文件中，供下一个脚本使用
    DATA_DIR = "form" # 假设数据文件夹名为form
    output_path = os.path.join(DATA_DIR, 'filtered_materials_for_processing.csv')
    final_materials.to_csv(output_path, index=False, encoding='utf-8-sig')

    print(f"已根据SOP筛选出 {len(final_materials)} 个素材，建议操作已保存至: {output_path}")


def main():
    """主函数"""
    print("=" * 60)
    print("🔍 素材高消耗筛选工具")
    print("=" * 60)
    
    # 获取最新的Excel文件
    latest_file = get_latest_excel_file()
    if latest_file:
        print(f"找到最新的素材数据文件: {latest_file}")
        # 根据SOP筛选高消耗素材
        filter_materials_by_sop(latest_file)
    else:
        print("在 'form' 文件夹中没有找到任何Excel文件。")

if __name__ == "__main__":
    main() 