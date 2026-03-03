import json
import os
import re
from app.utils.json_parser import extract_json_from_response, extract_complete_field

def extract_field_from_text(text: str, field_name: str) -> dict:
    """
    从文本中提取指定字段的完整内容
    
    Args:
        text: JSON文本
        field_name: 字段名
        
    Returns:
        dict: 包含提取字段的字典
    """
    # 查找字段的开始位置
    pattern = rf'"{field_name}"\s*:\s*\{{'
    match = re.search(pattern, text)
    
    if not match:
        return {}
    
    start_pos = match.start()
    
    # 从开始位置找到匹配的闭合大括号
    brace_count = 0
    in_string = False
    escape_next = False
    
    for i in range(start_pos, len(text)):
        char = text[i]
        
        if escape_next:
            escape_next = False
            continue
        elif char == '\\':
            escape_next = True
            continue
        elif char == '"' and not in_string:
            in_string = True
            continue
        elif char == '"' and in_string:
            in_string = False
            continue
        elif char == '{' and not in_string:
            brace_count += 1
        elif char == '}' and not in_string:
            brace_count -= 1
            if brace_count == 0:
                # 找到了完整的字段
                field_text = text[start_pos:i+1]
                try:
                    # 包装成完整的JSON对象
                    wrapped = '{' + field_text + '}'
                    result = json.loads(wrapped)
                    return result
                except json.JSONDecodeError:
                    return {}
    
    return {}

def reprocess_single_file(work_dir: str):
    """重新处理单个文件"""
    print(f"处理目录: {work_dir}")
    
    # 读取analysis_result.json
    analysis_result_path = os.path.join(work_dir, 'analysis_result.json')
    with open(analysis_result_path, 'r', encoding='utf-8') as f:
        analysis_result = json.load(f)
    
    # 读取FirstPassAgent的原始响应
    first_pass_response_path = os.path.join(work_dir, 'raw_responses', 'FirstPassAgent_Task.json')
    if not os.path.exists(first_pass_response_path):
        print(f"  跳过: 没有FirstPassAgent_Task.json")
        return
    
    with open(first_pass_response_path, 'r', encoding='utf-8') as f:
        first_pass_data = json.load(f)
        response_text = first_pass_data.get('response', '')
    
    print(f"  响应长度: {len(response_text)}")
    
    # 尝试使用extract_json_from_response
    result = extract_json_from_response(response_text)
    
    if not result:
        print(f"  标准解析失败，尝试逐个字段提取...")
        result = {}
    
    # 逐个字段提取
    fields_to_extract = ['phenomenon', 'tools', 'key_concepts', 'contribution', 'writing_framework', 'useful_expressions']
    
    for field in fields_to_extract:
        if field not in result or not result[field]:
            print(f"  尝试提取字段: {field}...")
            field_data = extract_field_from_text(response_text, field)
            if field_data and field in field_data:
                result[field] = field_data[field]
                print(f"    成功提取字段: {field}")
    
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
        print(f"  警告: 无法解析任何字段")

# 处理失败的文件
work_dirs = [
    'project/work_dir/lit_20260302_211726',
    'project/work_dir/lit_20260303_090744',
]

for work_dir in work_dirs:
    print("=" * 50)
    reprocess_single_file(work_dir)
