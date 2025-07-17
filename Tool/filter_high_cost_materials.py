#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
素材高消耗筛选并写入飞书多维表格工具
High Cost Materials Filter & Feishu Bitable Uploader

功能：
1. 从'form'文件夹读取最新的、包含'全域数据'关键字的Excel文件。
2. 筛选出'整体消耗'大于10000的素材。
3. 读取'feishu_config.json'中的配置。
4. 连接到指定的飞书多维表格。
5. 将筛选出的高消耗素材数据逐条写入表格。

作者：MiniMax Agent
版本：v4.0 - Feishu Integration
"""

import pandas as pd
import glob
import json
import os
import lark_oapi as lark
from lark_oapi.api.bitable.v1 import CreateAppTableRecordRequest, AppTableRecord

# --- 全局函数区域 ---

def find_cost_column(df):
    """动态查找消耗列名。"""
    potential_columns = ['整体消耗', '消耗', '总消耗', '花费', '总花费', 'cost', 'spend', '总费用']
    for col in potential_columns:
        if col in df.columns:
            return col
    return None

def find_target_excel_file(folder_path, keyword="全域数据"):
    """查找包含关键字的最新Excel文件，忽略临时文件。"""
    # 路径修正：从脚本所在位置(Tool/)返回上一级目录再进入目标文件夹
    abs_folder_path = os.path.join(os.path.dirname(__file__), '..', folder_path)
    list_of_files = glob.glob(os.path.join(abs_folder_path, '*.xlsx'))
    non_temp_files = [f for f in list_of_files if not os.path.basename(f).startswith('~$')]
    keyword_files = [f for f in non_temp_files if keyword in os.path.basename(f)]
    if not keyword_files:
        return None
    return max(keyword_files, key=os.path.getctime)

def _load_feishu_config(profile_name):
    # 路径修正：从脚本所在位置(Tool/)返回上一级目录查找配置文件
    config_file = os.path.join(os.path.dirname(__file__), '..', 'feishu_config.json')
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            all_configs = json.load(f)

        profiles = all_configs.get("profiles", {})
        profile_config = profiles.get(profile_name)

        if not profile_config:
            print(f"错误: 在 '{config_file}' 的 'profiles' 部分中找不到名为 '{profile_name}' 的配置。")
            return None

        final_config = {
            "app_id": profile_config.get("app_id") or profile_config.get("APP_ID"),
            "app_secret": profile_config.get("app_secret") or profile_config.get("APP_SECRET"),
            "base_app_token": profile_config.get("base_app_token") or profile_config.get("BASE_APP_TOKEN"),
            "table_id": profile_config.get("table_id") or profile_config.get("TABLE_ID")
        }

        if not all(final_config.values()):
            missing_keys = [k for k, v in final_config.items() if not v]
            print(f"错误: 配置 '{profile_name}' 中缺少必要的键: {missing_keys}")
            return None
        
        return final_config
    except FileNotFoundError:
        print(f"❌ 错误: 配置文件 '{config_file}' 未找到。")
        return None
    except json.JSONDecodeError:
        print("❌ 错误: 'feishu_config.json' 文件格式不正确。")
        return None

def write_to_feishu_bitable(client, config, record_data):
    """将单条记录写入飞书多维表格。"""
    request = lark.bitable.v1.model.CreateAppTableRecordRequest.builder() \
        .app_token(config["base_app_token"]) \
        .table_id(config["table_id"]) \
        .request_body(lark.bitable.v1.model.AppTableRecord.builder().fields(record_data).build()) \
        .build()

    try:
        response = client.bitable.v1.app_table_record.create(request)

        if not response.success():
            lark.logger.error(
                f"调用飞书API失败, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}"
            )
            return False
        
        print(f"  -> ✅ 上传成功!")
        return True
    except Exception as e:
        print(f"  - 写入飞书时发生网络或API错误: {e}")
        return False

def safe_convert_to_float(value):
    """
    【新增】安全地将值转换为浮点数。
    - 处理含'%'的百分比字符串。
    - 处理含','的千位分隔符字符串。
    - 忽略无法转换的值，返回None。
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        # 如果已经是数字，直接返回
        if isinstance(value, (int, float)):
            return float(value)
        
        # 如果是字符串，进行清洗
        s_value = str(value).strip()
        if '%' in s_value:
            # 是百分比，移除'%'并除以100
            return float(s_value.replace('%', '')) / 100.0
        elif ',' in s_value:
            # 是带千位符的数字，移除','
            return float(s_value.replace(',', ''))
        else:
            # 尝试直接转换
            return float(s_value)
    except (ValueError, TypeError):
        # 转换失败则返回None
        return None

