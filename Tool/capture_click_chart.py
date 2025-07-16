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
            # 备用方案：使用JavaScript进行输入
            try:
                js_search = f'''
                (function() {{
                    // 尝试找到搜索框并输入
                    const searchInput = Array.from(document.querySelectorAll('input')).find(
                        el => el.placeholder && el.placeholder.includes('输入素材名称或ID')
                    );
                    if (searchInput) {{
                        searchInput.value = '{material_id}';
                        searchInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        searchInput.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true }}));
                        return true;
                    }}
                    return false;
                }})();
                '''
                page.evaluate(js_search)
                print(f"使用JavaScript搜索素材ID: {material_id}")
                time.sleep(3)
            except Exception as e2:
                print(f"JavaScript搜索也失败: {e2}")
                return False
        
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
            # 尝试使用其他方式定位分析按钮
            try:
                page.locator("span").filter(has_text="分析").first.click()
                print("使用备用方式点击分析按钮")
                time.sleep(5)
            except Exception as e2:
                print(f"备用方式点击分析按钮也失败: {e2}")
                # 尝试使用JavaScript点击
                try:
                    js_click_analyze = '''
                    (function() {
                        // 尝试找到包含"分析"文本的按钮
                        const buttons = Array.from(document.querySelectorAll('span, button, div'));
                        const analyzeBtn = buttons.find(el => el.innerText && el.innerText.includes('分析'));
                        if (analyzeBtn) {
                            analyzeBtn.click();
                            return true;
                        }
                        return false;
                    })();
                    '''
                    page.evaluate(js_click_analyze)
                    print("使用JavaScript点击分析按钮")
                    time.sleep(5)
                except Exception as e3:
                    print(f"所有点击分析按钮方式都失败: {e3}")
                    return False
        
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
            capture_population_chart(page, output_dir, f"八大人群分布人数_{timestamp}")
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
                
                # 备用方案2: 使用 Escape 键
                try:
                    page.keyboard.press("Escape")
                    print("使用Escape键尝试关闭分析模块")
                    time.sleep(3)
                except Exception as e3:
                    print(f"使用Escape键关闭失败: {e3}")
                    
                    # 备用方案3: 使用JavaScript关闭
                    try:
                        js_close = '''
                        (function() {
                            // 尝试找到关闭按钮
                            const closeBtn = document.querySelector('.oc-drawer-close');
                            if (closeBtn) {
                                closeBtn.click();
                                return '找到并点击了.oc-drawer-close';
                            }
                            
                            // 尝试通过类名查找可能的关闭按钮
                            const possibleCloseButtons = Array.from(
                                document.querySelectorAll('[class*=close], [class*=cancel], button, span, i')
                            ).filter(el => {
                                const classes = el.getAttribute('class') || '';
                                return classes.includes('close') || classes.includes('cancel');
                            });
                            
                            if (possibleCloseButtons.length > 0) {
                                possibleCloseButtons[0].click();
                                return '找到并点击了备用关闭按钮';
                            }
                            
                            // 如果找不到按钮，尝试查找带有关闭或取消文本的元素
                            const textButtons = Array.from(document.querySelectorAll('*')).filter(el => {
                                const text = el.innerText || '';
                                return text.includes('关闭') || text.includes('取消') || text.includes('返回');
                            });
                            
                            if (textButtons.length > 0) {
                                textButtons[0].click();
                                return '找到并点击了带有关闭文本的元素';
                            }
                            
                            return '未找到任何可以关闭的元素';
                        })();
                        '''
                        result = page.evaluate(js_close)
                        print(f"使用JavaScript尝试关闭分析模块: {result}")
                        time.sleep(3)
                    except Exception as e4:
                        print(f"使用JavaScript关闭失败: {e4}")
                        print("警告: 所有关闭分析模块的方法都失败，可能会影响下一个素材ID的处理")
            
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
            
            # 备用方案1: 使用data-e2e属性定位
            try:
                data_selector = "div[data-e2e='oc_emptyKey_dataV2/bidding/site-promotion_video_lose_count_for_roi2']"
                page.locator(data_selector).click(timeout=5000)
                print("使用data-e2e属性成功点击'整体流失数'选项卡")
            except Exception as e2:
                print(f"使用data-e2e属性点击失败: {e2}")
                
                # 备用方案2: 直接使用文本内容定位
                try:
                    # 使用提供的playwright代码
                    page.get_by_text("整体流失数").click(timeout=5000)
                    print("使用文本内容成功点击'整体流失数'选项卡")
                except Exception as e3:
                    print(f"使用文本内容点击失败: {e3}")
                    
                    # 备用方案3: 使用JavaScript
                    try:
                        js_click = '''
                        (function() {
                            // 尝试通过data-e2e属性找到元素
                            let lossBtn = document.querySelector("div[data-e2e='oc_emptyKey_dataV2/bidding/site-promotion_video_lose_count_for_roi2']");
                            
                            // 如果找不到，尝试通过文本内容找到元素
                            if (!lossBtn) {
                                const elements = Array.from(document.querySelectorAll('div'));
                                lossBtn = elements.find(el => el.innerText && 
                                             el.innerText.trim() === '整体流失数');
                            }
                            
                            if (lossBtn) {
                                lossBtn.click();
                                return true;
                            }
                            return false;
                        })();
                        '''
                        page.evaluate(js_click)
                        print("使用JavaScript成功点击'整体流失数'选项卡")
                    except Exception as e4:
                        print(f"使用JavaScript点击失败: {e4}")
        
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
            
            # 方法2: 尝试截取任何canvas元素
            try:
                canvas_simple = page.locator("canvas").first
                canvas_simple.screenshot(path=screenshot_path)
                print(f"成功截取整体流失数canvas: {screenshot_path}")
                return screenshot_path
            except Exception as e2:
                print(f"截取简单canvas失败: {e2}")
                
                # 方法3: 截取整个图表区域
                try:
                    chart_area = page.locator("div.trend-chart").first
                    chart_area.screenshot(path=screenshot_path)
                    print(f"成功截取整体流失数图表区域: {screenshot_path}")
                    return screenshot_path
                except Exception as e3:
                    print(f"截取图表区域失败: {e3}")
                    
                    # 最后方案: 截取整个页面
                    try:
                        page.screenshot(path=screenshot_path)
                        print(f"已截取整个页面: {screenshot_path}")
                        return screenshot_path
                    except Exception as e4:
                        print(f"截取整个页面失败: {e4}")
                        return None
    except Exception as e:
        print(f"截取整体流失数图表时出错: {e}")
        return None

