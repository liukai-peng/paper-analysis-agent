import streamlit as st
import time
from typing import Callable, Any
from app.utils.log_util import logger

class UIHelper:
    """UI辅助类，提供常用的UI组件和动画效果"""
    
    @staticmethod
    def show_progress_bar(operations: list[str], callback: Callable[[str], Any]) -> dict:
        """
        显示进度条并执行操作
        
        Args:
            operations: 操作列表
            callback: 回调函数，接收当前操作描述
        
        Returns:
            操作结果字典
        """
        results = {}
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, operation in enumerate(operations):
            status_text.text(f"正在执行: {operation}...")
            progress = (i + 1) / len(operations)
            progress_bar.progress(progress)
            
            try:
                result = callback(operation)
                results[operation] = result
                logger.info(f"操作完成: {operation}")
            except Exception as e:
                logger.error(f"操作失败: {operation}, 错误: {e}")
                results[operation] = {"error": str(e)}
            
            time.sleep(0.1)  # 小延迟，让进度条动画更流畅
        
        status_text.text("所有操作完成！")
        time.sleep(0.5)
        status_text.empty()
        progress_bar.empty()
        
        return results
    
    @staticmethod
    def show_loading_animation(message: str = "处理中...", duration: int = 2):
        """
        显示加载动画
        
        Args:
            message: 加载消息
            duration: 持续时间（秒）
        """
        with st.spinner(message):
            time.sleep(duration)
    
    @staticmethod
    def show_success_animation(message: str = "操作成功！"):
        """
        显示成功动画
        
        Args:
            message: 成功消息
        """
        st.success(f"✅ {message}")
        time.sleep(1)
    
    @staticmethod
    def show_error_animation(message: str = "操作失败！"):
        """
        显示错误动画
        
        Args:
            message: 错误消息
        """
        st.error(f"❌ {message}")
        time.sleep(1)
    
    @staticmethod
    def show_info_animation(message: str = "提示信息"):
        """
        显示信息动画
        
        Args:
            message: 信息消息
        """
        st.info(f"ℹ️ {message}")
        time.sleep(1)
    
    @staticmethod
    def create_step_indicator(steps: list[str], current_step: int):
        """
        创建步骤指示器
        
        Args:
            steps: 步骤列表
            current_step: 当前步骤索引
        """
        cols = st.columns(len(steps))
        for i, (col, step) in enumerate(zip(cols, steps)):
            if i == current_step:
                col.markdown(f"🔵 **{step}**")
            elif i < current_step:
                col.markdown(f"✅ {step}")
            else:
                col.markdown(f"⚪ {step}")
    
    @staticmethod
    def show_typing_effect(text: str, speed: float = 0.02):
        """
        显示打字效果
        
        Args:
            text: 要显示的文本
            speed: 打字速度（秒/字符）
        """
        placeholder = st.empty()
        displayed_text = ""
        
        for char in text:
            displayed_text += char
            placeholder.markdown(displayed_text)
            time.sleep(speed)
        
        return placeholder
    
    @staticmethod
    def create_collapsible_section(title: str, content: str, default_expanded: bool = False):
        """
        创建可折叠的章节
        
        Args:
            title: 章节标题
            content: 章节内容
            default_expanded: 默认是否展开
        """
        with st.expander(title, expanded=default_expanded):
            st.markdown(content)
    
    @staticmethod
    def show_metrics(metrics: dict[str, Any]):
        """
        显示指标卡片
        
        Args:
            metrics: 指标字典
        """
        cols = st.columns(len(metrics))
        for col, (key, value) in zip(cols, metrics.items()):
            col.metric(key, value)
    
    @staticmethod
    def create_status_badge(status: str, message: str):
        """
        创建状态徽章
        
        Args:
            status: 状态（success, error, warning, info）
            message: 消息内容
        """
        if status == "success":
            st.success(f"✅ {message}")
        elif status == "error":
            st.error(f"❌ {message}")
        elif status == "warning":
            st.warning(f"⚠️ {message}")
        elif status == "info":
            st.info(f"ℹ️ {message}")
        else:
            st.markdown(f"🔹 {message}")
    
    @staticmethod
    def show_file_upload_status(filename: str, file_size: int, status: str = "success"):
        """
        显示文件上传状态
        
        Args:
            filename: 文件名
            file_size: 文件大小（字节）
            status: 状态
        """
        size_mb = file_size / (1024 * 1024)
        UIHelper.create_status_badge(status, f"文件 {filename} ({size_mb:.2f} MB) 上传成功")
    
    @staticmethod
    def create_download_button(filename: str, content: str, button_text: str = "下载"):
        """
        创建下载按钮
        
        Args:
            filename: 文件名
            content: 文件内容
            button_text: 按钮文本
        """
        st.download_button(
            label=button_text,
            data=content,
            file_name=filename,
            mime="text/plain"
        )

# 全局UI辅助实例
ui_helper = UIHelper()