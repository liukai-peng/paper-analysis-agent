"""
测试PDF处理功能
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("🔍 PDF处理测试")
print("=" * 60)
print()

# 测试导入
try:
    print("1. 测试导入 pdf_processor...")
    from app.utils.pdf_processor import pdf_processor
    print("   ✅ 导入成功")
except Exception as e:
    print(f"   ❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试PDF文件路径
pdf_path = input("\n请输入PDF文件路径（或按回车跳过）: ").strip()

if pdf_path and os.path.exists(pdf_path):
    print(f"\n2. 测试解析PDF: {pdf_path}")
    try:
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
        
        print(f"   PDF文件大小: {len(pdf_bytes)} bytes")
        
        # 获取信息
        print("   获取PDF信息...")
        info = pdf_processor.get_pdf_info(pdf_bytes)
        print(f"   ✅ 页数: {info['page_count']}")
        print(f"   ✅ 文件大小: {info['file_size']} bytes")
        
        # 提取文本
        print("   提取文本...")
        
        def progress_callback(current, total):
            print(f"   进度: {current}/{total} 页", end='\r')
        
        text = pdf_processor.extract_text_with_progress(pdf_bytes, progress_callback)
        print()
        print(f"   ✅ 提取完成，共 {len(text)} 字符")
        
        # 显示前500字符
        print("\n   文本预览（前500字符）:")
        print("   " + "-" * 50)
        preview = text[:500].replace('\n', ' ')
        print(f"   {preview}...")
        print("   " + "-" * 50)
        
    except Exception as e:
        print(f"   ❌ 解析失败: {e}")
        import traceback
        traceback.print_exc()
else:
    if pdf_path:
        print(f"\n❌ 文件不存在: {pdf_path}")
    else:
        print("\n跳过PDF解析测试")

print()
print("=" * 60)
print("测试完成！")
print("=" * 60)
input("\n按回车键退出...")