# 提取通用的图表截图逻辑到单独的函数
def capture_chart(page, chart_name, screenshots_dir, file_prefix, click_position={"x": 19, "y": 293}):
    print(f"\\n===== 开始截取{chart_name}图表 =====")
    
    # 尝试点击对应的选项卡
    try:
        print(f"尝试点击{chart_name}选项卡...")
        
        # 方法1: 精确文本匹配
        try:
            # 先尝试使用索引定位
            page.get_by_text(chart_name).nth(1).click(timeout=5000)
            print(f"使用索引方式成功点击{chart_name}选项卡")
        except Exception as e1:
            print(f"使用索引方式点击{chart_name}选项卡失败: {e1}")
            
            # 方法2: 使用选择器组合定位
            try:
                selector = f"div.ovui-radio-item:has-text('{chart_name}'), div[class*='radio']:has-text('{chart_name}')"
                page.locator(selector).first.click(timeout=5000)
                print(f"使用选择器组合成功点击{chart_name}选项卡")
            except Exception as e2:
                print(f"使用选择器组合点击{chart_name}选项卡失败: {e2}")
                
                # 方法3: 使用JavaScript
                try:
                    js_click = f'''
                    (function() {{
                        // 尝试找到并点击匹配的元素
                        const elements = Array.from(document.querySelectorAll('div'));
                        const target = elements.find(el => el.innerText && el.innerText.includes('{chart_name}') && 
                            (el.getAttribute('class') && 
                            (el.getAttribute('class').includes('item') || 
                             el.getAttribute('class').includes('radio') || 
                             el.getAttribute('class').includes('tab'))));
                        
                        if (target) {{
                            target.click();
                            return true;
                        }}
                        return false;
                    }})();
                    '''
                    page.evaluate(js_click)
                    print(f"使用JavaScript成功点击{chart_name}选项卡")
                except Exception as e3:
                    print(f"使用JavaScript点击{chart_name}选项卡失败: {e3}")
    except Exception as e:
        print(f"所有点击{chart_name}选项卡方式都失败: {e}")
    
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
    try:
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
            
            # 方法2: 尝试截取可能包含图表的区域
            try:
                area_selectors = [
                    "div.trend-chart", 
                    "div.chart", 
                    "div.lightcharts-container",
                    "div.content-analyze",
                    "div[class*='chart']",
                    "div[class*='图表']"
                ]
                
                for selector in area_selectors:
                    try:
                        area_path = os.path.join(screenshots_dir, f"{file_prefix}_区域.png")
                        area = page.locator(selector).first
                        if area:
                            area.screenshot(path=area_path)
                            print(f"成功截取{chart_name}图表区域，保存为: {area_path}")
                            return area_path
                    except Exception:
                        continue
                
                # 如果上述所有方法都失败，截取整个页面
                page_path = os.path.join(screenshots_dir, f"{file_prefix}_全页面.png")
                page.screenshot(path=page_path)
                print(f"所有区域截图方法失败，已截取整个页面，保存为: {page_path}")
                return page_path
            except Exception as e2:
                print(f"所有截图方法都失败: {e2}")
                return None
    except Exception as e:
        print(f"截取{chart_name}图表时发生异常: {e}")
        return None

