#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
提取素材ID工具

从Excel文件中提取素材ID并保存为JSON格式
"""

import os
import pandas as pd
import json
import glob
from datetime import datetime


def extract_material_ids(input_file, output_file):
    """
    从Excel文件中提取素材ID并保存为JSON格式
    
    Args:
        input_file (str): 输入Excel文件路径
        output_file (str): 输出JSON文件路径
    
    Returns:
        bool: 操作是否成功
    """
    try:
        print(f"正在读取文件: {input_file}")
        print(f"文件是否存在: {os.path.exists(input_file)}")
        
        df = pd.read_excel(input_file)
        
        # 检查是否存在素材ID列
        print(f"Excel文件列名: {df.columns.tolist()}")
        if '素材ID' not in df.columns:
            print("错误: 未找到'素材ID'列")
            return False
        
        # 提取素材ID
        material_ids = df['素材ID'].tolist()
        print(f"提取到的素材ID数量: {len(material_ids)}")
        
        # 创建JSON数据结构
        result = {
            "提取时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "素材数量": len(material_ids),
            "素材ID列表": material_ids
        }
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        print(f"准备保存到: {output_file}")
        print(f"输出目录是否存在: {os.path.exists(output_dir)}")
        
        # 保存为JSON文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        
        print(f"成功提取 {len(material_ids)} 个素材ID")
        print(f"结果已保存至: {output_file}")
        print(f"文件是否成功创建: {os.path.exists(output_file)}")
        return True
        
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def extract_top_material_ids(input_file, output_file, top_n=5):
    """
    从Excel文件中只提取前N条素材ID并保存为JSON格式
    
    Args:
        input_file (str): 输入Excel文件路径
        output_file (str): 输出JSON文件路径
        top_n (int): 提取的素材ID数量，默认为5
    
    Returns:
        bool: 操作是否成功
    """
    try:
        print(f"正在读取文件: {input_file}")
        print(f"文件是否存在: {os.path.exists(input_file)}")
        
        df = pd.read_excel(input_file)
        
        # 检查是否存在素材ID列
        print(f"Excel文件列名: {df.columns.tolist()}")
        if '素材ID' not in df.columns:
            print("错误: 未找到'素材ID'列")
            return False
        
        # 提取前N条素材ID
        material_ids = df['素材ID'].head(top_n).tolist()
        print(f"提取到的前{top_n}条素材ID: {material_ids}")
        
        # 创建JSON数据结构
        result = {
            "提取时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "素材数量": len(material_ids),
            "素材ID列表": material_ids
        }
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        print(f"准备保存到: {output_file}")
        print(f"输出目录是否存在: {os.path.exists(output_dir)}")
        
        # 保存为JSON文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        
        print(f"成功提取前 {len(material_ids)} 个素材ID")
        print(f"结果已保存至: {output_file}")
        print(f"文件是否成功创建: {os.path.exists(output_file)}")
        return True
        
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def find_material_data_file(data_dir):
    """
    在指定目录中查找以"素材数据"开头的Excel文件
    
    Args:
        data_dir (str): 数据目录路径
    
    Returns:
        str: 找到的文件路径，如果没找到则返回None
    """
    # 查找所有以"素材数据"开头的Excel文件
    pattern = os.path.join(data_dir, "素材数据*.xlsx")
    files = glob.glob(pattern)
    
    if files:
        # 如果找到多个匹配文件，使用最新的一个
        return max(files, key=os.path.getmtime)
    return None


def main():
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 获取项目根目录
    root_dir = os.path.dirname(current_dir)
    # 数据目录
    data_dir = os.path.join(root_dir, 'data')
    
    # 查找素材数据文件
    material_file = find_material_data_file(data_dir)
    if not material_file:
        print("错误: 未找到素材数据文件")
        return
    
    # 定义输出文件路径
    output_file = os.path.join(data_dir, '素材ID.json')
    
    print(f"当前脚本目录: {current_dir}")
    print(f"项目根目录: {root_dir}")
    print(f"找到素材数据文件: {material_file}")
    print(f"输出文件路径: {output_file}")
    
    # 提取所有素材ID
    success = extract_material_ids(material_file, output_file)
    
    if success:
        print("处理完成!")
    else:
        print("处理失败!")
    
    # # 提取前5条素材ID
    # top_success = extract_top_material_ids(material_file, output_file, top_n=5)
    
    # if top_success:
    #     print("提取前5条素材ID成功!")
    # else:
    #     print("提取前5条素材ID失败!")
    



if __name__ == "__main__":
    main() 