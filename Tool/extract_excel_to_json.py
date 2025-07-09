#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Excel数据转换为JSON工具
读取素材数据Excel，处理后存储为JSON格式，只保留指定字段
"""

import pandas as pd
import json
import os
import sys
import re
import codecs
import glob

# 配置变量
# 获取脚本所在目录的绝对路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录（假设脚本在Tool文件夹下）
ROOT_DIR = os.path.dirname(SCRIPT_DIR)

# 数据分析目录
DATA_ANALYSIS_DIR = os.path.join(ROOT_DIR, "json", "素材数据分析")

# 配置变量，使用绝对路径
DEFAULT_EXCEL_PATH = os.path.join(ROOT_DIR, "data", "素材数据.xlsx")  # 默认Excel数据位置
OUTPUT_JSON_PATH = os.path.join(DATA_ANALYSIS_DIR, "素材数据.json")     # 默认输出JSON位置

# DEFAULT_EXCEL_PATH = "data/素材数据.xlsx"  # 默认Excel数据位置
# OUTPUT_JSON_PATH = "json/素材数据分析/素材数据.json"     # 默认输出JSON位置


# 确保数据分析目录存在
os.makedirs(DATA_ANALYSIS_DIR, exist_ok=True)

# 需要保留的字段列表
KEEP_FIELDS = [
    "素材ID",
    "素材名称",
    "素材时长",
    "整体消耗",
    "整体支付ROI",
    "整体成交金额",
    "整体转化率",
    "整体点击率",
    "3秒播放率",
    "平均观看时长",
    "视频完播率",
    "追投调控消耗",
    "追投调控成交金额",
    "追投调控支付ROI",
    "追投调控点击率",
    "追投调控转化率",
    "基础消耗"
]

# 需要转换为字符串的字段
STR_FIELDS = ['素材ID', '整体支付ROI', '平均观看时长', '追投调控支付ROI']

# 列名映射，将Excel列名映射为标准JSON字段名
COLUMN_MAPPING = {
    '素材命名': '素材名称',
    '素材时长': '素材时长',
    '求和项:GMV': '整体成交金额',
    '整体成交金额GMV': '整体成交金额',
    '整体支付ROI': '整体支付ROI',
    '求和项:总CTR': '整体点击率',
    '整体点击率CTR': '整体点击率',
    '求和项:总CVR': '整体转化率',
    '整体转化率CVR': '整体转化率',
    '全域素材ID': '素材ID',
    '求和项:消耗': '整体消耗',
    '整体消耗': '整体消耗',
    '3s播放率': '3秒播放率',
    '平均观看时长(s)': '平均观看时长',
    '完播率': '视频完播率',
    '调控消耗': '追投调控消耗',
    '调控成交金额': '追投调控成交金额',
    '调控支付ROI': '追投调控支付ROI',
    '调控点击率': '追投调控点击率',
    '调控转化率': '追投调控转化率',
    '基础消耗': '基础消耗'
}

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

def ensure_dir(file_path):
    """确保目录存在"""
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

def process_excel_to_json(excel_path=None, output_path=OUTPUT_JSON_PATH):
    """
    将Excel文件处理成JSON格式，只保留指定字段
    
    Args:
        excel_path: Excel文件路径，如果为None则自动查找
        output_path: 输出JSON文件路径
    """
    try:
        # 如果未指定Excel路径，尝试查找素材数据文件
        if excel_path is None or not os.path.exists(excel_path):
            data_dir = os.path.join(ROOT_DIR, "data")
            found_file = find_material_data_file(data_dir)
            if found_file:
                excel_path = found_file
                print(f"找到素材数据文件: {excel_path}")
            else:
                print(f"错误: 未找到素材数据文件")
                return False
        
        print(f"开始处理Excel文件: {excel_path}")
        
        # 设置Pandas显示选项，避免中文乱码
        pd.set_option('display.unicode.east_asian_width', True)
        pd.set_option('display.unicode.ambiguous_as_wide', True)
        
        # 读取Excel文件，尝试多种方式处理可能的不同格式
        df = None
        excel_format = None
        
        # 尝试多种方式读取Excel文件
        read_attempts = [
            {"desc": "标准读取", "params": {}},
            {"desc": "第5行作为表头", "params": {"header": 4}},
            {"desc": "无表头", "params": {"header": None}},
            {"desc": "跳过前3行", "params": {"header": 2}},
            {"desc": "跳过前10行", "params": {"header": 9}}
        ]
        
        for attempt in read_attempts:
            try:
                print(f"尝试 {attempt['desc']} 方式读取Excel...")
                temp_df = pd.read_excel(excel_path, **attempt['params'])
                print(f"  - 读取成功，列数: {len(temp_df.columns)}, 行数: {len(temp_df)}")
                print(f"  - 列名: {list(temp_df.columns)[:10]}{'...' if len(temp_df.columns) > 10 else ''}")
                
                # 显示前几行数据的样例
                print("  - 数据样例 (前2行):")
                for i in range(min(2, len(temp_df))):
                    row_sample = {}
                    for col in list(temp_df.columns)[:5]:
                        row_sample[col] = temp_df.iloc[i][col]
                    print(f"    行{i+1}: {row_sample}")
                
                # 检查是否包含关键列
                if '素材命名' in temp_df.columns or '全域素材ID' in temp_df.columns or '素材ID' in temp_df.columns or '素材名称' in temp_df.columns:
                    print(f"  ✓ 发现关键列，使用 {attempt['desc']} 方式")
                    df = temp_df
                    excel_format = attempt['desc']
                    break
                    
            except Exception as e:
                print(f"  ✗ 尝试 {attempt['desc']} 方式失败: {str(e)}")
        
        if df is None:
            print("未能找到合适的方式读取Excel文件，将使用默认无表头方式")
            df = pd.read_excel(excel_path, header=None)
            excel_format = "默认无表头"
            
        print(f"\n成功读取Excel文件，使用{excel_format}方式，包含 {len(df)} 行数据")
        print(f"Excel文件完整列名: {list(df.columns)}")
        
        # 检查是否需要手动设置列名
        if all(col.startswith('Unnamed: ') for col in df.columns if isinstance(col, str)):
            print("\n检测到全部为无名列，尝试使用第一行作为列名...")
            
            # 使用第一行作为列名
            try:
                new_columns = {i: str(df.iloc[0][i]) for i in range(len(df.columns))}
                df = df.iloc[1:].copy()  # 跳过第一行
                df.rename(columns=new_columns, inplace=True)
                print(f"使用第一行作为列名后: {list(df.columns)}")
            except Exception as e:
                print(f"设置列名失败: {str(e)}")
        
        # 将数据转换为字典列表
        materials_data = []
        
        for index, row in df.iterrows():
            material = {}
            
            # 处理每一列
            for col, val in row.items():
                if pd.notna(val):  # 跳过NaN值
                    # 将Excel列名映射到标准字段名
                    field_name = COLUMN_MAPPING.get(col, col)
                    material[field_name] = val
            
            # 确保素材ID存在（如果没有或为NaN，则跳过此行）
            if '素材ID' not in material:
                if '全域素材ID' in material:
                    material['素材ID'] = material['全域素材ID']
                    del material['全域素材ID']
                elif '素材命名' in material or '素材名称' in material:
                    # 使用素材名称作为临时ID
                    name_key = '素材命名' if '素材命名' in material else '素材名称'
                    if material[name_key]:
                        print(f"为素材 '{material[name_key]}' 生成临时ID")
                        material['素材ID'] = f"temp_{hash(str(material[name_key]))}"
                    else:
                        continue
                else:
                    # 如果既没有ID也没有名称，但至少有一些数据，也添加一个临时ID
                    if len(material) >= 3:  # 至少有3个字段
                        material['素材ID'] = f"unknown_{index}"
                        print(f"为行 {index} 生成临时ID: unknown_{index}")
                    else:
                        continue
            
            # 将数值型字段转换为字符串
            for field in STR_FIELDS:
                if field in material and material[field] is not None:
                    material[field] = str(material[field])
            
            # 将框架名称标准化
            if '框架' in material:
                # 检查是否包含"不一定很贵"相关字符
                if re.search(r'不一定很贵|bydhg', str(material.get('框架', '')), re.IGNORECASE):
                    material['框架ID'] = 'bydhg'
            
            # 只保留指定字段
            filtered_material = {}
            for field in KEEP_FIELDS:
                if field in material:
                    filtered_material[field] = material[field]
                else:
                    # 对于缺失的字段，填入空字符串
                    filtered_material[field] = ""
            
            # 添加images字段以符合素材数据分析格式
            filtered_material["images"] = {
                "整体流失数_20250515_175020.png": {
                    "main_peak": {
                        "x": "00:00",
                        "y": 0
                    },
                    "secondary_peak": {
                        "x": "00:00",
                        "y": 0
                    },
                    "error": None
                },
                "整体点击次数_20250515_175020.png": {
                    "main_peak": {
                        "x": "00:00",
                        "y": 0
                    },
                    "secondary_peak": {
                        "x": "00:00",
                        "y": 0
                    },
                    "error": None
                }
            }
            # 检查这行是否有有效数据
            if '素材ID' in filtered_material and (filtered_material['素材ID'] != ""):  # 至少有素材ID才算有效数据
                materials_data.append(filtered_material)
            else:
                print(f"跳过行 {index}，缺少素材ID: {filtered_material}")
        
        print(f"\n处理了 {len(materials_data)} 条有效素材数据")
        
        # 确保输出目录存在
        ensure_dir(output_path)
        
        # 写入JSON文件，使用UTF-8编码
        with codecs.open(output_path, 'w', encoding='utf-8') as json_file:
            json_str = json.dumps(materials_data, ensure_ascii=False, indent=2)
            json_file.write(json_str)
            
        print(f"数据已成功保存到: {output_path}")
        
        return True
        
    except Exception as e:
        print(f"处理Excel数据时出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def merge_material_with_peaks(material_json_path, peaks_json_path, output_path):
    """
    合并素材数据和峰值分析结果，相同素材ID的内容合并在一起
    
    Args:
        material_json_path: 素材数据JSON文件路径
        peaks_json_path: 峰值分析JSON文件路径
        output_path: 输出合并后的JSON文件路径
    
    Returns:
        bool: 成功返回True，失败返回False
    """
    try:
        print(f"开始合并素材数据和峰值分析结果...")
        
        # 读取素材数据
        with codecs.open(material_json_path, 'r', encoding='utf-8') as f:
            material_data = json.load(f)
        
        # 读取峰值分析数据
        with codecs.open(peaks_json_path, 'r', encoding='utf-8') as f:
            peaks_data = json.load(f)
        
        print(f"读取素材数据: {len(material_data)} 条")
        print(f"读取峰值分析数据: {len(peaks_data)} 条")
        
        # 创建素材ID到素材数据的映射（字符串类型作为键）
        material_map = {}
        for item in material_data:
            # 确保素材ID是字符串类型
            material_id = str(item.get('素材ID', ''))
            if material_id:
                material_map[material_id] = item
        
        print(f"创建素材ID映射: {len(material_map)} 条")
        
        # 合并数据
        merged_data = []
        matched_count = 0
        processed_material_ids = set()  # 用于跟踪已处理的素材ID
        
        # 先处理峰值分析中的素材
        for material_id, peaks_info in peaks_data.items():
            # 创建基础结构，按照素材数据分析格式.txt的结构
            merged_item = {
                "素材ID": material_id,
                "素材名称": "",
                "素材时长": "",
                "整体消耗": "",
                "整体支付ROI": "",
                "整体成交金额": "",
                "整体转化率": "",
                "整体点击率": "",
                "3秒播放率": "",
                "平均观看时长": "",
                "视频完播率": "",
                "追投调控消耗": "",
                "追投调控成交金额": "",
                "追投调控支付ROI": "",
                "追投调控点击率": "",
                "追投调控转化率": "",
                "基础消耗": "",
                "images": {
                    "整体流失数_20250515_175020.png": {
                        "main_peak": {
                            "x": "00:00",
                            "y": 0
                        },
                        "secondary_peak": {
                            "x": "00:00",
                            "y": 0
                        },
                        "error": None
                    },
                    "整体点击次数_20250515_175020.png": {
                        "main_peak": {
                            "x": "00:00",
                            "y": 0
                        },
                        "secondary_peak": {
                            "x": "00:00",
                            "y": 0
                        },
                        "error": None
                    }
                }
            }
            
            # 添加峰值分析数据
            if "images" in peaks_info:
                # 确保images结构符合新格式
                if isinstance(peaks_info["images"], dict):
                    merged_item["images"] = peaks_info["images"]
                else:
                    # 如果旧格式，转换为新格式
                    print(f"转换素材 {material_id} 的峰值数据为新格式")
            
            # 尝试匹配素材数据
            matched = False
            matched_id = None
            
            # 直接匹配
            if material_id in material_map:
                material_info = material_map[material_id]
                for field in KEEP_FIELDS:
                    if field in material_info and material_info[field] is not None:
                        # 确保特定字段为字符串类型
                        if field in STR_FIELDS:
                            merged_item[field] = str(material_info[field])
                        else:
                            merged_item[field] = material_info[field]
                matched = True
                matched_id = material_id
            else:
                # 尝试将material_id转换为整数再进行匹配
                try:
                    material_id_int = str(int(material_id))
                    if material_id_int in material_map:
                        material_info = material_map[material_id_int]
                        for field in KEEP_FIELDS:
                            if field in material_info and material_info[field] is not None:
                                # 确保特定字段为字符串类型
                                if field in STR_FIELDS:
                                    merged_item[field] = str(material_info[field])
                                else:
                                    merged_item[field] = material_info[field]
                        matched = True
                        matched_id = material_id_int
                except (ValueError, TypeError):
                    pass
            
            if matched:
                matched_count += 1
                processed_material_ids.add(matched_id)
            
            # 添加到合并数据中
            merged_data.append(merged_item)
        
        print(f"成功匹配素材数据: {matched_count}/{len(peaks_data)} 条")
        
        # 处理Excel中存在但峰值分析中不存在的素材
        excel_only_count = 0
        for material_id, material_info in material_map.items():
            if material_id not in processed_material_ids:
                # 创建只有素材数据的项，按照素材数据分析格式.txt的结构
                merged_item = {
                    "素材ID": material_id,
                    "素材名称": "",
                    "素材时长": "",
                    "整体消耗": "",
                    "整体支付ROI": "",
                    "整体成交金额": "",
                    "整体转化率": "",
                    "整体点击率": "",
                    "3秒播放率": "",
                    "平均观看时长": "",
                    "视频完播率": "",
                    "追投调控消耗": "",
                    "追投调控成交金额": "",
                    "追投调控支付ROI": "",
                    "追投调控点击率": "",
                    "追投调控转化率": "",
                    "基础消耗": "",
                    "images": {
                        "整体流失数_20250515_175020.png": {
                            "main_peak": {
                                "x": "00:00",
                                "y": 0
                            },
                            "secondary_peak": {
                                "x": "00:00",
                                "y": 0
                            },
                            "error": None
                        },
                        "整体点击次数_20250515_175020.png": {
                            "main_peak": {
                                "x": "00:00",
                                "y": 0
                            },
                            "secondary_peak": {
                                "x": "00:00",
                                "y": 0
                            },
                            "error": None
                        }
                    }
                }
                
                # 填充素材数据
                for field in KEEP_FIELDS:
                    if field in material_info and material_info[field] is not None:
                        # 确保特定字段为字符串类型
                        if field in STR_FIELDS:
                            merged_item[field] = str(material_info[field])
                        else:
                            merged_item[field] = material_info[field]
                
                merged_data.append(merged_item)
                excel_only_count += 1
        
        print(f"添加仅在Excel中存在的素材: {excel_only_count} 条")
        
        # 确保输出目录存在
        ensure_dir(output_path)
        
        # 写入合并后的JSON文件
        with codecs.open(output_path, 'w', encoding='utf-8') as f:
            json_str = json.dumps(merged_data, ensure_ascii=False, indent=2)
            f.write(json_str)
        
        print(f"成功合并 {len(merged_data)} 条数据，保存到: {output_path}")
        return True
        
    except Exception as e:
        print(f"合并数据时出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    # 设置默认编码为UTF-8
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    
    # 处理命令行参数
    if len(sys.argv) < 2:
        print("用法：")
        print("1. 转换Excel为JSON: python extract_excel_to_json.py [excel_path] [output_json_path]")
        print("2. 合并素材和峰值分析: python extract_excel_to_json.py merge [素材数据JSON路径] [峰值分析JSON路径] [输出JSON路径]")
        
        # 没有参数时，尝试自动查找素材数据文件并处理
        data_dir = os.path.join(ROOT_DIR, "data")
        found_file = find_material_data_file(data_dir)
        if found_file:
            print(f"\n找到素材数据文件: {found_file}")
            print(f"将使用默认输出路径: {OUTPUT_JSON_PATH}")
            success = process_excel_to_json(found_file, OUTPUT_JSON_PATH)
            return 0 if success else 1
        else:
            print(f"\n未找到素材数据文件，请指定Excel文件路径")
            return 1
    
    # 检查是否是合并操作
    if sys.argv[1].lower() == 'merge':
        if len(sys.argv) < 5:
            print("合并模式需要提供3个参数:")
            print("python extract_excel_to_json.py merge [素材数据JSON路径] [峰值分析JSON路径] [输出JSON路径]")
            return 1
        
        material_json_path = sys.argv[2]
        peaks_json_path = sys.argv[3]
        merge_output_path = sys.argv[4]
        
        print(f"执行合并操作:")
        print(f"- 素材数据: {material_json_path}")
        print(f"- 峰值分析: {peaks_json_path}")
        print(f"- 输出路径: {merge_output_path}")
        
        success = merge_material_with_peaks(material_json_path, peaks_json_path, merge_output_path)
        return 0 if success else 1
    else:
        # 默认模式：Excel转JSON
        excel_path = sys.argv[1]
        output_path = OUTPUT_JSON_PATH
        if len(sys.argv) > 2:
            output_path = sys.argv[2]
        
        # 如果指定的Excel路径不存在，尝试模糊匹配
        if not os.path.exists(excel_path):
            data_dir = os.path.dirname(excel_path)
            if not data_dir:
                data_dir = os.path.join(ROOT_DIR, "data")
            
            found_file = find_material_data_file(data_dir)
            if found_file:
                excel_path = found_file
                print(f"找到素材数据文件: {excel_path}")
            else:
                print(f"错误: 未找到素材数据文件")
                return 1
        
        print(f"执行Excel转JSON操作:")
        print(f"- Excel路径: {excel_path}")
        print(f"- 输出路径: {output_path}")
        
        success = process_excel_to_json(excel_path, output_path)
        return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 