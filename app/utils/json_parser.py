import json
import re
from app.utils.log_util import logger

def extract_json_from_response(response_text: str) -> dict:
    """
    从大模型响应中提取JSON数据，使用多种策略确保解析成功
    
    Args:
        response_text: 大模型返回的原始响应文本
        
    Returns:
        dict: 解析出的JSON对象，如果解析失败返回空字典
    """
    if not response_text:
        logger.error("响应文本为空")
        return {}
    
    # 策略1: 尝试直接解析整个响应
    try:
        result = json.loads(response_text)
        logger.info("策略1成功: 直接解析整个响应")
        return result
    except json.JSONDecodeError:
        logger.debug("策略1失败: 响应不是纯JSON格式")
    
    # 策略2: 移除代码块标记并尝试解析
    try:
        # 移除 ```json 和 ``` 标记（使用更灵活的正则表达式）
        cleaned = re.sub(r'```json\s*', '', response_text, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s*```\s*$', '', cleaned)
        result = json.loads(cleaned)
        logger.info("策略2成功: 移除代码块后解析")
        return result
    except json.JSONDecodeError:
        logger.debug("策略2失败: 移除代码块后仍无法解析")
    
    # 策略3: 清理文本并再次尝试
    try:
        cleaned_text = clean_json_text(response_text)
        result = json.loads(cleaned_text)
        logger.info("策略3成功: 清理后解析响应")
        return result
    except json.JSONDecodeError as e:
        logger.debug(f"策略3失败: {e}")
    
    # 策略4: 使用正则表达式匹配JSON对象
    json_pattern = r'\{[\s\S]*\}'
    matches = re.findall(json_pattern, response_text, re.DOTALL)
    if matches:
        matches.sort(key=len, reverse=True)
        for match in matches:
            try:
                cleaned_match = clean_json_text(match)
                result = json.loads(cleaned_match)
                logger.info(f"策略4成功: 匹配并清理后解析，长度: {len(match)}")
                return result
            except json.JSONDecodeError:
                continue
    
    # 策略5: 尝试修复被截断的JSON
    try:
        fixed_truncated = fix_truncated_json(response_text)
        if fixed_truncated:
            result = json.loads(fixed_truncated)
            logger.info("策略5成功: 修复被截断的JSON")
            return result
    except json.JSONDecodeError as e:
        logger.debug(f"策略5失败: {e}")
    
    # 策略6: 尝试使用json5库（如果可用）
    try:
        import json5
        result = json5.loads(response_text)
        logger.info("策略6成功: 使用json5库解析")
        return result
    except ImportError:
        logger.debug("策略6失败: json5库未安装")
    except Exception as e:
        logger.debug(f"策略6失败: {e}")
    
    # 所有策略都失败，记录错误并返回空字典
    logger.error(f"所有JSON解析策略都失败。响应内容预览: {response_text[:500]}...")
    return {}

def clean_json_text(text: str) -> str:
    """
    清理JSON文本，处理常见的格式问题
    
    Args:
        text: 可能有格式问题的JSON文本
        
    Returns:
        str: 清理后的JSON文本
    """
    # 移除BOM标记
    text = text.replace('\ufeff', '')
    
    # 移除注释
    text = re.sub(r'//.*?\n', '\n', text)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    
    # 修复尾随逗号
    text = re.sub(r',(\s*[}\]])', r'\1', text)
    
    # 修复中文引号和特殊引号
    text = text.replace('“', '"')
    text = text.replace('”', '"')
    text = text.replace('‘', "'")
    text = text.replace('’', "'")
    
    # 修复字符串内部的未转义引号
    # 使用状态机来正确处理
    result = []
    in_string = False
    escape_next = False
    
    for char in text:
        if escape_next:
            result.append(char)
            escape_next = False
        elif char == '\\':
            result.append(char)
            escape_next = True
        elif char == '"':
            if in_string:
                # 检查是否是字符串结束
                i = len(result) - 1
                backslash_count = 0
                while i >= 0 and result[i] == '\\':
                    backslash_count += 1
                    i -= 1
                if backslash_count % 2 == 0:
                    in_string = False
            else:
                in_string = True
            result.append(char)
        else:
            result.append(char)
    
    return ''.join(result)

def extract_complete_field(text: str, field_name: str) -> dict:
    """
    从文本中提取完整的字段内容，如果字段被截断则尝试修复
    
    Args:
        text: JSON文本
        field_name: 字段名
        
    Returns:
        dict: 包含提取字段的字典
    """
    import re
    
    # 构建正则表达式模式来匹配字段
    # 匹配 "field_name": { ... } 或 "field_name": [ ... ]
    pattern = rf'"{field_name}"\s*:\s*([{{\[])'  # 匹配开始的大括号或中括号
    match = re.search(pattern, text)
    
    if not match:
        return {}
    
    start_pos = match.start()
    start_brace = match.group(1)
    end_brace = '}' if start_brace == '{' else ']'
    
    # 从字段开始位置，找到匹配的闭合括号
    brace_count = 0
    in_string = False
    escape_next = False
    last_valid_pos = None
    
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
        elif char == start_brace and not in_string:
            brace_count += 1
        elif char == end_brace and not in_string:
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
    
    # 字段被截断了，尝试修复
    # 找到最后一个可以解析的位置
    for i in range(len(text), start_pos, -1):
        truncated_field = text[start_pos:i]
        # 尝试添加闭合括号
        fixed_field = truncated_field + end_brace * (brace_count if brace_count > 0 else 0)
        # 尝试闭合未闭合的字符串
        quote_count = 0
        j = 0
        while j < len(fixed_field):
            if fixed_field[j] == '\\' and j + 1 < len(fixed_field) and fixed_field[j + 1] == '"':
                j += 2
            elif fixed_field[j] == '"':
                quote_count += 1
                j += 1
            else:
                j += 1
        
        if quote_count % 2 != 0:
            fixed_field += '"'
        
        try:
            wrapped = '{' + fixed_field + '}'
            result = json.loads(wrapped)
            return result
        except json.JSONDecodeError:
            continue
    
    return {}

def fix_truncated_json(text: str) -> str:
    """
    修复被截断的JSON，使用智能截断策略
    
    Args:
        text: 可能被截断的JSON文本
        
    Returns:
        str: 修复后的JSON文本，如果无法修复则返回空字符串
    """
    # 首先清理文本
    text = clean_json_text(text)
    
    # 移除代码块标记
    text = re.sub(r'```json\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*```\s*$', '', text)
    
    # 找到最后一个完整的JSON对象
    best_result = None
    best_length = 0
    
    # 尝试不同的截断位置
    for i in range(len(text), 0, -1):
        truncated = text[:i]
        try:
            result = json.loads(truncated)
            if isinstance(result, dict) and len(truncated) > best_length:
                best_result = result
                best_length = len(truncated)
                break
        except json.JSONDecodeError:
            continue
    
    if best_result:
        return json.dumps(best_result)
    
    # 如果没有找到完整的JSON对象，尝试提取各个字段
    result = {}
    fields_to_extract = ['phenomenon', 'tools', 'key_concepts', 'contribution', 'writing_framework', 'useful_expressions']
    
    for field in fields_to_extract:
        field_data = extract_complete_field(text, field)
        if field_data and field in field_data:
            result[field] = field_data[field]
    
    if result:
        return json.dumps(result)
    
    # 如果还是失败，尝试修复括号
    open_braces = text.count('{')
    close_braces = text.count('}')
    open_brackets = text.count('[')
    close_brackets = text.count(']')
    
    if open_braces > close_braces:
        text += '}' * (open_braces - close_braces)
    if open_brackets > close_brackets:
        text += ']' * (open_brackets - close_brackets)
    
    # 检查是否还有未闭合的字符串
    quote_count = 0
    i = 0
    while i < len(text):
        if text[i] == '\\' and i + 1 < len(text) and text[i + 1] == '"':
            i += 2
        elif text[i] == '"':
            quote_count += 1
            i += 1
        else:
            i += 1
    
    if quote_count % 2 != 0:
        text += '"'
    
    try:
        result = json.loads(text)
        return json.dumps(result)
    except json.JSONDecodeError:
        pass
    
    return text

def safe_json_parse(response_text: str, default_value: dict = None) -> dict:
    """
    安全的JSON解析，提供默认值
    
    Args:
        response_text: 要解析的文本
        default_value: 解析失败时返回的默认值
        
    Returns:
        dict: 解析结果或默认值
    """
    if default_value is None:
        default_value = {}
    
    result = extract_json_from_response(response_text)
    return result if result else default_value