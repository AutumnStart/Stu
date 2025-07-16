#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import time
import pandas as pd
import requests
from datetime import datetime

class FeishuBitable:
    """飞书多维表格操作类"""
    
    def __init__(self, config_file='feishu_config.json', profile_name=None):
        """初始化飞书API连接
        
        参数:
            config_file: 配置文件路径
            profile_name: 要使用的配置档案名称
        """
        if profile_name is None:
            print("错误: 初始化 FeishuBitable 时必须提供 profile_name。")
            exit(1)
        self.config = self._load_config(config_file, profile_name)
        if not self.config:
            exit(1)
        self.access_token = None
        self.token_expires = 0
        
    def _load_config(self, config_file, profile_name):
        """加载指定profile的配置文件"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                all_configs = json.load(f)

            profiles = all_configs.get("profiles", {})
            profile_config = profiles.get(profile_name)

            if not profile_config:
                print(f"错误: 在 '{config_file}' 的 'profiles' 部分中找不到名为 '{profile_name}' 的配置。")
                return None

            # 创建一个新的、规范化的配置字典，统一处理大小写和别名问题
            final_config = {
                "app_id": profile_config.get("app_id") or profile_config.get("APP_ID"),
                "app_secret": profile_config.get("app_secret") or profile_config.get("APP_SECRET"),
                "bitable_app_token": profile_config.get("base_app_token") or profile_config.get("BASE_APP_TOKEN") or profile_config.get("bitable_app_token"),
                "table_id": profile_config.get("table_id") or profile_config.get("TABLE_ID")
            }

            # 检查必要的键是否存在
            if not all(final_config.values()):
                missing_keys = [k for k, v in final_config.items() if not v]
                print(f"错误: 配置 '{profile_name}' 中缺少必要的键: {missing_keys}")
                return None

            return final_config
        except FileNotFoundError:
            print(f"错误: 配置文件 '{config_file}' 未找到")
            return None
        except json.JSONDecodeError:
            print(f"错误: 配置文件 '{config_file}' 格式不正确，请确保是有效的JSON格式")
            return None
    
    def _get_access_token(self):
        """获取飞书访问令牌"""
        # 如果令牌未过期，则直接返回已有的令牌
        if self.access_token and time.time() < self.token_expires:
            return self.access_token
        
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": self.config["app_id"],
            "app_secret": self.config["app_secret"]
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()  # 如果请求失败，抛出异常
            
            data = response.json()
            if data["code"] != 0:
                print(f"获取访问令牌失败: {data['msg']}")
                return None
                
            # 设置访问令牌和过期时间（提前5分钟过期作为缓冲）
            self.access_token = data["tenant_access_token"]
            self.token_expires = time.time() + data["expire"] - 300
            return self.access_token
            
        except requests.RequestException as e:
            print(f"请求访问令牌时发生错误: {str(e)}")
            return None
    
    def create_records(self, data_list):
        """向已存在的多维表中添加记录
        
        参数:
            data_list: 要添加的数据列表，每项应该是一个字典
        
        返回:
            成功添加的记录数
        """
        token = self._get_access_token()
        if not token:
            return 0
            
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.config['bitable_app_token']}/tables/{self.config['table_id']}/records/batch_create"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 飞书API限制每次最多创建500条记录
        batch_size = 500
        success_count = 0
        
        for i in range(0, len(data_list), batch_size):
            batch = data_list[i:i + batch_size]
            records = [{"fields": item} for item in batch]
            
            payload = {
                "records": records
            }
            
            try:
                response = requests.post(url, headers=headers, json=payload)
                response.raise_for_status()
                
                data = response.json()
                if data["code"] != 0:
                    print(f"批量创建记录失败: {data['msg']}")
                    continue
                    
                success_count += len(data["data"]["records"])
                print(f"成功添加 {len(data['data']['records'])} 条记录")
                
            except requests.RequestException as e:
                print(f"批量创建记录时发生错误: {str(e)}")
                continue
            
            # 添加短暂延迟以避免API限流
            time.sleep(1)
        
        return success_count


def excel_to_feishu(excel_file, config_file='feishu_config.json', profile_name=None):
    """
    将水平格式的Excel文件数据作为单条记录写入飞书多维表，并使用字段映射。
    
    参数:
        excel_file: 水平格式的Excel文件路径
        config_file: 飞书配置文件路径
    
    返回:
        成功添加的记录数 (0或1)
    """
    # 在这里定义从Excel列名到飞书字段名的映射
    # 请根据您在飞书多维表格中实际的列名来填写
    # 左边是Excel中的长列名，右边是飞书中对应的短列名

    # 总结
    # 可以简单记为：
    # 左边（Excel列名）：在映射表里多写了没关系，脚本找不到就会跳过。
    # 右边（飞书列名）：必须和您在飞书表格里设置的字段名一字不差地完全对应，否则就会报错。

    field_mapping = {
        '素材ID': '素材ID',
        '素材名称': '素材名称',
        '分析时间': '分析时间',
        '关键用户行为节点分析.高点击时刻分析': '高点击时刻',
        '关键用户行为节点分析.高流失时刻分析': '高流失时刻',
        '关键用户行为节点分析.开篇用户行为解读': '开篇用户行为解读',
        '内容要素有效性评估.画面表现': '画面表现评估',
        '内容要素有效性评估.音频与BGM': '音频与BGM评估',
        '内容要素有效性评估.视频节奏': '视频节奏评估',
        '内容要素有效性评估.Agent1逻辑要素应用效果.文案强句式应用效果': '文案强句式效果',
        '内容要素有效性评估.Agent1逻辑要素应用效果.痛点解决匹配度评估': '痛点解决匹配度',
        '内容要素有效性评估.Agent1逻辑要素应用效果.美好场景营造效果': '美好场景营造效果',
        '内容要素有效性评估.Agent1逻辑要素应用效果.可视化表现方式效果': '可视化表现效果',
        '内容要素有效性评估.核心卡片关键词有效性': '核心卡片关键词有效性',
        '内容要素有效性评估.关键转化场景/元素分析.识别到的关键转化场景/元素.[0]': '关键转化场景1',
        '内容要素有效性评估.关键转化场景/元素分析.识别到的关键转化场景/元素.[1]': '关键转化场景2',
        '内容要素有效性评估.关键转化场景/元素分析.识别到的关键转化场景/元素.[2]': '关键转化场景3',
        '内容要素有效性评估.关键转化场景/元素分析.识别到的关键转化场景/元素.[3]': '关键转化场景4',
        '内容要素有效性评估.关键转化场景/元素分析.效果评估': '关键转化场景效果评估',
        '综合诊断与归因.整体表现归因': '整体表现归因',
        '综合诊断与归因.调控效果专项分析': '调控效果专项分析',
        '综合诊断与归因.内容层面主要优点.[0]': '主要优点1',
        '综合诊断与归因.内容层面主要优点.[1]': '主要优点2',
        '综合诊断与归因.内容层面主要缺点.[0]': '主要缺点1',
        '综合诊断与归因.内容层面主要缺点.[1]': '主要缺点2',
        '优化建议.针对此条视频修改建议.[0]': '修改建议1',
        '优化建议.针对此条视频修改建议.[1]': '修改建议2',
        '优化建议.针对此条视频修改建议.[2]': '修改建议3',
        '优化建议.针对此条视频修改建议.[3]': '修改建议4',
        '优化建议.后续素材创作建议.[0]': '后续创作建议1',
        '优化建议.后续素材创作建议.[1]': '后续创作建议2',
        '优化建议.后续素材创作建议.[2]': '后续创作建议3',
        '优化建议.后续素材创作建议.[3]': '后续创作建议4',
        '优化建议.后续素材创作建议.[4]': '后续创作建议5',
        '优化建议.A/B测试建议.[0]': 'A/B测试建议1',
        '优化建议.A/B测试建议.[1]': 'A/B测试建议2',
        '优化建议.A/B测试建议.[2]': 'A/B测试建议3',
        '优化建议.A/B测试建议.[3]': 'A/B测试建议4',
        # ... 如果还有其他字段，请继续添加 ...
    }
    
    print(f"开始处理水平格式的Excel文件: {excel_file}")
    
    try:
        # 读取水平的Excel文件，没有表头
        df = pd.read_excel(excel_file, header=None)
        
        if len(df) < 2:
            print("错误: Excel文件内容不足两行，无法解析。应包含一行字段名和一行内容。")
            return 0
            
        print(f"成功读取Excel文件，准备进行字段映射并上传。")
        
        # 第一行作为字段名(keys)，第二行作为内容(values)
        keys = df.iloc[0].tolist()
        values = df.iloc[1].tolist()
        
        # 应用字段映射
        mapped_record = {}
        unmapped_keys = []
        for key, val in zip(keys, values):
            if key in field_mapping:
                feishu_field_name = field_mapping[key]
                
                processed_val = None
                if not pd.isna(val):
                    # 如果值是字符串，则替换换行符
                    if isinstance(val, str):
                        processed_val = val.replace('\n', ' ').replace('\r', '')
                    else:
                        processed_val = val
                
                mapped_record[feishu_field_name] = processed_val
            else:
                unmapped_keys.append(key)
        
        if unmapped_keys:
            print(f"警告: 以下字段在映射表中未找到，将被忽略: {unmapped_keys}")
        
        # 初始化飞书多维表操作类，并传入profile_name
        bitable = FeishuBitable(config_file=config_file, profile_name=profile_name)
        
        # 将映射后的记录包装在列表中，调用现有的批量创建方法
        success_count = bitable.create_records([mapped_record])
        return success_count
        
    except FileNotFoundError:
        print(f"错误: 文件未找到 {excel_file}")
        return 0
    except Exception as e:
        print(f"处理Excel文件时出错: {str(e)}")
        return 0


def find_latest_excel_in_report_dir():
    """在 'analysis_report' 目录下找到最新的Excel文件"""
    report_dir = 'analysis_report'
    excel_files = [f for f in os.listdir(report_dir) if f.endswith('.xlsx') and not f.startswith('~$')]
    if not excel_files:
        print(f"在目录 '{report_dir}' 中没有找到Excel文件。")
        return None
    
    latest_file = max(excel_files, key=lambda f: os.path.getmtime(os.path.join(report_dir, f)))
    return os.path.join(report_dir, latest_file)

def main():
    """主函数"""
    analysis_dir = './analysis_report'
    config_file = 'feishu_config.json'
    # 为这个脚本硬编码指定它应该使用的配置名称
    profile_name_for_this_script = "another_function_placeholder" 
    
    # 检查分析目录是否存在
    if not os.path.exists(analysis_dir):
        print(f"错误: 目录 '{analysis_dir}' 不存在")
        return
    
    # 查找所有Excel文件，并获取完整路径
    all_files = [os.path.join(analysis_dir, f) for f in os.listdir(analysis_dir) if f.endswith('.xlsx')]
    
    if not all_files:
        print(f"在 '{analysis_dir}' 目录中未找到Excel文件")
        return
    
    # 过滤掉临时文件（以~$开头）
    excel_files = [f for f in all_files if not os.path.basename(f).startswith('~$')]

    if not excel_files:
        print(f"在 '{analysis_dir}' 目录中未找到有效的Excel文件")
        return

    # 按文件修改时间降序排序，获取最新的文件
    excel_files.sort(key=os.path.getmtime, reverse=True)
    latest_file = excel_files[0]
    
    print(f"找到最新的Excel文件: {os.path.basename(latest_file)}")
    print("准备将数据写入到已存在的飞书多维表中...")
    
    # 在调用excel_to_feishu时，传入正确的profile_name
    total_records = excel_to_feishu(latest_file, config_file, profile_name=profile_name_for_this_script)
    
    if total_records > 0:
        print(f"\n文件处理完成，共向飞书多维表添加了 {total_records} 条记录")
    
        # 记录执行日志
        log_dir = os.path.join(analysis_dir, 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(log_dir, f'feishu_upload_{timestamp}.log')
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"上传时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"处理文件: {os.path.basename(latest_file)}\n")
            f.write(f"上传记录数: {total_records}\n")
        
        print(f"执行日志已保存到 {log_file}")

if __name__ == "__main__":
    main()
