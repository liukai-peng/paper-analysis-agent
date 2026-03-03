import json

# 读取失败的文件
with open('project/work_dir/lit_20260302_193648/raw_responses/FirstPassAgent_Task.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    response_text = data['response']

print(f"响应长度: {len(response_text)}")
print(f"最后200字符: {response_text[-200:]}")

# 检查JSON结构
print(f"\nJSON结构检查:")
print(f"  左大括号 {{ 数量: {response_text.count('{')}")
print(f"  右大括号 }} 数量: {response_text.count('}')}")
print(f"  左中括号 [ 数量: {response_text.count('[')}")
print(f"  右中括号 ] 数量: {response_text.count(']')}")
print(f"  双引号 \" 数量: {response_text.count('"')}")

# 找到phenomenon字段
import re
phenom_match = re.search(r'"phenomenon":\s*\{', response_text)
if phenom_match:
    start_pos = phenom_match.start()
    print(f"\nphenomenon字段开始位置: {start_pos}")
    
    # 尝试找到phenomenon字段的结束位置
    brace_count = 0
    in_string = False
    escape_next = False
    
    for i in range(start_pos, len(response_text)):
        char = response_text[i]
        
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
                print(f"phenomenon字段结束位置: {i}")
                print(f"phenomenon字段长度: {i - start_pos + 1}")
                break
    else:
        print(f"phenomenon字段未闭合，当前brace_count: {brace_count}")
        print(f"文本在位置 {len(response_text)-1} 结束")
