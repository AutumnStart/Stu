import re
import os
import time
import json
import shutil
from datetime import datetime
from playwright.sync_api import Playwright, sync_playwright, expect

import download_videos

def handle_popups(page):
    """处理页面上的各种弹窗"""
    try:
        # 1. 尝试关闭'我知道了'弹窗
        try:
            selector = "body > div:nth-child(49) > div > div.c-lib-guide-mask > div > div.c-lib-guide-body > div.c-lib-guide-bottom > div"
            page.wait_for_selector(selector, timeout=10000, state="visible")
            page.locator(selector).click()
            print("成功关闭'我知道了'弹窗")
        except Exception as e:
            print(f"关闭'我知道了'弹窗失败: {e}")
        
        # 2. 尝试点击'跳过'按钮
        try:
            skip_button = page.locator("button.firefly-modal-multi-step-skip").first
            skip_button.click(timeout=10000)
            print("成功点击'跳过'按钮")
        except Exception as e:
            print(f"点击'跳过'按钮失败: {e}")
        
        return True
    except Exception as e:
        print(f"处理弹窗过程中发生错误: {e}")
        return False

def search_and_capture_material(page, material_id, output_dir):
    """
    按照正确的流程处理素材:
    1. 先搜索素材ID
    2. 下载视频
    3. 点击内容分析模块
    4. 截取图表
    5. 关闭分析模块
    """
    try:
        # 1. 搜索素材ID
        print(f"开始搜索素材ID: {material_id}")
        try:
            # 首先尝试点击搜索框
            search_box = page.get_by_role("textbox", name="输入素材名称或ID")
            search_box.click()
            # 清空搜索框
            search_box.fill("")
            # 输入素材ID
            search_box.fill(material_id)
            # 按回车搜索
            search_box.press("Enter")
            print(f"已搜索素材ID: {material_id}")
            
            # 等待搜索结果加载
            time.sleep(3)
        except Exception as e:
            print(f"搜索素材ID失败: {e}")

        
        # 1.5 下载视频
        try:
            print("\n===== 开始下载视频 =====")
            # 获取项目根目录
            root_dir = download_videos.get_root_dir()
            # 设置视频保存目录
            video_save_dir = os.path.join(root_dir, 'storage', 'video', '留香珠')
            # 下载视频
            download_result = download_videos.download_video(page, video_save_dir)
            
            if download_result["success"]:
                if download_result.get("skipped", False):
                    print(f"视频已存在，跳过下载: {download_result['video_path']}")
                else:
                    print(f"视频下载成功: {download_result['video_path']}")
            else:
                print(f"视频下载失败: {download_result.get('error', '未知错误')}")
        except Exception as e:
            print(f"下载视频过程中发生错误: {e}")
            # 继续执行，不因视频下载失败而中断整个流程
        
        # 2. 点击分析按钮（内容分析模块）
        try:
            print("点击分析按钮进入内容分析模块...")
            page.locator("div:nth-child(2) > span > .analyse").first.click()
            print("成功点击分析按钮")
            # 等待页面加载
            time.sleep(5)
        except Exception as e:
            print(f"点击分析按钮失败: {e}")
        
        # 3. 获取当前时间作为文件名基础
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 4. 截取各种图表
        # 4.1 截取整体点击次数曲线图
        print(f"开始为素材ID: {material_id} 截取图表")
        click_chart_path = capture_chart(page, "整体点击次数", output_dir, f"整体点击次数_{timestamp}")
        
        # 4.2 截取整体流失数曲线图 - 使用精确选择器
        loss_chart_path = capture_loss_chart(page, output_dir, f"整体流失数_{timestamp}")
        
        # 复制图片到BYDHG目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = script_dir
        while not os.path.exists(os.path.join(root_dir, 'storage')) and os.path.dirname(root_dir) != root_dir:
            root_dir = os.path.dirname(root_dir)
        if not os.path.exists(os.path.join(root_dir, 'storage')):
            root_dir = os.path.abspath(os.path.join(script_dir, '..', '..'))
        
        bydhg_dir = os.path.join(root_dir, 'storage', 'image', 'BYDHG')
        bydhg_material_dir = os.path.join(bydhg_dir, f"Material_{material_id}")
        
        # 确保目标目录存在
        os.makedirs(bydhg_material_dir, exist_ok=True)
        
        # 复制整体点击次数图表
        if click_chart_path and os.path.exists(click_chart_path):
            click_chart_filename = os.path.basename(click_chart_path)
            bydhg_click_path = os.path.join(bydhg_material_dir, click_chart_filename)
            shutil.copy2(click_chart_path, bydhg_click_path)
            print(f"已复制整体点击次数图表到BYDHG: {bydhg_click_path}")
        
        # 复制整体流失数图表
        if loss_chart_path and os.path.exists(loss_chart_path):
            loss_chart_filename = os.path.basename(loss_chart_path)
            bydhg_loss_path = os.path.join(bydhg_material_dir, loss_chart_filename)
            shutil.copy2(loss_chart_path, bydhg_loss_path)
            print(f"已复制整体流失数图表到BYDHG: {bydhg_loss_path}")
        
        # 4.3 截取八大人群分布人数图表
        # 先切换到人群分析
        try:
            print("\\n===== 切换到人群分析 =====")
            page.locator("div").filter(has_text=re.compile(r"^人群分析$")).first.click()
            print("成功点击人群分析选项卡")
            time.sleep(3)  # 等待页面切换
            # 截取八大人群分布人数图表
            capture_population_chart(page, output_dir, f"八大人群分布人数整体展现次数_{timestamp}")
            # 精确查找 class 为 'ovui-input__prefix' 且包含文本 '展示指标：' 的 div
            page.locator("div.ovui-input__prefix:has-text('展示指标：')").click()
            page.locator("div.ovui-cascader-panel__item-label:has-text('整体成交金额')").click()
            print(1)
            time.sleep(5)  # 等待页面切换
            
            capture_population_chart(page, output_dir, f"八大人群分布人数整体成交金额_{timestamp}")
            page.locator("div.ovui-input__prefix:has-text('展示指标：')").click()
            page.locator("div.ovui-cascader-panel__item-label:has-text('整体点击次数')").click()
            print(2)
            time.sleep(5)  # 等待页面切换
            capture_population_chart(page, output_dir, f"八大人群分布人数整体点击次数_{timestamp}")
        except Exception as e:
            print(f"切换到人群分析失败: {e}")
            
        # 5. 重要：关闭分析模块
        try:
            print("\\n===== 关闭分析模块 =====")
            page.locator(".oc-drawer-close").click()
            print("成功关闭分析模块")
            # 等待页面恢复到初始状态
            time.sleep(3)
        except Exception as e:
            print(f"使用locator关闭分析模块失败: {e}")
            
            # 备用方案1: 使用其他CSS选择器
            try:
                page.locator("div.oc-drawer-close, span.oc-drawer-close, i.oc-drawer-close").click(timeout=5000)
                print("使用备用CSS选择器成功关闭分析模块")
                time.sleep(3)
            except Exception as e2:
                print(f"使用备用CSS选择器关闭失败: {e2}")
                    
        print(f"已完成素材ID: {material_id} 的所有图表截取")
        return True
    except Exception as e:
        print(f"处理素材ID时出错: {e}")
        return False 
    

