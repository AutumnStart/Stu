#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
素材数据筛选工具
从form文件夹扫描最新的Excel文件，筛选"整体消耗"在1000-10000区间的数据
将筛选结果保存到data文件夹的新Excel文件中

作者: AI Assistant
版本: v1.0
"""

import pandas as pd
import os
import glob
from datetime import datetime
import sys
import json

def find_latest_excel_file(folder_path):
    """
    在指定文件夹中查找最新的Excel文件
    
    Args:
        folder_path (str): 文件夹路径
        
    Returns:
        str: 最新Excel文件的路径，如果没找到则返回None
    """
    try:
        # 查找所有Excel文件
        excel_pattern = os.path.join(folder_path, "*.xlsx")
        excel_files = glob.glob(excel_pattern)
        
        # 过滤掉临时文件（以~$开头的文件）
        excel_files = [f for f in excel_files if not os.path.basename(f).startswith('~$')]
        
        if not excel_files:
            print(f"❌ 在 {folder_path} 文件夹中未找到Excel文件")
            return None
            
        # 按修改时间排序，获取最新的文件
        latest_file = max(excel_files, key=os.path.getmtime)
        print(f"✅ 找到最新Excel文件: {os.path.basename(latest_file)}")
        return latest_file
        
    except Exception as e:
        print(f"❌ 查找Excel文件时出错: {e}")
        return None

def read_excel_data(file_path):
    """
    读取Excel文件数据
    
    Args:
        file_path (str): Excel文件路径
        
    Returns:
        pd.DataFrame: 读取的数据，如果失败则返回None
    """
    try:
        print(f"📖 正在读取Excel文件: {os.path.basename(file_path)}")
        
        # 尝试多种方式读取Excel文件
        read_attempts = [
            {"desc": "标准读取", "params": {"dtype": {"素材ID": str}}},
            {"desc": "第2行作为表头", "params": {"header": 1, "dtype": {"素材ID": str}}},
            {"desc": "第3行作为表头", "params": {"header": 2, "dtype": {"素材ID": str}}},
            {"desc": "第4行作为表头", "params": {"header": 3, "dtype": {"素材ID": str}}},
            {"desc": "第5行作为表头", "params": {"header": 4, "dtype": {"素材ID": str}}}
        ]
        
        for attempt in read_attempts:
            try:
                print(f"  尝试 {attempt['desc']} 方式...")
                df = pd.read_excel(file_path, **attempt['params'])
                
                # 检查是否包含"整体消耗"列
                if '整体消耗' in df.columns:
                    print(f"  ✅ 成功找到'整体消耗'列，使用 {attempt['desc']} 方式")
                    print(f"  📊 数据维度: {df.shape[0]} 行 × {df.shape[1]} 列")
                    print(f"  📋 所有列名: {list(df.columns)}")
                    return df
                else:
                    print(f"  ⚠️ 未找到'整体消耗'列，列名: {list(df.columns)[:10]}")
                    
            except Exception as e:
                print(f"  ❌ {attempt['desc']} 方式失败: {str(e)}")
        
        print("❌ 所有读取方式都失败，无法找到包含'整体消耗'列的数据")
        return None
        
    except Exception as e:
        print(f"❌ 读取Excel文件时出错: {e}")
        return None

def preserve_material_id_format(df):
    """
    确保素材ID列保持字符串格式，避免精度丢失
    
    Args:
        df (pd.DataFrame): 原始数据
        
    Returns:
        pd.DataFrame: 处理后的数据
    """
    if '素材ID' in df.columns:
        # 将素材ID转换为字符串，保持原始格式
        df['素材ID'] = df['素材ID'].astype(str)
        # 移除可能的.0后缀（由于Excel读取导致的浮点数格式）
        df['素材ID'] = df['素材ID'].str.replace(r'\.0$', '', regex=True)
        print(f"  ✅ 素材ID列已转换为字符串格式，前5个样本: {list(df['素材ID'].head(5))}")
    return df

def filter_data_by_consumption(df, min_value=1000, max_value=10000):
    """
    根据"整体消耗"列筛选数据
    
    Args:
        df (pd.DataFrame): 原始数据
        min_value (int): 最小消耗值
        max_value (int): 最大消耗值
        
    Returns:
        pd.DataFrame: 筛选后的数据
    """
    try:
        print(f"🔍 开始筛选数据，消耗区间: {min_value} - {max_value}")
        
        # 首先确保素材ID格式正确
        df = preserve_material_id_format(df)
        
        # 检查"整体消耗"列是否存在
        if '整体消耗' not in df.columns:
            print("❌ 数据中不包含'整体消耗'列")
            return pd.DataFrame()
        
        # 转换"整体消耗"列为数值类型，先移除千位分隔符逗号
        df['整体消耗'] = df['整体消耗'].astype(str).str.replace(',', '').str.replace('，', '')
        df['整体消耗'] = pd.to_numeric(df['整体消耗'], errors='coerce')
        
        # 移除无效数据
        valid_data = df.dropna(subset=['整体消耗'])
        print(f"  📊 有效数据行数: {len(valid_data)}")
        
        # 显示"整体消耗"列的数据分布
        if len(valid_data) > 0:
            consumption_stats = valid_data['整体消耗'].describe()
            print(f"  📈 整体消耗数据分布:")
            print(f"      最小值: {consumption_stats['min']:.2f}")
            print(f"      最大值: {consumption_stats['max']:.2f}")
            print(f"      平均值: {consumption_stats['mean']:.2f}")
            print(f"      中位数: {consumption_stats['50%']:.2f}")
            
            # 显示前10个数据样本
            print(f"  📋 前10个整体消耗数据样本: {list(valid_data['整体消耗'].head(10))}")
        
        # 检查日期列是否存在
        date_column = None
        possible_date_columns = ['日期', '时间', 'Date', '统计日期']
        for col in possible_date_columns:
            if col in valid_data.columns:
                date_column = col
                break
        
        if date_column:
            print(f"  📅 找到日期列: {date_column}")
            # 显示日期列的唯一值
            unique_dates = valid_data[date_column].unique()
            print(f"  📋 日期列唯一值: {list(unique_dates)[:10]}")
            
            # 筛选数据：消耗区间 + 日期为"全部"
            filtered_data = valid_data[
                (valid_data['整体消耗'] >= min_value) & 
                (valid_data['整体消耗'] <= max_value) &
                (valid_data[date_column] == '全部')
            ]
            print(f"  📅 已添加日期筛选条件: {date_column} = '全部'")
        else:
            print(f"  ⚠️ 未找到日期列，仅使用消耗筛选")
            # 仅使用消耗筛选
            filtered_data = valid_data[
                (valid_data['整体消耗'] >= min_value) & 
                (valid_data['整体消耗'] <= max_value)
            ]
        
        print(f"  ✅ 筛选完成，符合条件的数据: {len(filtered_data)} 行")
        
        if len(filtered_data) > 0:
            consumption_stats = filtered_data['整体消耗'].describe()
            print(f"  📈 消耗统计: 最小值={consumption_stats['min']:.2f}, 最大值={consumption_stats['max']:.2f}, 平均值={consumption_stats['mean']:.2f}")
        
        return filtered_data
        
    except Exception as e:
        print(f"❌ 筛选数据时出错: {e}")
        return pd.DataFrame()

def save_to_excel(df, output_folder, filename="素材数据.xlsx"):
    """
    将数据保存到Excel文件
    
    Args:
        df (pd.DataFrame): 要保存的数据
        output_folder (str): 输出文件夹路径
        filename (str): 输出文件名
        
    Returns:
        str: 保存的文件路径，如果失败则返回None
    """
    try:
        # 确保输出文件夹存在
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            print(f"✅ 创建输出文件夹: {output_folder}")
        
        # 构建输出文件路径
        output_path = os.path.join(output_folder, filename)
        
        # 如果文件已存在，添加时间戳
        if os.path.exists(output_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{timestamp}{ext}"
            output_path = os.path.join(output_folder, filename)
            print(f"⚠️ 文件已存在，使用新文件名: {filename}")
        
        # 保存数据
        print(f"💾 正在保存数据到: {output_path}")
        
        # 创建ExcelWriter对象以便设置格式
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # 保存数据
            df.to_excel(writer, index=False, sheet_name='Sheet1')
            
            # 获取工作表对象
            worksheet = writer.sheets['Sheet1']
            
            # 设置素材ID列为文本格式
            if '素材ID' in df.columns:
                col_idx = df.columns.get_loc('素材ID') + 1  # Excel列索引从1开始
                col_letter = chr(64 + col_idx)  # 转换为字母
                
                # 设置整列为文本格式
                for row in range(2, len(df) + 2):  # 从第2行开始（跳过标题）
                    cell = worksheet[f'{col_letter}{row}']
                    cell.number_format = '@'  # 文本格式
                    # 确保值为字符串，保持原始精度
                    if cell.value is not None:
                        cell.value = str(cell.value)
        
        print(f"✅ 数据保存成功: {output_path}")
        print(f"📊 保存的数据: {len(df)} 行 × {len(df.columns)} 列")
        
        return output_path
        
    except Exception as e:
        print(f"❌ 保存Excel文件时出错: {e}")
        return None

def save_material_ids_to_json(df, output_folder, filename="素材ID.json"):
    """
    将筛选后数据的素材ID保存到JSON文件
    
    Args:
        df (pd.DataFrame): 筛选后的数据
        output_folder (str): 输出文件夹路径
        filename (str): 输出文件名
        
    Returns:
        str: 保存的文件路径，如果失败则返回None
    """
    try:
        # 确保输出文件夹存在
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            print(f"✅ 创建输出文件夹: {output_folder}")
        
        # 构建输出文件路径
        output_path = os.path.join(output_folder, filename)
        
        # 如果文件已存在，添加时间戳
        if os.path.exists(output_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{timestamp}{ext}"
            output_path = os.path.join(output_folder, filename)
            print(f"⚠️ JSON文件已存在，使用新文件名: {filename}")
        
        # 提取素材ID列表
        if '素材ID' in df.columns:
            material_ids = df['素材ID'].unique().tolist()  # 去重并转为列表
            print(f"📋 提取到 {len(material_ids)} 个唯一素材ID")
            
            # 保存到JSON文件
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(material_ids, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 素材ID已保存到JSON文件: {output_path}")
            print(f"📊 JSON文件包含: {len(material_ids)} 个素材ID")
            
            return output_path
        else:
            print("❌ 数据中不包含'素材ID'列，无法生成JSON文件")
            return None
            
    except Exception as e:
        print(f"❌ 保存JSON文件时出错: {e}")
        return None

def main():
    """
    主函数
    """
    print("="*50)
    print("    素材数据筛选工具")
    print("="*50)
    print()
    
    # 获取脚本所在目录的父目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    # 设置文件夹路径
    form_folder = os.path.join(project_root, "form")
    data_folder = os.path.join(project_root, "data")
    
    print(f"📁 源文件夹: {form_folder}")
    print(f"📁 输出文件夹: {data_folder}")
    print()
    
    # 1. 查找最新的Excel文件
    latest_file = find_latest_excel_file(form_folder)
    if not latest_file:
        print("❌ 未找到Excel文件，程序退出")
        return False
    
    # 2. 读取Excel数据
    df = read_excel_data(latest_file)
    if df is None or len(df) == 0:
        print("❌ 读取数据失败，程序退出")
        return False
    
    # 3. 筛选数据
    filtered_df = filter_data_by_consumption(df, min_value=1000, max_value=10000)
    if len(filtered_df) == 0:
        print("❌ 没有符合筛选条件的数据")
        return False
    
    # 4. 保存筛选结果到Excel
    output_path = save_to_excel(filtered_df, data_folder, "素材数据.xlsx")
    if not output_path:
        print("❌ 保存Excel数据失败")
        return False
    
    # 5. 保存素材ID到JSON文件
    json_path = save_material_ids_to_json(filtered_df, data_folder, "素材ID.json")
    if not json_path:
        print("⚠️ 保存JSON文件失败，但Excel文件已成功保存")
    
    print()
    print("🎉 数据筛选完成！")
    print(f"📄 Excel文件: {output_path}")
    if json_path:
        print(f"📄 JSON文件: {json_path}")
    print(f"📊 筛选结果: {len(filtered_df)} 行数据")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断程序")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 程序执行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)