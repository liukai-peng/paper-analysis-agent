import os
import json

# 检查文件大小
file_path = 'project/work_dir/lit_20260302_211726/raw_responses/FirstPassAgent_Task.json'
file_size = os.path.getsize(file_path)
print(f"文件大小: {file_size} 字节")

# 读取文件内容
with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)
    response_text = data['response']

print(f"响应长度: {len(response_text)}")
print(f"响应最后100字符: {response_text[-100:]}")

# 检查是否有未闭合的引号
open_quotes = 0
close_quotes = 0

for char in response_text:
    if char == '"':
        open_quotes += 1
    elif char == '"':
        close_quotes += 1

print(f"双引号数量: {open_quotes}")

# 检查是否以 } 结尾
print(f"是否以 '}}' 结尾: {response_text.strip().endswith('}}')}")
print(f"最后50字符: {response_text[-50:]}")