def check_feishu_table_fields(client, config):
    """
    【新增】表格结构自检功能。
    连接到飞书，获取表的实际字段，并与脚本要求的字段进行比对。
    """
    print("  - 正在进行飞书表格结构自检...")
    try:
        # 1. 构建请求以获取指定表的字段列表
        field_request = lark.api.bitable.v1.ListAppTableFieldRequest.builder() \
            .app_token(config["base_app_token"]) \
            .table_id(config["table_id"]) \
            .build()
        
        # 2. 发送API请求
        response = client.bitable.v1.app_table_field.list(field_request)

        # 3. 检查API调用是否成功
        if not response.success():
            print(f"  - ❌ 自检失败：无法获取表格字段列表。飞书API错误: {response.msg}")
            print(f"    请检查feishu_config.json中的 'base_app_token' 和 'table_id' 是否正确，")
            print(f"    以及机器人是否已被添加为该表格的协作者。")
            return False

        # 4. 提取表格中实际存在的字段名
        actual_fields = set()
        if response.data and response.data.items:
            actual_fields = {field.field_name for field in response.data.items}
        
        print(f"  - ✅ 成功获取表格结构，包含字段: {sorted(list(actual_fields))}")

        # 5. 定义脚本需要上传的字段名集合
        required_fields = {
            "素材ID", "素材名称", "消耗", "创建日期", "评审", "整体支付ROI", # 修正：将'AI建议'改为'评审'
            "整体成交金额", "整体转化率", "整体点击率", "基础消耗", "平均观看时长",
            "3秒播放率", "视频完播率", "追投调控消耗", "追投调控成交金额", 
            "追投调控支付ROI", "追投调控转化率"
        }
        
        # 6. 对比，找出缺失的字段
        missing_fields = required_fields - actual_fields
        
        if not missing_fields:
            print("  - ✅ 表格结构自检通过，所有必需字段均存在。")
            return True
        else:
            print("\n  - ❌ 自检失败：发现字段不匹配！")
            print(f"    - 脚本需要的字段: {sorted(list(required_fields))}")
            print(f"    - 飞书表格现有的字段: {sorted(list(actual_fields))}")
            print(f"    - ❗❗【请重点检查】以下脚本需要的字段，在您的飞书表格中【不存在】或【名称不完全匹配】(注意空格或错别字):")
            for field in sorted(list(missing_fields)):
                print(f"      - \"{field}\"")
            return False

    except Exception as e:
        print(f"  - ❌ 自检过程中发生未知异常: {e}")
        return False

# --- 主逻辑 ---