# 专门为整体流失数设计的截图函数，使用精确的前端选择器
def capture_loss_chart(page, screenshots_dir, file_prefix):
    print("\\n===== 开始截取整体流失数图表 =====")
    try:
        # 使用精确选择器点击整体流失数选项卡
        # 从前端代码中提取的选择器
        loss_selector = "div.ovui-radio-item[data-e2e='oc_emptyKey_dataV2/bidding/site-promotion_video_lose_count_for_roi2']"
        
        print("尝试使用精确选择器点击'整体流失数'选项卡...")
        
        try:
            # 使用精确选择器
            page.locator(loss_selector).click(timeout=5000)
            print("使用精确选择器成功点击'整体流失数'选项卡")
        except Exception as e:
            print(f"使用精确选择器点击失败: {e}")
            
        # 等待图表加载
        time.sleep(3)
        
        # 截取图表
        screenshot_path = os.path.join(screenshots_dir, f"{file_prefix}.png")
        
        # 方法1: 尝试截取canvas元素
        try:
            # 从前端代码中提取的canvas选择器
            canvas = page.locator("canvas[width='826'][height='320']")
            canvas.screenshot(path=screenshot_path)
            print(f"成功截取整体流失数曲线图: {screenshot_path}")
            return screenshot_path
        except Exception as e:
            print(f"截取canvas元素失败: {e}")
            
    except Exception as e:
        print(f"截取整体流失数图表时出错: {e}")
        return None

