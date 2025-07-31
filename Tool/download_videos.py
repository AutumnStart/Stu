import os
import re
import time
import requests
from urllib.parse import unquote
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("video_download.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("video_downloader")

def download_video(page, output_dir):
    """
    从页面中提取视频标题和视频源URL，然后下载视频
    
    Args:
        page: Playwright页面对象
        output_dir: 视频保存目录
    
    Returns:
        dict: 包含下载结果信息的字典
    """
    try:
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"确保输出目录存在: {output_dir}")
        
        # 1. 提取视频标题
        try:
            logger.info("尝试提取视频标题...")
            title_selector = "div[data-v-6d152e40].title.ellipsis-text-2"
            
            # 尝试直接使用选择器，设置较短的超时时间
            title_element = page.locator(title_selector).first
            video_title = title_element.inner_text(timeout=15000)  # 15秒超时
            logger.info(f"成功提取到视频标题: {video_title}")
            
        except Exception as e:
            logger.error(f"使用选择器提取标题失败: {e}")
            # 使用默认标题
            import datetime
            video_title = f"video_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            logger.info(f"使用默认标题: {video_title}")
            
        
        # 2. 提取视频源URL
        try:
            logger.info("尝试提取视频源URL...")
            
            # 先点击视频缩略图容器
            try:
                logger.info("尝试点击视频缩略图...")
                page.locator("div.oc-media-thumb-container").first.click(timeout=10000)
                logger.info("成功点击视频缩略图")
                # 等待视频加载
                time.sleep(2)
            except Exception as thumb_e:
                logger.error(f"点击视频缩略图失败: {thumb_e}")
                # 尝试使用JavaScript点击
                try:
                    js_click = '''
                    (function() {
                        const thumbContainer = document.querySelector("div.oc-media-thumb-container");
                        if (thumbContainer) {
                            thumbContainer.click();
                            return true;
                        }
                        return false;
                    })();
                    '''
                    page.evaluate(js_click)
                    logger.info("使用JavaScript点击视频缩略图")
                    time.sleep(2)
                except Exception as js_e:
                    logger.error(f"使用JavaScript点击视频缩略图也失败: {js_e}")
            
            # 尝试直接使用选择器提取视频元素，设置超时
            video_element = page.locator("video").first
            video_src = video_element.get_attribute("src", timeout=15000)  # 15秒超时
            
            if not video_src:
                # 尝试获取data-src属性
                video_src = video_element.get_attribute("data-src", timeout=15000)
            
            if video_src:
                logger.info(f"成功提取到视频源URL: {video_src}")
            else:
                logger.warning("未能提取到视频源URL")
                raise Exception("视频源URL为空")
            
        except Exception as e:
            logger.error(f"使用选择器提取视频源URL失败: {e}")
            video_src = None
        
        # 3. 清理标题，移除非法字符
        clean_title = re.sub(r'[\\/*?:"<>|]', '_', video_title)
        clean_title = clean_title.strip()
        
        if not clean_title:
            # 如果清理后标题为空，使用时间戳
            import datetime
            clean_title = f"video_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 4. 构建保存路径
        video_path = os.path.join(output_dir, f"{clean_title}.mp4")
        
        # 检查文件是否已存在
        if os.path.exists(video_path):
            logger.info(f"视频已存在，跳过下载: {video_path}")
            return {
                "success": True, 
                "video_path": video_path, 
                "title": clean_title,
                "skipped": True
            }
        
        # 5. 下载视频
        logger.info(f"开始下载视频: {video_src}")
        logger.info(f"保存到: {video_path}")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": page.url
        }
        
        response = requests.get(video_src, headers=headers, stream=True)
        response.raise_for_status()
        
        # 获取文件大小
        total_size = int(response.headers.get('content-length', 0))
        logger.info(f"视频大小: {total_size / (1024 * 1024):.2f} MB")
        
        # 下载文件，显示进度
        downloaded_size = 0
        with open(video_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    # 每下载10%显示一次进度
                    if total_size > 0 and downloaded_size % (total_size // 10) < 8192:
                        progress = (downloaded_size / total_size) * 100
                        logger.info(f"下载进度: {progress:.2f}%")
        
        logger.info(f"视频下载完成: {video_path}")
        
        return {
            "success": True,
            "video_path": video_path,
            "title": clean_title,
            "size": total_size
        }
        
    except Exception as e:
        logger.error(f"下载视频时发生错误: {e}")
        return {"success": False, "error": str(e)}

def get_root_dir():
    """
    获取项目根目录
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = script_dir
    while not os.path.exists(os.path.join(root_dir, 'storage')) and os.path.dirname(root_dir) != root_dir:
        root_dir = os.path.dirname(root_dir)
    if not os.path.exists(os.path.join(root_dir, 'storage')):
        root_dir = os.path.abspath(os.path.join(script_dir, '..', '..'))
    return root_dir

def main():
    """
    测试函数
    """
    print("这是一个视频下载模块，需要从capture_click_chart.py调用")
    print("无法直接运行")

if __name__ == "__main__":
    main()