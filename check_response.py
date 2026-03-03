import json

# 读取真实的FirstPassAgent响应
with open('project/work_dir/lit_20260303_090744/raw_responses/FirstPassAgent_Task.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    response_text = data['response']

print(f"响应长度: {len(response_text)}")
print(f"最后100字符: {response_text[-100:]}")
print(f"是否以 }} 结尾: {response_text.strip().endswith('}')}")

# 检查括号平衡
open_braces = response_text.count('{')
close_braces = response_text.count('}')
print(f"左大括号: {open_braces}, 右大括号: {close_braces}")

# 检查引号
quotes = response_text.count('"')
print(f"双引号数量: {quotes}")

# 检查是否有 ``` 结尾
print(f"是否包含 ```: {'```' in response_text}")
print(f"``` 出现次数: {response_text.count('```')}")