# 提取通用的图表截图逻辑到单独的函数
def capture_chart(page, chart_name, screenshots_dir, file_prefix, click_position={"x": 19, "y": 293}):
    print(f"\\n===== 开始截取{chart_name}图表 =====")
    
    print(f"尝试点击{chart_name}选项卡...")
    # 方法1: 精确文本匹配
    try:
        # 先尝试使用索引定位
        page.get_by_text(chart_name).nth(1).click(timeout=5000)
        print(f"使用索引方式成功点击{chart_name}选项卡")
    except Exception as e1:
        print(f"使用索引方式点击{chart_name}选项卡失败: {e1}")
            
    # 等待图表加载
    time.sleep(3)
    
    # 点击曲线图上的特定位置进行交互
    try:
        print(f"尝试点击{chart_name}图表上的特定位置...")
        
        # 首先尝试使用canvas元素
        try:
            page.locator("canvas").click(position=click_position)
            print(f"成功点击{chart_name}图表")
        except Exception as e:
            print(f"点击{chart_name}图表失败: {e}")
    except Exception as e:
        print(f"所有点击{chart_name}图表的方式都失败: {e}")
    
    # 等待图表交互响应
    time.sleep(3)
    
    # 截取图表
    print(f"尝试截取{chart_name}图表...")
    
    # 方法1: 尝试截取canvas元素
    try:
        # 尝试找到可能是图表的canvas元素
        chart_path = os.path.join(screenshots_dir, f"{file_prefix}.png")
        canvas = page.locator("canvas").first
        canvas.screenshot(path=chart_path)
        print(f"成功截取{chart_name}图表，保存为: {chart_path}")
        return chart_path
    except Exception as e:
        print(f"截取canvas元素失败: {e}")
            


