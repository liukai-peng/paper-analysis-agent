from openai import OpenAI
import json
from app.utils.log_util import logger

class LLM:
    def __init__(self, model_name: str, api_key: str, base_url: str = "https://api.deepseek.com"):
        if not api_key or not api_key.strip():
            raise ValueError("API密钥不能为空")
        self.model_name = model_name
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        logger.info(f"LLM初始化完成: model={model_name}, base_url={base_url}")

    async def chat(self, history: list[dict], agent_name: str = "Agent", sub_title: str = "Task") -> object:
        """
        调用大模型进行对话

        Args:
            history: 对话历史
            agent_name: Agent名称
            sub_title: 子任务标题

        Returns:
            模型响应对象
        """
        try:
            logger.info(f"{agent_name}: 开始调用大模型 - {sub_title}")
            logger.debug(f"请求历史消息数: {len(history)}")
            
            # 验证消息格式
            valid_roles = ["system", "user", "assistant", "tool"]
            for i, msg in enumerate(history):
                if not isinstance(msg, dict):
                    logger.error(f"消息 {i} 不是字典类型: {type(msg)}, 内容: {msg}")
                    raise ValueError(f"消息 {i} 不是字典类型: {type(msg)}")
                role = msg.get("role")
                if role not in valid_roles:
                    logger.error(f"消息 {i} 的角色无效: {role}, 消息内容: {msg}")
                    raise ValueError(f"消息 {i} 的角色无效: {role}")
                if "content" not in msg:
                    logger.error(f"消息 {i} 缺少 content 字段: {msg}")
                    raise ValueError(f"消息 {i} 缺少 content 字段")
                # 检查content是否为空
                if msg.get("content") is None or str(msg.get("content")).strip() == "":
                    logger.warning(f"消息 {i} 的content为空，将替换为提示信息")
                    msg["content"] = "[空内容]"
            
            # 估算总token数（粗略估算：中文字符约占2-3个token）
            total_chars = sum(len(str(msg.get("content", ""))) for msg in history)
            logger.info(f"请求总字符数: {total_chars}")

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=history,
                temperature=0.3,
                max_tokens=4000
            )
            logger.info(f"{agent_name}: 大模型调用完成 - {sub_title}")
            return response
        except Exception as e:
            error_msg = str(e)
            logger.error(f"大模型调用失败: {error_msg}")
            # 检查是否是API密钥问题
            if "401" in error_msg or "Unauthorized" in error_msg:
                raise ValueError("API密钥无效或已过期，请检查您的API密钥")
            elif "400" in error_msg:
                raise ValueError(f"请求参数错误: {error_msg}")
            raise

async def simple_chat(model: LLM, messages: list[dict]) -> str:
    """
    简单的聊天函数，用于总结等任务

    Args:
        model: LLM实例
        messages: 消息列表

    Returns:
        模型响应内容
    """
    try:
        response = await model.chat(history=messages, agent_name="SimpleChat")
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"simple_chat失败: {str(e)}")
        return "总结失败"

class LLMFactory:
    def __init__(self, task_id: str):
        self.task_id = task_id

    def get_llm(self, model_name: str, api_key: str) -> LLM:
        """
        获取LLM实例

        Args:
            model_name: 模型名称
            api_key: API密钥

        Returns:
            LLM实例
        """
        return LLM(model_name, api_key)

    def get_all_llms(self, api_key: str) -> tuple[LLM, LLM, LLM, LLM]:
        """
        获取所有LLM实例

        Args:
            api_key: API密钥

        Returns:
            四个LLM实例
        """
        coordinator_llm = self.get_llm("deepseek-chat", api_key)
        first_pass_llm = self.get_llm("deepseek-chat", api_key)
        second_pass_llm = self.get_llm("deepseek-chat", api_key)
        third_pass_llm = self.get_llm("deepseek-chat", api_key)
        return coordinator_llm, first_pass_llm, second_pass_llm, third_pass_llm