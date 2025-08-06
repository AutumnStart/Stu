#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TXT文件内容提取并上传到飞书表格工具
TXT Content Extractor and Feishu Uploader

功能：
1. 提取json/素材数据分析文件夹下的txt文件内容
2. 解析AI分析结果的结构化数据
3. 将数据上传到飞书表格

"""

import os
import json
import re
from datetime import datetime
import lark_oapi as lark
from lark_oapi.api.bitable.v1 import CreateAppTableRecordRequest, AppTableRecord

def load_feishu_config(profile_name="ai_analysis_report"):
    """加载飞书配置"""
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

def read_all_txt_content(txt_folder):
    """读取所有txt文件内容并合并为一个字符串"""
    try:
        all_content = []
        txt_files = []
        
        if os.path.exists(txt_folder):
            for file in os.listdir(txt_folder):
                if file.endswith('.txt'):
                    txt_files.append(os.path.join(txt_folder, file))
        
        if not txt_files:
            return None, []
        
        for txt_file in txt_files:
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read()
                file_name = os.path.basename(txt_file)
                all_content.append(f"=== 文件: {file_name} ===\n{content}\n")
        
        # 合并所有内容
        merged_content = "\n".join(all_content)
        
        return merged_content, txt_files
        
    except Exception as e:
        print(f"读取txt文件失败: {e}")
        return None, []

def write_to_feishu_bitable(client, config, record_data):
    """写入数据到飞书多维表格"""
    try:
        # 构建记录
        record = AppTableRecord.builder() \
            .fields(record_data) \
            .build()
        
        # 创建请求
        request = CreateAppTableRecordRequest.builder() \
            .app_token(config["base_app_token"]) \
            .table_id(config["table_id"]) \
            .request_body(record) \
            .build()
        
        # 发送请求
        response = client.bitable.v1.app_table_record.create(request)
        
        if response.success():
            return True
        else:
            print(f"  -> ❌ 上传失败: {response.msg}")
            return False
            
    except Exception as e:
        print(f"  -> ❌ 写入飞书时发生错误: {e}")
        return False

def main():
    """主函数"""
    print("\n" + "="*80)
    print(" TXT文件内容提取并上传到飞书表格工具 v1.0")
    print(" TXT Content Extractor and Feishu Uploader")
    print("="*80)
    print(f" 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # 步骤1: 加载飞书配置
    print("\n🔧 步骤 1/3: 加载飞书配置...")
    feishu_config = load_feishu_config()
    if not feishu_config:
        input("请按回车键退出...")
        return False
    print("  - 飞书配置加载成功。")
    
    # 步骤2: 读取所有txt文件内容
    print("\n📄 步骤 2/3: 读取txt文件内容...")
    
    # 获取txt文件路径
    script_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(script_dir)
    txt_folder = os.path.join(project_root, 'json', '素材数据分析')
    
    # 读取所有txt文件内容
    merged_content, txt_files = read_all_txt_content(txt_folder)
    
    if not merged_content:
        print(f"  - ❌ 在 '{txt_folder}' 目录中未找到txt文件或读取失败。")
        input("请按回车键退出...")
        return False
    
    print(f"  - 📂 找到 {len(txt_files)} 个txt文件")
    print(f"  - 📝 合并内容长度: {len(merged_content)} 字符")
    
    # 创建单条记录，包含所有txt文件的内容
    record_data = {
        "文件数量": len(txt_files),
        "文件列表": ", ".join([os.path.basename(f) for f in txt_files]),
        "合并内容": merged_content,
        "创建时间": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "内容长度": len(merged_content)
    }
    
    all_parsed_data = [record_data]
    
    # 步骤3: 上传到飞书
    print("\n📤 步骤 3/3: 上传数据到飞书表格...")
    feishu_client = lark.Client.builder() \
        .app_id(feishu_config["app_id"]) \
        .app_secret(feishu_config["app_secret"]) \
        .log_level(lark.LogLevel.WARNING) \
        .build()
    
    success_count = 0
    fail_count = 0
    
    for i, record_data in enumerate(all_parsed_data, 1):
        file_list = record_data.get('文件列表', '未知文件')
        print(f"  - 正在上传第 {i}/{len(all_parsed_data)} 条: 包含文件 '{file_list[:50]}'...")
        
        if write_to_feishu_bitable(feishu_client, feishu_config, record_data):
            success_count += 1
            print(f"    -> ✅ 上传成功!")
        else:
            fail_count += 1
    
    # 完成总结
    print("\n" + "="*80)
    print(" 🎉 TXT文件上传流程执行完成！")
    print("="*80)
    print(f" 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n📋 执行摘要:")
    print(f"   ✅ 读取txt文件: {len(txt_files)} 个")
    print(f"   ✅ 合并数据记录: {len(all_parsed_data)} 条")
    print(f"   ✅ 飞书上传成功: {success_count} 条")
    print(f"   ❌ 飞书上传失败: {fail_count} 条")
    print("="*80)
    
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ 用户中断了处理流程")
    except Exception as e:
        print(f"\n\n❌ 处理流程执行过程中发生未知错误: {e}")
    finally:
        input("\n按回车键退出...")