# 添加专门用于八大人群分布人数图表截图的函数
def capture_population_chart(page, screenshots_dir, file_prefix):
    """专门为八大人群分布人数设计的截图函数"""
    print("\\n===== 开始截取八大人群分布人数图表 =====")
    
    try:
        # 尝试点击对应的选项卡
        try:
            print("尝试点击八大人群分布人数选项卡...")
            # 使用更广泛的文本匹配
            try:
                page.locator("div").filter(has_text=re.compile(r".*人群分布.*")).first.click(timeout=5000)
                print("通过模糊文本成功点击八大人群分布人数选项卡")
            except Exception as e3:
                print(f"通过模糊文本点击失败: {e3}")
                    
        except Exception as e:
            print(f"所有点击八大人群分布人数选项卡的方式都失败: {e}")
        
        # 等待图表加载
        time.sleep(3)
        
        # 截取图表 - 优化处理多个canvas的情况
        screenshot_path = os.path.join(screenshots_dir, f"{file_prefix}.png")
        
        try:
            print("尝试截取八大人群分布人数图表...")
            
            # 方法1: 尝试通过特定尺寸或特征定位正确的canvas
            try:
                # 查找最大的canvas元素，通常是主图表
                js_get_main_canvas = '''
                (function() {
                    const canvases = Array.from(document.querySelectorAll('canvas'));
                    if (canvases.length === 0) return null;
                    
                    // 按面积大小排序
                    canvases.sort((a, b) => {
                        const areaA = a.width * a.height;
                        const areaB = b.width * b.height;
                        return areaB - areaA; // 降序排列
                    });
                    
                    // 返回最大canvas的信息
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
                    # 使用JS获取到的信息精确定位
                    if canvas_info.get("id"):
                        main_canvas = page.locator(f"canvas#{canvas_info['id']}")
                    elif canvas_info.get("className"):
                        main_canvas = page.locator(f"canvas.{canvas_info['className'].split(' ')[0]}") # Use first class
                    else:
                        # 如果没有id或class，使用nth选择器
                        main_canvas = page.locator("canvas").nth(canvas_info["index"])
                    
                    main_canvas.screenshot(path=screenshot_path)
                    print(f"成功截取八大人群分布人数图表，保存为: {screenshot_path}")
                    return screenshot_path
            except Exception as e:
                print(f"通过特定特征定位canvas失败: {e}")
            
        except Exception as e:
            print(f"截取八大人群分布人数图表失败: {e}")
            return None
            
    except Exception as e:
        print(f"处理八大人群分布人数图表时出错: {e}")
        return None

def main():
    """
    主函数，用于读取素材ID，登录并批量处理。
    """
    # 确定JSON文件路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = script_dir
    while not os.path.exists(os.path.join(root_dir, 'storage')) and os.path.dirname(root_dir) != root_dir:
        root_dir = os.path.dirname(root_dir)
    if not os.path.exists(os.path.join(root_dir, 'storage')):
        root_dir = os.path.abspath(os.path.join(script_dir, '..', '..'))
        
    json_path = os.path.join(root_dir, 'data', '素材ID.json')
    
    if not os.path.exists(json_path):
        print(f"错误: JSON文件未找到 at {json_path}")
        return
    
    print(f"正在读取JSON文件: {json_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    material_ids = data.get("素材ID列表", [])
    
    if not material_ids:
        print("错误: JSON文件中未找到'素材ID列表'或列表为空。")
        return
        
    print(f"找到 {len(material_ids)} 个素材ID，准备开始批量处理...")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # 登录巨量引擎
            page.goto("https://business.oceanengine.com/login?appKey=80")
            page.get_by_text("邮箱登录").click()
            page.get_by_role("textbox", name="请输入邮箱").click()
            page.get_by_role("textbox", name="请输入邮箱").fill("tianqi.wang@gewuchuanmei.com")
            page.get_by_role("textbox", name="请输入邮箱").press("Tab")
            page.get_by_role("textbox", name="密码").fill("Soulink-88818")
            page.locator("use").nth(1).click()
            page.get_by_role("button", name="登录").click()
            
            # 等待登录成功
            page.wait_for_load_state("networkidle")
            print("登录成功!")
            
            # 打开智联页面
            with page.expect_popup() as page1_info:
                page.get_by_text("智联（卓尔01）-PWU-留香珠").click()
            page1 = page1_info.value
            
            # 处理弹窗
            # print("处理可能的弹窗...")
            # handle_popups(page1)

            # 导航到数据分析页面
            page1.get_by_role("button", name="数据").click()
            page1.locator("a").filter(has_text="全域数据").click()
            time.sleep(3)
            
            # # 处理点击全域数据后可能出现的弹窗
            # handle_popups(page1)
            
            page1.locator("div").filter(has_text=re.compile(r"^素材数据$")).nth(2).click()
            time.sleep(3)
            
            # 设置截图保存目录
            main_screenshot_dir = "screenshots"
            error_dir = os.path.join("screenshots", "errors")
            os.makedirs(main_screenshot_dir, exist_ok=True)
            os.makedirs(error_dir, exist_ok=True)
            print(f"确认主截图目录存在: {main_screenshot_dir}")

            # 批量处理素材ID
            for i, material_id in enumerate(material_ids):
                material_id_str = str(material_id)

                # 检查结果是否已存在于screenshots目录
                material_screenshot_dir = os.path.join(main_screenshot_dir, f"Material_{material_id_str}")
                
                # 如果目录存在且至少包含2个图表文件，则跳过
                if os.path.exists(material_screenshot_dir) and len([name for name in os.listdir(material_screenshot_dir) if name.endswith('.png')]) >= 2:
                    print(f"结果已存在，跳过素材ID: {material_id_str}")
                    continue

                print(f"\n{'='*20} 开始处理第 {i+1}/{len(material_ids)} 个素材: {material_id_str} {'='*20}")
                
                try:
                    # 创建该素材ID的截图目录
                    material_dir = os.path.join(main_screenshot_dir, f"Material_{material_id_str}")
                    os.makedirs(material_dir, exist_ok=True)
                    print(f"创建素材截图目录: {material_dir}")
                    
                    time.sleep(2)
                    
                    success = search_and_capture_material(page1, material_id_str, material_dir)
                    
                    if success:
                        print(f"成功处理素材ID {material_id_str} 并截取图表。截图保存在: {material_dir}")
                    else:
                        print(f"处理素材ID {material_id_str} 失败。")

                except Exception as e:
                    print(f"处理素材ID {material_id_str} 时出错: {e}")
                    # 保存错误页面截图
                    try:
                        error_path = os.path.join(material_dir, f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                        page1.screenshot(path=error_path)
                        print(f"已保存错误状态截图: {error_path}")
                    except Exception as err:
                        print(f"无法保存错误状态截图: {err}")
            
        except Exception as e:
            print(f"发生严重错误: {e}")
            try:
                error_dir = os.path.join("screenshots", "errors")
                os.makedirs(error_dir, exist_ok=True)
                error_path = os.path.join(error_dir, f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                page.screenshot(path=error_path)
                print(f"已保存错误状态截图: {error_path}")
            except Exception as err:
                print(f"无法保存错误状态截图: {err}")
        finally:
            context.close()
            browser.close()
            print("浏览器已关闭")
            print(f"\n{'='*20} 所有素材ID处理完毕 {'='*20}")

if __name__ == "__main__":
    main()