# 添加专门用于八大人群分布人数图表截图的函数
def capture_population_chart(page, screenshots_dir, file_prefix):
    """专门为八大人群分布人数设计的截图函数"""
    print("\\n===== 开始截取八大人群分布人数图表 =====")
    
    try:
        # 尝试点击对应的选项卡
        try:
            print("尝试点击八大人群分布人数选项卡...")
            
            # 尝试多种方法找到并点击八大人群分布人数选项卡
            try:
                # 通过数据属性更精确地定位
                page.locator("div[data-e2e*='crowd_distribution'], div[data-e2e*='人群分布']").click(timeout=5000)
                print("通过数据属性成功点击八大人群分布人数选项卡")
            except Exception as e1:
                print(f"通过数据属性点击八大人群分布人数选项卡失败: {e1}")
                
                # 使用更广泛的文本匹配
                try:
                    page.locator("div").filter(has_text=re.compile(r".*人群分布.*")).first.click(timeout=5000)
                    print("通过模糊文本成功点击八大人群分布人数选项卡")
                except Exception as e3:
                    print(f"通过模糊文本点击失败: {e3}")
                    
                    # 最后使用JavaScript方法
                    try:
                        js_click = '''
                        (function() {
                            // 尝试找到包含"人群分布"或"八大人群"文本的元素
                            const elements = Array.from(document.querySelectorAll('div, span, button'));
                            const target = elements.find(el => 
                                el.innerText && (
                                    el.innerText.includes('人群分布') || 
                                    el.innerText.includes('八大人群') ||
                                    el.innerText.includes('分布人数')
                                )
                            );
                            
                            if (target) {
                                target.click();
                                return '找到并点击了人群分布相关元素';
                            }
                            return '未找到人群分布相关元素';
                        })();
                        '''
                        result = page.evaluate(js_click)
                        print(f"使用JavaScript点击八大人群分布人数选项卡: {result}")
                    except Exception as e4:
                        print(f"使用JavaScript点击失败: {e4}")
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
            
            # 方法2: 尝试截取整个图表区域
            try:
                # 查找可能包含图表的区域
                area_selectors = [
                    "div.distribution-chart", 
                    "div[class*='distribution']",
                    "div[class*='crowd']", 
                    "div.chart-container",
                    "div.chart-wrapper",
                    "div.content-analyze section",
                    "div.content-population"
                ]
                
                for selector in area_selectors:
                    try:
                        area = page.locator(selector).first
                        area_path = os.path.join(screenshots_dir, f"{file_prefix}_区域.png")
                        area.screenshot(path=area_path)
                        print(f"成功截取人群分布区域，保存为: {area_path}")
                        return area_path
                    except Exception:
                        continue
            except Exception as e2:
                print(f"截取图表区域失败: {e2}")
            
            # 方法3: 使用JS截取整个可视区域中的图表部分
            try:
                js_screenshot = '''
                (function() {
                    // 查找包含图表的区域
                    const chartContainers = Array.from(document.querySelectorAll(
                        'div[class*="chart"], div[class*="population"], div[class*="distribution"], section'
                    )).filter(el => {
                        const rect = el.getBoundingClientRect();
                        // 只选择视口中足够大的元素，很可能是图表容器
                        return rect.width > 400 && rect.height > 200 && 
                               rect.top >= 0 && rect.bottom <= window.innerHeight;
                    });
                    
                    if (chartContainers.length > 0) {
                        // 返回元素信息，供后续定位使用
                        return chartContainers.map(el => ({
                            tag: el.tagName,
                            id: el.id,
                            className: el.className,
                            text: el.innerText.substring(0, 50) + '...'
                        }));
                    }
                    return null;
                })();
                '''
                containers = page.evaluate(js_screenshot)
                print(f"找到可能的图表容器: {containers}")
                
                if containers and len(containers) > 0:
                    for container_info in containers: # Renamed to avoid conflict
                        try:
                            selector = ""
                            if container_info.get("id"):
                                selector = f"#{container_info['id']}"
                            elif container_info.get("className"):
                                class_name = container_info['className'].split(' ')[0]
                                selector = f".{class_name}"
                            else:
                                continue
                                
                            container_el = page.locator(selector).first
                            container_path = os.path.join(screenshots_dir, f"{file_prefix}_容器.png")
                            container_el.screenshot(path=container_path)
                            print(f"成功截取容器元素，保存为: {container_path}")
                            return container_path
                        except Exception:
                            continue
            except Exception as e3:
                print(f"使用JS查找图表容器失败: {e3}")
            
            # 最后方案：截取整个页面
            page_path = os.path.join(screenshots_dir, f"{file_prefix}_全页面.png")
            page.screenshot(path=page_path)
            print(f"所有方法都失败，已截取整个页面，保存为: {page_path}")
            return page_path
            
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
            print("处理可能的弹窗...")
            handle_popups(page1)

            # 导航到数据分析页面
            page1.get_by_role("button", name="数据").click()
            page1.locator("a").filter(has_text="全域数据").click()
            time.sleep(3)
            
            # 处理点击全域数据后可能出现的弹窗
            handle_popups(page1)
            
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
