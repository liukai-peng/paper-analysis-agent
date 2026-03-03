import json
import os
from app.utils.json_parser import extract_json_from_response
from app.utils.log_util import logger

def reprocess_analysis_result(work_dir: str):
    """
    重新处理已有的分析结果，使用修复后的JSON解析器
    
    Args:
        work_dir: 工作目录路径
    """
    print(f"\n处理目录: {work_dir}")
    
    # 检查是否有raw_responses目录
    raw_responses_dir = os.path.join(work_dir, 'raw_responses')
    if not os.path.exists(raw_responses_dir):
        print(f"  跳过: 没有raw_responses目录")
        return
    
    # 读取analysis_result.json
    analysis_result_path = os.path.join(work_dir, 'analysis_result.json')
    if not os.path.exists(analysis_result_path):
        print(f"  跳过: 没有analysis_result.json")
        return
    
    with open(analysis_result_path, 'r', encoding='utf-8') as f:
        analysis_result = json.load(f)
    
    # 检查first_pass是否为空
    first_pass = analysis_result.get('first_pass', {})
    if first_pass.get('phenomenon') and first_pass.get('tools') and first_pass.get('contribution'):
        print(f"  跳过: first_pass数据已完整")
        return
    
    print(f"  需要重新处理first_pass数据")
    
    # 读取FirstPassAgent的原始响应
    first_pass_response_path = os.path.join(raw_responses_dir, 'FirstPassAgent_Task.json')
    if not os.path.exists(first_pass_response_path):
        print(f"  错误: 没有FirstPassAgent_Task.json")
        return
    
    with open(first_pass_response_path, 'r', encoding='utf-8') as f:
        first_pass_data = json.load(f)
        response_text = first_pass_data.get('response', '')
    
    if not response_text:
        print(f"  错误: FirstPassAgent响应为空")
        return
    
    # 使用修复后的JSON解析器解析
    print(f"  正在解析FirstPassAgent响应...")
    result = extract_json_from_response(response_text)
    
    if result:
        print(f"  解析成功! 包含字段: {list(result.keys())}")
        
        # 更新analysis_result
        analysis_result['first_pass'] = {
            'phenomenon': result.get('phenomenon', {}),
            'tools': result.get('tools', {}),
            'key_concepts': result.get('key_concepts', []),
            'contribution': result.get('contribution', {}),
            'writing_framework': result.get('writing_framework', {}),
            'useful_expressions': result.get('useful_expressions', {})
        }
        
        # 保存更新后的analysis_result
        with open(analysis_result_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=4)
        
        print(f"  已保存更新后的analysis_result.json")
    else:
        print(f"  警告: JSON解析失败")

def main():
    """主函数"""
    work_dir_base = 'project/work_dir'
    
    # 获取所有lit_开头的目录
    lit_dirs = [d for d in os.listdir(work_dir_base) if d.startswith('lit_')]
    lit_dirs.sort()
    
    print(f"找到 {len(lit_dirs)} 个文献分析目录")
    
    processed_count = 0
    skipped_count = 0
    error_count = 0
    
    for lit_dir in lit_dirs:
        work_dir = os.path.join(work_dir_base, lit_dir)
        try:
            reprocess_analysis_result(work_dir)
            processed_count += 1
        except Exception as e:
            print(f"  错误: {e}")
            error_count += 1
    
    print(f"\n处理完成:")
    print(f"  成功处理: {processed_count}")
    print(f"  跳过: {skipped_count}")
    print(f"  错误: {error_count}")

if __name__ == "__main__":
    main()