if __name__ == "__main__":
    # 1. 初始化
    print("==========================================================")
    print(" 素材高消耗筛选及飞书上传工具 v4.1 (多目标版)")
    print("==========================================================")
    excel_folder = 'form'
    cost_threshold = 10000
    config_profile_name = "high_cost_report" # 指定要使用的配置档案

    # 2. 加载飞书配置
    print(f"\n1. 正在加载飞书配置 (Profile: {config_profile_name})...")
    feishu_config = _load_feishu_config(config_profile_name)
    if not feishu_config:
        input("请按回车键退出...")
        exit()
    print("  - 飞书配置加载成功。")

    # 3. 查找并读取Excel文件
    print("\n2. 正在查找并读取数据文件...")
    target_excel_file = find_target_excel_file(excel_folder)
    if not target_excel_file:
        print(f"  - ❌ 在 '{excel_folder}' 目录中未找到包含'全域数据'的Excel文件。")
        input("请按回车键退出...")
        exit()
    
    print(f"  - 📂 找到目标文件: {target_excel_file}")
    try:
        # 修正1：使用 converters 强制将所有可能的ID列作为文本读取，杜绝精度丢失
        possible_id_cols = ['素材ID', '素材id', 'material_id', '视频ID']
        converters = {col: str for col in possible_id_cols}
        df = pd.read_excel(target_excel_file, engine='openpyxl', thousands=',', converters=converters)
        print("  - 文件读取并解析成功。")
    except Exception as e:
        print(f"  - ❌ 读取Excel文件时出错: {e}")
        input("请按回车键退出...")
        exit()

    # 4. 筛选高消耗数据
    print("\n3. 正在筛选高消耗素材...")
    cost_column = find_cost_column(df)
    if not cost_column:
        print(f"  - ❌ 在文件中找不到可识别的消耗列。")
        input("请按回车键退出...")
        exit()
        
    df[cost_column] = pd.to_numeric(df[cost_column], errors='coerce')
    high_cost_materials = df.dropna(subset=[cost_column])
    high_cost_materials = high_cost_materials[high_cost_materials[cost_column] > cost_threshold].copy()

    if high_cost_materials.empty:
        print(f"  - ✅ 没有找到消耗高于 {cost_threshold} 的素材。")
        print("\n所有操作完成。")
        input("请按回车键退出...")
        exit()

    print(f"  - ✅ 找到 {len(high_cost_materials)} 条高消耗素材，准备上传。")

    # 5. 上传到飞书
    print("\n4. 正在连接飞书并上传数据...")
    feishu_client = lark.Client.builder() \
        .app_id(feishu_config["app_id"]) \
        .app_secret(feishu_config["app_secret"]) \
        .log_level(lark.LogLevel.WARNING) \
        .build()

    # 在上传前执行一次表格结构自检
    if not check_feishu_table_fields(feishu_client, feishu_config):
        input("\n请根据上面的提示检查并修正飞书表格中的列名，然后重新运行脚本。按回车键退出...")
        exit()

    print("\n5. 开始上传数据...")
    success_count = 0
    fail_count = 0

    for index, row in high_cost_materials.iterrows():
        # a. 准备基础信息
        material_id = str(row.get('素材ID', ''))
        material_name = str(row.get('素材名称', '未知素材'))
        print(f"  - 正在上传: '{material_name[:50]}'...")

        # b. 安全地处理【消耗】字段
        cost_value = None
        raw_cost = row.get(cost_column)
        if raw_cost is not None and pd.notna(raw_cost):
            try:
                cost_value = float(raw_cost)
            except (ValueError, TypeError):
                pass # 无法转换则保持None

        # c. 安全地处理【创建日期】字段
        date_value = None
        raw_date = row.get('素材创建时间') # 修正：使用正确的列名'素材创建时间'
        if raw_date is not None and pd.notna(raw_date):
            if isinstance(raw_date, pd.Timestamp):
                date_value = raw_date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                date_value = str(raw_date)

        # d. 构建最终只包含目标字段的数据包
        final_record_raw = {
            "素材ID": material_id,
            "素材名称": material_name,
            "消耗": cost_value,
            "创建日期": date_value,
            "评审": "等待AI生成建议...", # 修正：将'AI建议'改为'评审'
            
            # --- 效果指标 (区分类型处理) ---
            # 数字类型，需要安全转换
            "整体支付ROI": safe_convert_to_float(row.get('整体支付ROI')),
            "整体成交金额": safe_convert_to_float(row.get('整体成交金额')),
            # 文本类型，直接获取原始字符串
            "整体转化率": str(row.get('整体转化率', '') or ''),
            "整体点击率": str(row.get('整体点击率', '') or ''),

            # --- 新增的详细效果指标 ---
            "基础消耗": safe_convert_to_float(row.get('基础消耗')),
            "平均观看时长": str(row.get('平均观看时长', '') or ''),
            "3秒播放率": str(row.get('3秒播放率', '') or ''),
            "视频完播率": str(row.get('视频完播率', '') or ''),
            "追投调控消耗": safe_convert_to_float(row.get('追投调控消耗')),
            "追投调控成交金额": safe_convert_to_float(row.get('追投调控成交金额')),
            "追投调控支付ROI": safe_convert_to_float(row.get('追投调控支付ROI')),
            "追投调控转化率": str(row.get('追投调控转化率', '') or '')
        }

        # 清理字典中的NaN/NaT值，转换为None以兼容JSON和飞书API
        final_record = {k: (v if pd.notna(v) else None) for k, v in final_record_raw.items()}

        # e. 上传干净的数据包
        if write_to_feishu_bitable(feishu_client, feishu_config, final_record):
            success_count += 1
        else:
            fail_count += 1

    print("\n-----------------------------------------")
    print("上传完成!")
    print(f"  - 成功: {success_count}条")
    print(f"  - 失败: {fail_count}条")
    print("==========================================================")
    input("请按回车键退出...") 