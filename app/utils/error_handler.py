import time
import functools
from typing import Callable, TypeVar, Any
from app.utils.log_util import logger

T = TypeVar('T')

def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 延迟时间倍数
    
    Returns:
        装饰器函数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(f"函数 {func.__name__} 第 {attempt + 1}/{max_attempts} 次尝试失败: {e}")
                    
                    if attempt < max_attempts - 1:
                        logger.info(f"等待 {current_delay} 秒后重试...")
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
            
            logger.error(f"函数 {func.__name__} 在 {max_attempts} 次尝试后仍然失败")
            raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(f"函数 {func.__name__} 第 {attempt + 1}/{max_attempts} 次尝试失败: {e}")
                    
                    if attempt < max_attempts - 1:
                        logger.info(f"等待 {current_delay} 秒后重试...")
                        time.sleep(current_delay)
                        current_delay *= backoff
            
            logger.error(f"函数 {func.__name__} 在 {max_attempts} 次尝试后仍然失败")
            raise last_exception
        
        # 根据函数是否是协程函数返回对应的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def handle_errors(error_message: str = "操作失败"):
    """
    错误处理装饰器
    
    Args:
        error_message: 默认错误消息
    
    Returns:
        装饰器函数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return await func(*args, **kwargs)
            except FileNotFoundError as e:
                logger.error(f"文件未找到: {e}")
                raise FileNotFoundError(f"{error_message}: 文件未找到 - {e}")
            except PermissionError as e:
                logger.error(f"权限错误: {e}")
                raise PermissionError(f"{error_message}: 权限不足 - {e}")
            except ValueError as e:
                logger.error(f"值错误: {e}")
                raise ValueError(f"{error_message}: 数据格式错误 - {e}")
            except ConnectionError as e:
                logger.error(f"连接错误: {e}")
                raise ConnectionError(f"{error_message}: 网络连接失败 - {e}")
            except Exception as e:
                logger.error(f"未知错误: {e}")
                raise Exception(f"{error_message}: {e}")
        
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except FileNotFoundError as e:
                logger.error(f"文件未找到: {e}")
                raise FileNotFoundError(f"{error_message}: 文件未找到 - {e}")
            except PermissionError as e:
                logger.error(f"权限错误: {e}")
                raise PermissionError(f"{error_message}: 权限不足 - {e}")
            except ValueError as e:
                logger.error(f"值错误: {e}")
                raise ValueError(f"{error_message}: 数据格式错误 - {e}")
            except ConnectionError as e:
                logger.error(f"连接错误: {e}")
                raise ConnectionError(f"{error_message}: 网络连接失败 - {e}")
            except Exception as e:
                logger.error(f"未知错误: {e}")
                raise Exception(f"{error_message}: {e}")
        
        # 根据函数是否是协程函数返回对应的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

import asyncio