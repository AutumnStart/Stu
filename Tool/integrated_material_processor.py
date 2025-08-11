#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成素材处理工具
Integrated Material Processing Tool

功能：
1. 从'form'文件夹读取最新的、包含'全域'关键字的Excel文件
2. 筛选出'整体消耗'大于10000的素材
3. 保存符合条件的素材ID到JSON文件
4. 自动启动浏览器下载视频和截图
5. 最后一次性上传完整数据（包含附件）到飞书表格

"""

import pandas as pd
import glob
import json
import os
import sys
import time
import re
import shutil
from datetime import datetime
import lark_oapi as lark
from lark_oapi.api.bitable.v1 import CreateAppTableRecordRequest, AppTableRecord
from lark_oapi.api.drive.v1 import UploadAllMediaRequest, UploadAllMediaRequestBody
import mimetypes
from playwright.sync_api import Playwright, sync_playwright, expect

# 导入下载视频模块
try:
    import download_videos
except ImportError:
    print("⚠️ 警告: 无法导入 download_videos 模块，视频下载功能可能不可用")
    download_videos = None

# --- 数据处理函数区域 ---

def find_cost_column(df):
    """动态查找消耗列名。"""
    potential_columns = ['整体消耗', '消耗', '总消耗', '花费', '总花费', 'cost', 'spend', '总费用']
    for col in potential_columns:
        if col in df.columns:
            return col
    return None

def find_target_excel_file(folder_path, keyword="全域"):
    """查找包含关键字的最新Excel文件，忽略临时文件。"""
    abs_folder_path = os.path.join(os.path.dirname(__file__), '..', folder_path)
    list_of_files = glob.glob(os.path.join(abs_folder_path, '*.xlsx'))
    non_temp_files = [f for f in list_of_files if not os.path.basename(f).startswith('~$')]
    keyword_files = [f for f in non_temp_files if keyword in os.path.basename(f)]
    if not keyword_files:
        return None
    return max(keyword_files, key=os.path.getctime)

def _load_feishu_config(profile_name):
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

def safe_convert_to_float(value):
    """安全地将值转换为浮点数。"""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        if isinstance(value, (int, float)):
            return float(value)
        
        s_value = str(value).strip()
        if '%' in s_value:
            return float(s_value.replace('%', '')) / 100.0
        elif ',' in s_value:
            return float(s_value.replace(',', ''))
        else:
            return float(s_value)
    except (ValueError, TypeError):
        return None

def convert_duration_to_seconds(duration):
    """将 'HH:MM:SS' 或 'MM:SS' 格式的字符串转换为总秒数。"""
    if duration is None or (isinstance(duration, float) and pd.isna(duration)):
        return None
    if isinstance(duration, (int, float)):
        return float(duration)
    
    s_duration = str(duration).strip()
    parts = s_duration.split(':')
    try:
        if len(parts) == 1:
            return float(parts[0])
        elif len(parts) == 2:
            return float(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 3:
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
        else:
            return None
    except (ValueError, TypeError):
        return None

def save_material_ids_to_json(material_ids, base_folder='json'):
    """将符合要求的素材ID保存到json文件夹下的裂变素材ID文件夹中。"""
    try:
        script_dir = os.path.dirname(__file__)
        project_root = os.path.dirname(script_dir)
        json_folder = os.path.join(project_root, base_folder)
        target_folder = os.path.join(json_folder, '裂变素材ID')
        
        os.makedirs(target_folder, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'裂变素材ID_{timestamp}.json'
        filepath = os.path.join(target_folder, filename)
        
        data = {
            'timestamp': timestamp,
            'total_count': len(material_ids),
            'material_ids': material_ids,
            'description': '符合高消耗筛选条件的素材ID列表'
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"  - ✅ 素材ID已保存到: {filepath}")
        print(f"  - 📊 共保存 {len(material_ids)} 个素材ID")
        return filepath
        
    except Exception as e:
        print(f"  - ❌ 保存素材ID时发生错误: {e}")
        return None

# --- 浏览器自动化函数区域 ---

def handle_popups(page):
    """处理页面上的各种弹窗"""
    try:
        try:
            selector = "body > div:nth-child(49) > div > div.c-lib-guide-mask > div > div.c-lib-guide-body > div.c-lib-guide-bottom > div"
            page.wait_for_selector(selector, timeout=15000, state="visible")
            page.locator(selector).click()
            print("成功关闭'我知道了'弹窗")
        except Exception as e:
            print(f"关闭'我知道了'弹窗失败: {e}")
        
        try:
            skip_button = page.locator("button.firefly-modal-multi-step-skip").first
            skip_button.click(timeout=15000)
            print("成功点击'跳过'按钮")
        except Exception as e:
            print(f"点击'跳过'按钮失败: {e}")
        
        return True
    except Exception as e:
        print(f"处理弹窗过程中发生错误: {e}")
        return False

def search_and_capture_material(page, material_id, output_dir):
    """搜索素材并截取图表"""
    try:
        print(f"开始搜索素材ID: {material_id}")
        try:
            search_box = page.get_by_role("textbox", name="输入素材名称或ID")
            search_box.click()
            search_box.fill("")
            search_box.fill(material_id)
            search_box.press("Enter")
            print(f"已搜索素材ID: {material_id}")
            time.sleep(3)
        except Exception as e:
            print(f"搜索素材ID失败: {e}")

        # 下载视频
        try:
            print("\n===== 开始下载视频 =====")
            if download_videos:
                root_dir = download_videos.get_root_dir()
                video_save_dir = os.path.join(root_dir, 'storage', 'video', '留香珠')
                download_result = download_videos.download_video(page, video_save_dir)
                
                if download_result["success"]:
                    if download_result.get("skipped", False):
                        print(f"视频已存在，跳过下载: {download_result['video_path']}")
                    else:
                        print(f"视频下载成功: {download_result['video_path']}")
                else:
                    print(f"视频下载失败: {download_result.get('error', '未知错误')}")
            else:
                print("下载视频模块不可用，跳过视频下载")
        except Exception as e:
            print(f"下载视频过程中发生错误: {e}")
        
        # 点击分析按钮
        try:
            print("点击分析按钮进入内容分析模块...")
            page.locator("div:nth-child(2) > span > .analyse").first.click()
            print("成功点击分析按钮")
            time.sleep(5)
        except Exception as e:
            print(f"点击分析按钮失败: {e}")
        
        # 截取图表
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 截取整体点击次数曲线图
        print(f"开始为素材ID: {material_id} 截取图表")
        capture_chart(page, "整体点击次数", output_dir, f"整体点击次数_{timestamp}")
        
        # 截取整体流失数曲线图
        capture_loss_chart(page, output_dir, f"整体流失数_{timestamp}")
        
        # 截取八大人群分布人数图表
        try:
            print("\n===== 切换到人群分析 =====")
            page.locator("div").filter(has_text=re.compile(r"^人群分析$")).first.click()
            print("成功点击人群分析选项卡")
            time.sleep(3)
            
            capture_population_chart(page, output_dir, f"八大人群分布人数整体展现次数_{timestamp}")
            
            page.locator("div.ovui-input__prefix:has-text('展示指标：')").click()
            page.locator("div.ovui-cascader-panel__item-label:has-text('整体成交金额')").click()
            time.sleep(5)
            capture_population_chart(page, output_dir, f"八大人群分布人数整体成交金额_{timestamp}")
            
            page.locator("div.ovui-input__prefix:has-text('展示指标：')").click()
            page.locator("div.ovui-cascader-panel__item-label:has-text('整体点击次数')").click()
            time.sleep(5)
            capture_population_chart(page, output_dir, f"八大人群分布人数整体点击次数_{timestamp}")
        except Exception as e:
            print(f"切换到人群分析失败: {e}")
            
        # 关闭分析模块
        try:
            print("\n===== 关闭分析模块 =====")
            page.locator(".oc-drawer-close").click()
            print("成功关闭分析模块")
            time.sleep(3)
        except Exception as e:
            print(f"关闭分析模块失败: {e}")
            
        print(f"已完成素材ID: {material_id} 的所有图表截取")
        return True
    except Exception as e:
        print(f"处理素材ID时出错: {e}")
        return False

def capture_loss_chart(page, screenshots_dir, file_prefix):
    """截取整体流失数图表"""
    print("\n===== 开始截取整体流失数图表 =====")
    try:
        loss_selector = "div.ovui-radio-item[data-e2e='oc_emptyKey_dataV2/bidding/site-promotion_video_lose_count_for_roi2']"
        
        try:
            page.locator(loss_selector).click(timeout=10000)
            print("使用精确选择器成功点击'整体流失数'选项卡")
        except Exception as e:
            print(f"使用精确选择器点击失败: {e}")
            
        time.sleep(3)
        
        screenshot_path = os.path.join(screenshots_dir, f"{file_prefix}.png")
        
        try:
            canvas = page.locator("canvas[width='826'][height='320']")
            canvas.screenshot(path=screenshot_path)
            print(f"成功截取整体流失数曲线图: {screenshot_path}")
            return screenshot_path
        except Exception as e:
            print(f"截取canvas元素失败: {e}")
            
    except Exception as e:
        print(f"截取整体流失数图表时出错: {e}")
        return None

def capture_chart(page, chart_name, screenshots_dir, file_prefix, click_position={"x": 19, "y": 293}):
    """截取图表"""
    print(f"\n===== 开始截取{chart_name}图表 =====")
    
    try:
        page.get_by_text(chart_name).nth(1).click(timeout=10000)
        print(f"使用索引方式成功点击{chart_name}选项卡")
    except Exception as e1:
        print(f"使用索引方式点击{chart_name}选项卡失败: {e1}")
            
    time.sleep(3)
    
    try:
        page.locator("canvas").click(position=click_position)
        print(f"成功点击{chart_name}图表")
    except Exception as e:
        print(f"点击{chart_name}图表失败: {e}")
    
    time.sleep(3)
    
    try:
        chart_path = os.path.join(screenshots_dir, f"{file_prefix}.png")
        canvas = page.locator("canvas").first
        canvas.screenshot(path=chart_path)
        print(f"成功截取{chart_name}图表，保存为: {chart_path}")
        return chart_path
    except Exception as e:
        print(f"截取canvas元素失败: {e}")

def capture_population_chart(page, screenshots_dir, file_prefix):
    """截取八大人群分布人数图表"""
    print("\n===== 开始截取八大人群分布人数图表 =====")
    
    try:
        try:
            page.locator("div").filter(has_text=re.compile(r".*人群分布.*")).first.click(timeout=10000)
            print("通过模糊文本成功点击八大人群分布人数选项卡")
        except Exception as e3:
            print(f"通过模糊文本点击失败: {e3}")
                    
        time.sleep(3)
        
        screenshot_path = os.path.join(screenshots_dir, f"{file_prefix}.png")
        
        try:
            js_get_main_canvas = '''
            (function() {
                const canvases = Array.from(document.querySelectorAll('canvas'));
                if (canvases.length === 0) return null;
                
                canvases.sort((a, b) => {
                    const areaA = a.width * a.height;
                    const areaB = b.width * b.height;
                    return areaB - areaA;
                });
                
                const mainCanvas = canvases[0];
                return {
                    index: 0,
                    width: mainCanvas.width,
                    height: mainCanvas.height,
                    id: mainCanvas.id,
                    className: mainCanvas.className
                };
            })();
            '''
            canvas_info = page.evaluate(js_get_main_canvas)
            print(f"找到可能的主canvas元素: {canvas_info}")
            
            if canvas_info:
                if canvas_info.get("id"):
                    main_canvas = page.locator(f"canvas#{canvas_info['id']}")
                elif canvas_info.get("className"):
                    main_canvas = page.locator(f"canvas.{canvas_info['className'].split(' ')[0]}")
                else:
                    main_canvas = page.locator("canvas").nth(canvas_info["index"])
                
                main_canvas.screenshot(path=screenshot_path)
                print(f"成功截取八大人群分布人数图表，保存为: {screenshot_path}")
                return screenshot_path
        except Exception as e:
            print(f"通过特定特征定位canvas失败: {e}")
            
    except Exception as e:
        print(f"处理八大人群分布人数图表时出错: {e}")
        return None

def run_browser_automation(material_ids):
    """运行浏览器自动化，下载视频和截图"""
    print("\n" + "="*60)
    print(" 开始浏览器自动化流程")
    print("="*60)
    
    # 获取项目根目录路径
    script_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(script_dir)
    
    main_screenshot_dir = os.path.join(project_root, "screenshots_liebian")
    error_dir = os.path.join(main_screenshot_dir, "errors")
    os.makedirs(main_screenshot_dir, exist_ok=True)
    os.makedirs(error_dir, exist_ok=True)
    
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # 登录巨量引擎
            print("正在登录巨量引擎...")
            page.goto("https://business.oceanengine.com/login?appKey=80")
            page.get_by_text("邮箱登录").click()
            page.get_by_role("textbox", name="请输入邮箱").click()
            page.get_by_role("textbox", name="请输入邮箱").fill("tianqi.wang@gewuchuanmei.com")
            page.get_by_role("textbox", name="请输入邮箱").press("Tab")
            page.get_by_role("textbox", name="密码").fill("Soulink-88818")
            page.locator("use").nth(1).click()
            page.get_by_role("button", name="登录").click()

            page.wait_for_load_state("networkidle")
            print("登录成功!")
            time.sleep(3)
            
            # 打开智联页面
            with page.expect_popup() as page1_info:
                page.get_by_text("智联（卓尔01）-PWU-留香珠").click()
            page1 = page1_info.value
            
            # 导航到数据分析页面
            page1.get_by_role("button", name="数据").click()
            page1.locator("a").filter(has_text="全域数据").click()
            time.sleep(3)
            
            page1.locator("div").filter(has_text=re.compile(r"^素材数据$")).nth(2).click()
            time.sleep(3)
            
            # 批量处理素材ID
            for i, material_id in enumerate(material_ids):
                material_id_str = str(material_id)
                material_screenshot_dir = os.path.join(main_screenshot_dir, f"Material_{material_id_str}")
                
                # 检查结果是否已存在
                if os.path.exists(material_screenshot_dir) and len([name for name in os.listdir(material_screenshot_dir) if name.endswith('.png')]) >= 2:
                    print(f"结果已存在，跳过素材ID: {material_id_str}")
                    continue

                print(f"\n{'='*20} 开始处理第 {i+1}/{len(material_ids)} 个素材: {material_id_str} {'='*20}")
                
                try:
                    os.makedirs(material_screenshot_dir, exist_ok=True)
                    print(f"创建素材截图目录: {material_screenshot_dir}")
                    
                    time.sleep(2)
                    
                    success = search_and_capture_material(page1, material_id_str, material_screenshot_dir)
                    
                    if success:
                        print(f"成功处理素材ID {material_id_str} 并截取图表。截图保存在: {material_screenshot_dir}")
                    else:
                        print(f"处理素材ID {material_id_str} 失败。")

                except Exception as e:
                    print(f"处理素材ID {material_id_str} 时出错: {e}")
                    try:
                        error_path = os.path.join(material_screenshot_dir, f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                        page1.screenshot(path=error_path)
                        print(f"已保存错误状态截图: {error_path}")
                    except Exception as err:
                        print(f"无法保存错误状态截图: {err}")
            
        except Exception as e:
            print(f"发生严重错误: {e}")
            try:
                error_path = os.path.join(error_dir, f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                page.screenshot(path=error_path)
                print(f"已保存错误状态截图: {error_path}")
            except Exception as err:
                print(f"无法保存错误状态截图: {err}")
        finally:
            context.close()
            browser.close()
            print("浏览器已关闭")

# --- 飞书上传函数区域 ---

def check_feishu_table_fields(client, config):
    """表格结构自检功能"""
    print("  - 正在进行飞书表格结构自检...")
    try:
        field_request = lark.api.bitable.v1.ListAppTableFieldRequest.builder() \
            .app_token(config["base_app_token"]) \
            .table_id(config["table_id"]) \
            .build()
        
        response = client.bitable.v1.app_table_field.list(field_request)

        if not response.success():
            print(f"  - ❌ 自检失败：无法获取表格字段列表。飞书API错误: {response.msg}")
            return False

        actual_fields = set()
        if response.data and response.data.items:
            actual_fields = {field.field_name for field in response.data.items}
        
        print(f"  - ✅ 成功获取表格结构，包含字段: {sorted(list(actual_fields))}")

        required_fields = {
            "素材ID", "素材名称", "消耗", "创建日期", "评审", "整体支付ROI",
            "整体成交金额", "整体转化率", "整体点击率", "基础消耗", "平均观看时长",
            "3秒播放率", "视频完播率", "追投调控消耗", "追投调控成交金额", 
            "追投调控支付ROI", "追投调控转化率", "图片内容", "视频内容"
        }
        
        missing_fields = required_fields - actual_fields
        
        if not missing_fields:
            print("  - ✅ 表格结构自检通过，所有必需字段均存在。")
            return True
        else:
            print("\n  - ❌ 自检失败：发现字段不匹配！")
            print(f"    - 脚本需要的字段: {sorted(list(required_fields))}")
            print(f"    - 飞书表格现有的字段: {sorted(list(actual_fields))}")
            print(f"    - ❗❗【请重点检查】以下脚本需要的字段，在您的飞书表格中【不存在】或【名称不完全匹配】:")
            for field in sorted(list(missing_fields)):
                print(f"      - \"{field}\"")
            return False

    except Exception as e:
        print(f"  - ❌ 自检过程中发生未知异常: {e}")
        return False

def upload_file_to_feishu(client, file_path, file_name, app_token):
    """上传文件到飞书多维表格并返回文件token"""
    file_handle = None
    try:
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                mime_type = 'image/png' if file_path.lower().endswith('.png') else 'image/jpeg'
            elif file_path.lower().endswith('.mp4'):
                mime_type = 'video/mp4'
            else:
                mime_type = 'application/octet-stream'
        
        file_handle = open(file_path, 'rb')
        
        request = UploadAllMediaRequest.builder() \
            .request_body(UploadAllMediaRequestBody.builder()
                .file_name(file_name)
                .parent_type("bitable_file")
                .parent_node(app_token)
                .size(os.path.getsize(file_path))
                .file(file_handle)
                .build()) \
            .build()
        
        response = client.drive.v1.media.upload_all(request)
        
        if response.success() and response.data:
            file_token = response.data.file_token
            print(f"    -> ✅ 文件上传成功: {file_name} (token: {file_token[:20]}...)")
            return file_token
        else:
            print(f"    -> ❌ 文件上传失败: {file_name}, 错误: {response.msg}")
            return None
            
    except Exception as e:
        print(f"    -> ❌ 上传文件时发生异常: {file_name}, 错误: {e}")
        return None
    finally:
        if file_handle:
            file_handle.close()

def find_material_images(material_id, screenshots_folder='screenshots_liebian'):
    """根据素材ID查找对应的截图文件"""
    script_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(script_dir)
    screenshots_path = os.path.join(project_root, screenshots_folder)
    
    material_folder = f"Material_{material_id}"
    material_path = os.path.join(screenshots_path, material_folder)
    
    if not os.path.exists(material_path):
        print(f"    -> ⚠️ 未找到素材ID {material_id} 对应的截图文件夹")
        return []
    
    image_files = []
    for file in os.listdir(material_path):
        if file.lower().endswith('.png'):
            image_files.append(os.path.join(material_path, file))
    
    return sorted(image_files)

def find_material_video(material_name, video_folder='storage/video/留香珠'):
    """根据素材名称查找对应的视频文件"""
    script_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(script_dir)
    video_path = os.path.join(project_root, video_folder)
    
    if not os.path.exists(video_path):
        print(f"    -> ⚠️ 视频文件夹不存在: {video_path}")
        return None
    
    for file in os.listdir(video_path):
        if file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            if material_name in file or any(part in file for part in material_name.split()):
                return os.path.join(video_path, file)
    
    print(f"    -> ⚠️ 未找到素材名称 '{material_name}' 对应的视频文件")
    return None

def upload_material_attachments(client, material_id, material_name, app_token):
    """上传素材的图片和视频附件"""
    attachments = {
        '图片内容': [],
        '视频内容': []
    }
    
    # 上传图片
    print(f"    - 正在查找素材ID {material_id} 的截图...")
    image_files = find_material_images(material_id)
    if image_files:
        print(f"    - 找到 {len(image_files)} 个截图文件")
        for img_file in image_files:
            file_name = os.path.basename(img_file)
            token = upload_file_to_feishu(client, img_file, file_name, app_token)
            if token:
                attachments['图片内容'].append({
                    'file_token': token,
                    'name': file_name,
                    'type': 'image'
                })
    
    # 上传视频
    print(f"    - 正在查找素材名称 '{material_name}' 的视频...")
    video_file = find_material_video(material_name)
    if video_file:
        file_name = os.path.basename(video_file)
        print(f"    - 找到视频文件: {file_name}")
        token = upload_file_to_feishu(client, video_file, file_name, app_token)
        if token:
            attachments['视频内容'].append({
                'file_token': token,
                'name': file_name,
                'type': 'video'
            })
    
    return attachments

def write_to_feishu_bitable(client, config, record_data):
    """将单条记录写入飞书多维表格"""
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

# --- 主逻辑 ---

def main():
    """主函数"""
    print("\n" + "="*80)
    print(" 集成素材处理工具 v1.0")
    print(" Integrated Material Processing Tool")
    print("="*80)
    print(f" 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    excel_folder = 'form'
    cost_threshold = 10000
    config_profile_name = "high_cost_report"

    # 步骤1: 加载飞书配置
    print(f"\n🔧 步骤 1/4: 加载飞书配置 (Profile: {config_profile_name})...")
    feishu_config = _load_feishu_config(config_profile_name)
    if not feishu_config:
        input("请按回车键退出...")
        return False
    print("  - 飞书配置加载成功。")

    # 步骤2: 查找并读取Excel文件，筛选高消耗素材
    print("\n📊 步骤 2/4: 筛选高消耗素材...")
    target_excel_file = find_target_excel_file(excel_folder)
    if not target_excel_file:
        print(f"  - ❌ 在 '{excel_folder}' 目录中未找到包含'全域'关键字的Excel文件。")
        input("请按回车键退出...")
        return False
    
    print(f"  - 📂 找到目标文件: {target_excel_file}")
    try:
        possible_id_cols = ['素材ID', '素材id', 'material_id', '视频ID']
        converters = {col: str for col in possible_id_cols}
        df = pd.read_excel(target_excel_file, engine='openpyxl', thousands=',', converters=converters)
        print("  - 文件读取并解析成功。")
    except Exception as e:
        print(f"  - ❌ 读取Excel文件时出错: {e}")
        input("请按回车键退出...")
        return False

    # 筛选高消耗数据
    cost_column = find_cost_column(df)
    if not cost_column:
        print(f"  - ❌ 在文件中找不到可识别的消耗列。")
        input("请按回车键退出...")
        return False
        
    df[cost_column] = pd.to_numeric(df[cost_column], errors='coerce')
    high_cost_materials = df.dropna(subset=[cost_column])
    high_cost_materials = high_cost_materials[high_cost_materials[cost_column] > cost_threshold].copy()

    if high_cost_materials.empty:
        print(f"  - ✅ 没有找到消耗高于 {cost_threshold} 的素材。")
        input("请按回车键退出...")
        return False

    print(f"  - ✅ 找到 {len(high_cost_materials)} 条高消耗素材")
    
    # 提取并保存素材ID
    material_ids = []
    for index, row in high_cost_materials.iterrows():
        material_id = str(row.get('素材ID', ''))
        if material_id and material_id != 'nan':
            material_ids.append(material_id)
    
    if not material_ids:
        print("  - ⚠️ 没有找到有效的素材ID")
        input("请按回车键退出...")
        return False
        
    json_file_path = save_material_ids_to_json(material_ids)
    if not json_file_path:
        print("  - ❌ 保存素材ID文件失败")
        input("请按回车键退出...")
        return False

    # 步骤3: 浏览器自动化下载视频和截图
    print("\n🌐 步骤 3/4: 浏览器自动化下载视频和截图...")
    print("⚠️ 注意: 此步骤需要手动操作浏览器，请按照脚本提示进行操作")
    
    try:
        run_browser_automation(material_ids)
        print("✅ 浏览器自动化完成")
    except Exception as e:
        print(f"❌ 浏览器自动化失败: {e}")
        print("⚠️ 继续执行飞书上传...")
    
    # 等待文件系统同步
    print("\n⏳ 等待3秒，确保文件系统同步...")
    time.sleep(3)

    # 步骤4: 上传到飞书
    print("\n📤 步骤 4/4: 上传完整数据到飞书表格...")
    feishu_client = lark.Client.builder() \
        .app_id(feishu_config["app_id"]) \
        .app_secret(feishu_config["app_secret"]) \
        .log_level(lark.LogLevel.WARNING) \
        .build()

    # 表格结构自检
    if not check_feishu_table_fields(feishu_client, feishu_config):
        input("\n请根据上面的提示检查并修正飞书表格中的列名，然后重新运行脚本。按回车键退出...")
        return False

    print("\n开始上传数据...")
    success_count = 0
    fail_count = 0

    for index, row in high_cost_materials.iterrows():
        material_id = str(row.get('素材ID', ''))
        # 尝试多个可能的素材名称列名
        material_name = str(row.get('素材名称', row.get('全域素材视频名称', '未知素材')))
        print(f"  - 正在上传: '{material_name[:50]}'...")

        # 处理消耗字段
        cost_value = None
        raw_cost = row.get(cost_column)
        if raw_cost is not None and pd.notna(raw_cost):
            try:
                cost_value = float(raw_cost)
            except (ValueError, TypeError):
                pass

        # 处理创建日期字段
        date_value = None
        raw_date = row.get('素材创建时间')
        if raw_date is not None and pd.notna(raw_date):
            if isinstance(raw_date, pd.Timestamp):
                date_value = raw_date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                date_value = str(raw_date)

        # 上传附件
        print(f"  - 正在处理素材附件...")
        attachments = upload_material_attachments(feishu_client, material_id, material_name, feishu_config["base_app_token"])

        # 构建数据包
        final_record_raw = {
            "素材ID": material_id,
            "素材名称": material_name,
            "消耗": cost_value,
            "创建日期": date_value,
            "评审": "等待AI生成建议...",
            "整体支付ROI": safe_convert_to_float(row.get('整体支付ROI')),
            "整体成交金额": safe_convert_to_float(row.get('整体成交金额')),
            "整体转化率": safe_convert_to_float(row.get('整体转化率')),
            "整体点击率": safe_convert_to_float(row.get('整体点击率')),
            "基础消耗": safe_convert_to_float(row.get('基础消耗')),
            "平均观看时长": convert_duration_to_seconds(row.get('平均观看时长')),
            "3秒播放率": safe_convert_to_float(row.get('3秒播放率')),
            "视频完播率": safe_convert_to_float(row.get('视频完播率')),
            "追投调控消耗": safe_convert_to_float(row.get('追投调控消耗')),
            "追投调控成交金额": safe_convert_to_float(row.get('追投调控成交金额')),
            "追投调控支付ROI": safe_convert_to_float(row.get('追投调控支付ROI')),
            "追投调控转化率": safe_convert_to_float(row.get('追投调控转化率')),
            "图片内容": attachments['图片内容'] if attachments['图片内容'] else None,
            "视频内容": attachments['视频内容'] if attachments['视频内容'] else None
        }

        # 清理NaN值
        final_record = {}
        for k, v in final_record_raw.items():
            if k in ['图片内容', '视频内容']:
                final_record[k] = v
            else:
                final_record[k] = v if pd.notna(v) else None

        # 上传数据
        if write_to_feishu_bitable(feishu_client, feishu_config, final_record):
            success_count += 1
        else:
            fail_count += 1

    # 完成总结
    print("\n" + "="*80)
    print(" 🎉 集成处理流程执行完成！")
    print("="*80)
    print(f" 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n📋 执行摘要:")
    print(f"   ✅ 筛选出高消耗素材: {len(high_cost_materials)} 条")
    print(f"   ✅ 生成素材ID文件: {json_file_path}")
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