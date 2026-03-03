import os
import json
import asyncio
from app.core.workflow import LiteratureWorkFlow

def get_incomplete_files():
    """
    找出需要重新分析的不完整文件
    
    Returns:
        list: 需要重新分析的文献目录列表
    """
    incomplete_files = []
    work_dirs = [d for d in os.listdir('project/work_dir') if d.startswith('lit_')]
    
    for d in work_dirs:
        analysis_path = os.path.join('project/work_dir', d, 'analysis_result.json')
        if not os.path.exists(analysis_path):
            continue
        
        with open(analysis_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查是否缺少关键字段
        first_pass = data.get('first_pass', {})
        tools = first_pass.get('tools', {})
        contribution = first_pass.get('contribution', {})
        second_pass = data.get('second_pass', {})
        
        # 如果 tools 为空或者 contribution 为空，需要重新分析
        if not tools or not contribution:
            incomplete_files.append(d)
            print(f"标记为不完整: {d}")
    
    return incomplete_files

async def reanalyze_file(lit_dir):
    """
    重新分析单个文献
    
    Args:
        lit_dir: 文献目录名
    """
    print(f"\n开始重新分析: {lit_dir}")
    
    # 构建文献路径
    work_dir = os.path.join('project/work_dir', lit_dir)
    
    # 查找 PDF 文件
    pdf_files = [f for f in os.listdir(work_dir) if f.endswith('.pdf')]
    if not pdf_files:
        print(f"  错误: 没有找到 PDF 文件")
        return False
    
    pdf_path = os.path.join(work_dir, pdf_files[0])
    print(f"  找到 PDF: {pdf_files[0]}")
    
    try:
        # 创建工作流实例
        workflow = LiteratureWorkFlow()
        
        # 运行完整分析
        await workflow.run_complete_analysis(pdf_path, work_dir)
        
        print(f"  重新分析成功!")
        return True
    except Exception as e:
        print(f"  错误: {str(e)}")
        return False

async def main():
    """
    主函数
    """
    print("查找不完整的文献...")
    incomplete_files = get_incomplete_files()
    
    print(f"\n发现 {len(incomplete_files)} 个不完整的文献")
    
    if not incomplete_files:
        print("没有需要重新分析的文献")
        return
    
    print("\n开始重新分析...")
    success_count = 0
    
    for lit_dir in incomplete_files:
        success = await reanalyze_file(lit_dir)
        if success:
            success_count += 1
    
    print(f"\n重新分析完成: {success_count}/{len(incomplete_files)} 成功")

if __name__ == "__main__":
    asyncio.run(main())
