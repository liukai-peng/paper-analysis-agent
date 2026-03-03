import json
import re

# 读取真实的FirstPassAgent响应
with open('project/work_dir/lit_20260303_090744/raw_responses/FirstPassAgent_Task.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    response_text = data['response']

print(f"响应总长度: {len(response_text)}")

# 检查各个字段是否存在
fields_to_check = [
    '"phenomenon"',
    '"tools"',
    '"key_concepts"',
    '"contribution"',
    '"writing_framework"',
    '"useful_expressions"'
]

print("\n字段存在情况:")
for field in fields_to_check:
    if field in response_text:
        # 找到字段位置
        pos = response_text.find(field)
        print(f"  {field}: 存在 (位置: {pos})")
    else:
        print(f"  {field}: 不存在")

# 尝试提取tools字段的完整内容
tools_match = re.search(r'"tools":\s*\{', response_text)
if tools_match:
    start_pos = tools_match.start()
    print(f"\ntools字段开始位置: {start_pos}")
    
    # 从tools开始，尝试找到匹配的闭合括号
    brace_count = 0
    in_string = False
    escape_next = False
    
    for i in range(start_pos, len(response_text)):
        char = response_text[i]
        
        if escape_next:
            escape_next = False
        elif char == '\\':
            escape_next = True
        elif char == '"' and not in_string:
            in_string = True
        elif char == '"' and in_string:
            in_string = False
        elif char == '{' and not in_string:
            brace_count += 1
        elif char == '}' and not in_string:
            brace_count -= 1
            if brace_count == 0:
                print(f"tools字段结束位置: {i}")
                tools_content = response_text[start_pos:i+1]
                print(f"tools字段长度: {len(tools_content)}")
                print(f"tools字段前200字符: {tools_content[:200]}")
                break
    else:
        print("tools字段未闭合（被截断）")

# 检查JSON结构完整性
print(f"\nJSON结构检查:")
print(f"  左大括号 {{ 数量: {response_text.count('{')}")
print(f"  右大括号 }} 数量: {response_text.count('}')}")
print(f"  左中括号 [ 数量: {response_text.count('[')}")
print(f"  右中括号 ] 数量: {response_text.count(']')}")
print(f"  双引号 \" 数量: {response_text.count('"')}")
