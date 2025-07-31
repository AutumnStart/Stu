#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import re
import time
from pathlib import Path
import traceback

def extract_material_names(ai_result_file):
    """
    从AI分析结果文件中提取素材名称
    
    Args:
        ai_result_file: AI分析结果文件路径
        
    Returns:
        list: 素材名称和对应在文件中的位置信息的列表
    """
    material_info = []
    
    try:
        with open(ai_result_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用正则表达式匹配素材信息块
        pattern = r'素材: (.*?)\n素材ID: .*?(?=\n-{40}|\Z)'
        matches = re.finditer(pattern, content, re.DOTALL)
        
        for match in matches:
            material_name = match.group(1).strip()
            start_pos = match.start()
            end_pos = match.end()
            
            # 检查该块是否已包含关键用户行为节点分析
            chunk = content[start_pos:end_pos]
            has_analysis = "关键用户行为节点分析:" in chunk
            
            material_info.append({
                'name': material_name,
                'start_pos': start_pos,
                'end_pos': end_pos,
                'has_analysis': has_analysis
            })
        
        return material_info
    except Exception as e:
        print(f"提取素材名称时出错: {str(e)}")
        traceback.print_exc()
        return []

def find_json_file(material_name, base_dir):
    """
    根据素材名称查找对应的JSON文件
    
    Args:
        material_name: 素材名称
        base_dir: 基础目录路径
        
    Returns:
        str: JSON文件的完整路径，如果未找到则返回None
    """
    try:
        # 优先在项目根目录下的json文件夹中查找
        json_dir = base_dir / "json" / "留香珠"
        if json_dir.exists():
            # 构建JSON文件名模式
            json_filename = f"素材分析报告_{material_name}.json"
            json_path = json_dir / json_filename
            
            if json_path.exists():
                return str(json_path)
            
            # 如果找不到精确匹配的文件，尝试模糊匹配
            material_parts = material_name.split('-')
            if len(material_parts) >= 4:  # 至少包含日期、产品、类型和标题
                material_prefix = '-'.join(material_parts[:4])  # 使用前4个部分进行匹配
                
                # 列出目录下的所有文件
                for filename in os.listdir(json_dir):
                    if filename.startswith(f"素材分析报告_{material_prefix}") and filename.endswith(".json"):
                        return str(json_dir / filename)
        
        # 如果项目根目录下没有找到，则在agents目录下的json文件夹中查找（向后兼容）
        agents_json_dir = base_dir / "agents" / "json" / "留香珠"
        if agents_json_dir.exists():
            # 构建JSON文件名模式
            json_filename = f"素材分析报告_{material_name}.json"
            json_path = agents_json_dir / json_filename
            
            if json_path.exists():
                return str(json_path)
            
            # 如果找不到精确匹配的文件，尝试模糊匹配
            material_parts = material_name.split('-')
            if len(material_parts) >= 4:  # 至少包含日期、产品、类型和标题
                material_prefix = '-'.join(material_parts[:4])  # 使用前4个部分进行匹配
                
                # 列出目录下的所有文件
                for filename in os.listdir(agents_json_dir):
                    if filename.startswith(f"素材分析报告_{material_prefix}") and filename.endswith(".json"):
                        return str(agents_json_dir / filename)
        
        return None
    except Exception as e:
        print(f"查找JSON文件时出错: {str(e)}")
        traceback.print_exc()
        return None

def extract_behavior_analysis(json_file):
    """
    从JSON文件中提取关键用户行为节点分析
    
    Args:
        json_file: JSON文件路径
        
    Returns:
        dict: 关键用户行为节点分析数据
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if "关键用户行为节点分析" in data:
            return data["关键用户行为节点分析"]
        else:
            print(f"警告: 未在 {json_file} 中找到关键用户行为节点分析")
            return None
    except json.JSONDecodeError:
        print(f"错误: {json_file} 不是有效的JSON文件")
        return None
    except Exception as e:
        print(f"读取JSON文件 {json_file} 时出错: {str(e)}")
        traceback.print_exc()
        return None

def update_ai_result(ai_result_file, material_info, behavior_analysis_dict):
    """
    将提取的关键用户行为节点分析追加到AI分析结果文件中
    
    Args:
        ai_result_file: AI分析结果文件路径
        material_info: 素材信息，包含名称和文件位置
        behavior_analysis_dict: 素材名称到行为分析的映射
        
    Returns:
        bool: 更新成功返回True，否则返回False
    """
    try:
        with open(ai_result_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 不再创建备份文件
        
        update_count = 0
        # 从后向前处理每个素材块，避免位置变化问题
        for material in sorted(material_info, key=lambda x: x['end_pos'], reverse=True):
            name = material['name']
            end_pos = material['end_pos']
            
            # 检查该素材是否已经有关键用户行为节点分析
            if material.get('has_analysis', False):
                print(f"素材 {name} 已经包含关键用户行为节点分析，跳过更新")
                continue
            
            if name in behavior_analysis_dict and behavior_analysis_dict[name]:
                # 格式化行为分析数据
                behavior_text = "\n\n关键用户行为节点分析:\n"
                analysis = behavior_analysis_dict[name]
                
                for key, value in analysis.items():
                    behavior_text += f"  {key}: {value}\n"
                
                # 在素材块结束处添加行为分析数据
                content = content[:end_pos] + behavior_text + content[end_pos:]
                update_count += 1
        
        # 只有在有更新时才写回文件
        if update_count > 0:
            with open(ai_result_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"成功更新 {update_count} 个素材的关键用户行为节点分析")
        else:
            print("没有需要更新的素材内容")
        
        return True
    except Exception as e:
        print(f"更新AI分析结果文件时出错: {str(e)}")
        traceback.print_exc()
        return False

def clean_duplicate_analysis(ai_result_file):
    """
    清理文件中重复的关键用户行为节点分析
    
    Args:
        ai_result_file: AI分析结果文件路径
        
    Returns:
        bool: 清理成功返回True，否则返回False
    """
    try:
        with open(ai_result_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 不再创建备份文件
        
        # 查找所有素材块
        pattern = r'(素材: .*?)\n-{40}'
        matches = list(re.finditer(pattern, content, re.DOTALL))
        
        # 从后向前处理每个素材块，避免位置变化问题
        cleaned_count = 0
        for i in range(len(matches) - 1, -1, -1):
            match = matches[i]
            material_block = match.group(1)
            
            # 查找该块中的所有关键用户行为节点分析部分
            analysis_pattern = r'\n\n关键用户行为节点分析:([\s\S]*?)(?=\n\n关键用户行为节点分析:|\n-{40}|\Z)'
            analysis_matches = list(re.finditer(analysis_pattern, material_block))
            
            if len(analysis_matches) > 1:
                # 保留第一个分析，删除其余的
                start_pos = match.start(1)
                clean_block = material_block
                
                # 从后向前删除重复的分析，避免位置变化
                for j in range(len(analysis_matches) - 1, 0, -1):
                    dup_match = analysis_matches[j]
                    dup_start = dup_match.start()
                    dup_end = dup_match.end()
                    clean_block = clean_block[:dup_start] + clean_block[dup_end:]
                
                # 更新内容
                content = content[:start_pos] + clean_block + content[match.end(1):]
                cleaned_count += 1
        
        # 只有在有清理时才写回文件
        if cleaned_count > 0:
            with open(ai_result_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"成功清理 {cleaned_count} 个素材中的重复关键用户行为节点分析")
        else:
            print("没有检测到重复的关键用户行为节点分析")
        
        return True
    except Exception as e:
        print(f"清理重复关键用户行为节点分析时出错: {str(e)}")
        traceback.print_exc()
        return False

def main():
    start_time = time.time()
    
    # 定义文件路径
    base_dir = Path(__file__).parent.parent
    ai_result_file = base_dir / "json" / "素材数据分析" / "AI分析结果.txt"
    
    # 首先尝试项目根目录下的json文件夹
    json_dir = base_dir / "json" / "留香珠"
    if not json_dir.exists():
        # 如果项目根目录下没有，则使用agents目录下的json文件夹
        json_dir = base_dir / "agents" / "json" / "留香珠"
    
    print("=" * 50)
    print(f"关键用户行为节点分析提取工具")
    print("=" * 50)
    print(f"处理文件: {ai_result_file}")
    
    # 检查文件是否存在
    if not ai_result_file.exists():
        print(f"错误: AI分析结果文件不存在: {ai_result_file}")
        return
    
    if not json_dir.exists():
        print(f"错误: JSON目录不存在: {json_dir}")
        return
    
    # 首先清理可能存在的重复分析
    print("\n[1/5] 正在清理可能存在的重复分析...")
    clean_duplicate_analysis(ai_result_file)
    
    # 提取素材名称
    print("\n[2/5] 正在提取素材名称...")
    material_info = extract_material_names(ai_result_file)
    if not material_info:
        print("未在AI分析结果文件中找到素材信息")
        return
    
    print(f"找到 {len(material_info)} 个素材")
    
    # 计算需要处理的素材数量
    materials_to_process = [m for m in material_info if not m.get('has_analysis', False)]
    if not materials_to_process:
        print("所有素材已包含关键用户行为节点分析，无需更新")
        return
    
    print(f"需要处理 {len(materials_to_process)} 个素材")
    
    # 为每个素材提取行为分析
    print("\n[3/5] 正在提取关键用户行为节点分析...")
    behavior_analysis_dict = {}
    success_count = 0
    failed_count = 0
    
    for i, material in enumerate(materials_to_process, 1):
        name = material['name']
        print(f"处理素材 [{i}/{len(materials_to_process)}]: {name}")
        
        if material.get('has_analysis', False):
            print(f"  ✓ 已包含关键用户行为节点分析，跳过")
            continue
        
        json_file = find_json_file(name, base_dir)
        if json_file:
            print(f"  找到对应JSON文件: {os.path.basename(json_file)}")
            behavior_analysis = extract_behavior_analysis(json_file)
            if behavior_analysis:
                behavior_analysis_dict[name] = behavior_analysis
                print(f"  ✓ 成功提取关键用户行为节点分析")
                success_count += 1
            else:
                print(f"  ✗ 未能提取关键用户行为节点分析")
                failed_count += 1
        else:
            print(f"  ✗ 未找到素材 {name} 对应的JSON文件")
            failed_count += 1
    
    # 更新AI分析结果文件
    print(f"\n[4/5] 正在更新AI分析结果文件...")
    if behavior_analysis_dict:
        success = update_ai_result(ai_result_file, material_info, behavior_analysis_dict)
        if success:
            print(f"✓ 成功更新AI分析结果文件")
        else:
            print(f"✗ 更新AI分析结果文件失败")
    else:
        print("没有提取到任何关键用户行为节点分析数据，不更新AI分析结果文件")
    
    # 输出统计信息
    elapsed_time = time.time() - start_time
    print("\n[5/5] 处理完成！")
    print("=" * 50)
    print(f"统计信息:")
    print(f"  总素材数: {len(material_info)}")
    print(f"  已包含分析: {len(material_info) - len(materials_to_process)}")
    print(f"  新增分析: {success_count}")
    print(f"  处理失败: {failed_count}")
    print(f"  处理用时: {elapsed_time:.2f}秒")
    print("=" * 50)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"程序执行出错: {str(e)}")
        traceback.print_exc()
        print("\n请将以上错误信息反馈给开发人员")
        input("按任意键退出...")