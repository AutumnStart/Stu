import json
import os
import csv
import sys
from pprint import pprint

# 尝试导入pandas库用于Excel操作
try:
    import pandas as pd
    EXCEL_SUPPORT = True
except ImportError:
    EXCEL_SUPPORT = False
    print("警告: 未找到pandas库，将使用CSV格式输出。要生成Excel文件，请安装pandas: pip install pandas")

def log_message(message, file=None):
    """
    打印消息并可选地写入日志文件
    
    参数:
        message: 要记录的消息
        file: 可选的日志文件
    """
    print(message)
    if file:
        file.write(message + "\n")
        file.flush()  # 立即写入文件


def flatten_json(data, delimiter='.'):
    """
    将嵌套的JSON结构扁平化为一个字典
    
    参数:
        data: JSON数据
        delimiter: 连接键名时使用的字符
        
    返回:
        扁平化的字典
    """
    flattened = {}
    
    def _flatten(x, prefix=""):
        if isinstance(x, dict):
            for key, value in x.items():
                _flatten(value, f"{prefix}{key}{delimiter}" if prefix else f"{key}{delimiter}")
        elif isinstance(x, list):
            for i, item in enumerate(x):
                _flatten(item, f"{prefix}[{i}]{delimiter}")
        else:
            # 移除尾部的分隔符
            key = prefix[:-len(delimiter)] if prefix.endswith(delimiter) else prefix
            flattened[key] = x
    
    _flatten(data)
    return flattened


def save_to_excel(data, filename="analysis_report.xlsx", log_file=None):
    """
    将扁平化的JSON数据直接保存为水平的Excel表格。
    
    参数:
        data: JSON数据
        filename: 输出Excel文件名
        log_file: 日志文件对象
    """
    # 扁平化JSON结构
    flattened_data = flatten_json(data)
    
    # 计算总字段数
    total_fields = len(flattened_data)
    
    if EXCEL_SUPPORT:
        # 直接构建水平DataFrame，第一行为字段名，第二行为内容
        keys = list(flattened_data.keys())
        values = []
        for v in flattened_data.values():
            if isinstance(v, (list, dict)):
                values.append(str(v))
            else:
                values.append(v)
        
        df_horizontal = pd.DataFrame([keys, values])
        
        # 保存为Excel，不带索引和表头，因为我们已经手动创建了表头行
        df_horizontal.to_excel(filename, index=False, header=False)
        log_message(f"水平Excel表格已保存到 {filename}", log_file)
        
    else:
        # 如果没有pandas，fallback到CSV
        csv_filename = filename.replace('.xlsx', '.csv')
        with open(csv_filename, 'w', encoding='utf-8-sig', newline='') as csv_file:
            writer = csv.writer(csv_file)
            # 第一行写入键（字段名）
            writer.writerow(flattened_data.keys())
            # 第二行写入值（内容）
            values = []
            for v in flattened_data.values():
                if isinstance(v, (list, dict)):
                    values.append(str(v))
                else:
                    values.append(v)
            writer.writerow(values)
        log_message(f"水平CSV表格已保存到 {csv_filename}", log_file)
    
    log_message(f"总共处理了 {total_fields} 个字段", log_file)


def main():
    # 路径修正：定义相对于项目根目录的输入和输出目录
    json_input_dir = "json/留香珠/"  # 修改为只处理“留香珠”文件夹
    output_dir = "analysis_report/"
    output_log_dir = "analysis_report/logs/"
    
    # 路径修正：获取脚本所在目录，并构造绝对路径
    script_dir = os.path.dirname(__file__)
    base_dir = os.path.join(script_dir, '..') # 返回到项目根目录

    abs_json_input_dir = os.path.join(base_dir, json_input_dir)
    abs_output_dir = os.path.join(base_dir, output_dir)
    abs_output_log_dir = os.path.join(base_dir, output_log_dir)

    # 检查输入目录是否存在
    if not os.path.exists(abs_json_input_dir):
        # 如果日志目录可能还未创建，直接打印到控制台
        print(f"错误: 输入目录 '{abs_json_input_dir}' 不存在。程序将退出。")
        return

    # 创建输出目录
    if not os.path.exists(abs_output_dir):
        os.makedirs(abs_output_dir)
        log_message(f"创建输出目录: {abs_output_dir}")
    
    if not os.path.exists(abs_output_log_dir):
        os.makedirs(abs_output_log_dir)
        log_message(f"创建日志目录: {abs_output_log_dir}")

    log_file_path = os.path.join(abs_output_log_dir, "json_analysis.log")

    # 打开日志文件
    with open(log_file_path, 'w', encoding='utf-8') as log_file:
        log_message(f"开始扫描目录 '{abs_json_input_dir}' 查找所有JSON文件...", log_file)
        
        # 遍历目录查找所有JSON文件
        all_json_files = []
        for root, _, files in os.walk(abs_json_input_dir):
            for filename in files:
                if filename.endswith(".json"):
                    full_path = os.path.join(root, filename)
                    # 过滤掉可能的临时文件
                    if not os.path.basename(full_path).startswith('~$'):
                        all_json_files.append(full_path)
        
        if not all_json_files:
            log_message(f"在 '{abs_json_input_dir}' 目录及其子目录中未找到任何JSON文件。", log_file)
            return

        log_message(f"找到 {len(all_json_files)} 个JSON文件，开始处理...", log_file)
        
        processed_count = 0
        for json_file in all_json_files:
            log_message("-" * 50, log_file)
            log_message(f"开始处理文件: {json_file}", log_file)
            
            try:
                # 构建输出文件名，保留相对于“留香珠”目录的子目录结构
                relative_path = os.path.relpath(json_file, abs_json_input_dir)
                output_filename = os.path.splitext(relative_path)[0] + ".xlsx"
                output_file = os.path.join(abs_output_dir, output_filename)
                
                # 创建输出文件的目录
                output_file_dir = os.path.dirname(output_file)
                if not os.path.exists(output_file_dir):
                    os.makedirs(output_file_dir)
                    log_message(f"创建子目录: {output_file_dir}", log_file)

                # 读取JSON文件
                with open(json_file, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                
                # 保存为Excel表格
                save_to_excel(data, output_file, log_file)
                
                log_message(f"处理成功！输出文件: {output_file}", log_file)
                processed_count += 1
            
            except FileNotFoundError:
                log_message(f"错误: 找不到文件 {json_file}", log_file)
            except json.JSONDecodeError:
                log_message(f"错误: {json_file} 中的JSON格式无效", log_file)
            except Exception as e:
                log_message(f"处理 {json_file} 时发生未知错误: {e}", log_file)
        
        log_message("-" * 50, log_file)
        log_message(f"所有文件处理完毕。共处理了 {processed_count}/{len(all_json_files)} 个文件。", log_file)
        log_message(f"详细日志已保存到 {log_file_path}", log_file)


if __name__ == "__main__":
    main()