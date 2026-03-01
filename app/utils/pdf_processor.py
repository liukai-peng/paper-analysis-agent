import fitz
from typing import List, Optional
import traceback
from app.utils.log_util import logger

class PDFProcessor:
    """PDF处理器 - 完全同步版本"""
    
    def __init__(self, chunk_size: int = 1000):
        self.chunk_size = chunk_size
    
    def extract_text(self, pdf_bytes: bytes, max_pages: Optional[int] = None) -> str:
        """
        提取PDF文本 - 完全同步
        """
        doc = None
        try:
            logger.info(f"开始提取PDF文本，数据大小: {len(pdf_bytes)} bytes")
            
            # 直接打开PDF，不使用任何异步
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            full_text = []
            
            total_pages = len(doc)
            pages_to_process = min(total_pages, max_pages) if max_pages else total_pages
            
            logger.info(f"PDF共 {total_pages} 页，将处理 {pages_to_process} 页")
            
            for page_num in range(pages_to_process):
                try:
                    page = doc[page_num]
                    text = page.get_text()
                    full_text.append(text)
                except Exception as page_error:
                    logger.error(f"处理第 {page_num + 1} 页时出错: {page_error}")
                    full_text.append(f"[第{page_num + 1}页处理失败]")
            
            result = "\n".join(full_text)
            logger.info(f"PDF文本提取完成，共 {len(result)} 字符")
            return result
            
        except Exception as e:
            error_detail = traceback.format_exc()
            logger.error(f"提取PDF文本失败: {e}\n{error_detail}")
            raise Exception(f"PDF解析失败: {str(e)}")
        finally:
            # 确保关闭文档
            if doc:
                try:
                    doc.close()
                except:
                    pass
    
    def get_pdf_info(self, pdf_bytes: bytes) -> dict:
        """
        获取PDF基本信息 - 完全同步
        """
        doc = None
        try:
            logger.info(f"获取PDF信息，数据大小: {len(pdf_bytes)} bytes")
            
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            info = {
                "page_count": len(doc),
                "metadata": doc.metadata,
                "file_size": len(pdf_bytes)
            }
            
            logger.info(f"PDF信息: {info['page_count']} 页, {info['file_size']} bytes")
            return info
            
        except Exception as e:
            error_detail = traceback.format_exc()
            logger.error(f"获取PDF信息失败: {e}\n{error_detail}")
            raise Exception(f"无法读取PDF信息: {str(e)}")
        finally:
            if doc:
                try:
                    doc.close()
                except:
                    pass

# 全局PDF处理器实例
pdf_processor = PDFProcessor()
