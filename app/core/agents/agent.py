from app.core.llm.llm import LLM, simple_chat
from app.utils.log_util import logger

class Agent:
    def __init__(
        self,
        task_id: str,
        model: LLM,
        max_chat_turns: int = 30,
        max_memory: int = 12,
    ) -> None:
        self.task_id = task_id
        self.model = model
        self.chat_history: list[dict] = []
        self.max_chat_turns = max_chat_turns
        self.current_chat_turns = 0
        self.max_memory = max_memory

    async def run(self, prompt: str, system_prompt: str, sub_title: str) -> str:
        """
        执行agent的对话并返回结果

        Args:
            prompt: 输入的提示
            system_prompt: 系统提示
            sub_title: 子任务标题

        Returns:
            str: 模型的响应
        """
        try:
            logger.info(f"{self.__class__.__name__}:开始:执行对话")
            self.current_chat_turns = 0

            await self.append_chat_history({"role": "system", "content": system_prompt})
            await self.append_chat_history({"role": "user", "content": prompt})

            response = await self.model.chat(
                history=self.chat_history,
                agent_name=self.__class__.__name__,
                sub_title=sub_title,
            )
            
            # 确保响应对象存在且有有效的内容
            if not response or not hasattr(response, 'choices') or not response.choices:
                logger.error("模型响应为空或格式错误")
                raise ValueError("模型响应为空或格式错误")
            
            response_content = response.choices[0].message.content
            
            # 确保响应内容不为空
            if not response_content or str(response_content).strip() == "":
                logger.error("模型响应内容为空")
                raise ValueError("模型响应内容为空")
            
            self.chat_history.append({"role": "assistant", "content": response_content})
            logger.info(f"{self.__class__.__name__}:完成:执行对话")
            return response_content
        except Exception as e:
            error_msg = f"执行过程中遇到错误: {str(e)}"
            logger.error(f"Agent执行失败: {str(e)}")
            return error_msg

    async def append_chat_history(self, msg: dict) -> None:
        logger.debug(f"添加消息: role={msg.get('role')}, 当前历史长度={len(self.chat_history)}")
        self.chat_history.append(msg)
        logger.debug(f"添加后历史长度={len(self.chat_history)}")

        if msg.get("role") != "tool":
            logger.debug("触发内存清理")
            await self.clear_memory()
        else:
            logger.debug("跳过内存清理(tool消息)")

    async def clear_memory(self):
        """当聊天历史超过最大记忆轮次时，使用 simple_chat 进行总结压缩"""
        logger.debug(f"检查内存清理: 当前={len(self.chat_history)}, 最大={self.max_memory}")

        if len(self.chat_history) <= self.max_memory:
            logger.debug("无需清理内存")
            return

        logger.debug("开始内存清理")
        logger.info(
            f"{self.__class__.__name__}:开始清除记忆，当前记录数：{len(self.chat_history)}"
        )

        try:
            system_msg = (
                self.chat_history[0]
                if self.chat_history and self.chat_history[0]["role"] == "system"
                else None
            )

            preserve_start_idx = self._find_safe_preserve_point()
            logger.debug(f"保留起始索引: {preserve_start_idx}")

            start_idx = 1 if system_msg else 0
            end_idx = preserve_start_idx
            logger.debug(f"总结范围: {start_idx} -> {end_idx}")

            if end_idx > start_idx:
                summarize_history = []
                if system_msg:
                    summarize_history.append(system_msg)

                summarize_history.append(
                    {
                        "role": "user",
                        "content": f"请简洁总结以下对话的关键内容和重要结论，保留重要的上下文信息：\n\n{self._format_history_for_summary(self.chat_history[start_idx:end_idx])}",
                    }
                )

                summary = await simple_chat(self.model, summarize_history)

                new_history = []
                if system_msg:
                    new_history.append(system_msg)

                new_history.append(
                    {"role": "assistant", "content": f"[历史对话总结] {summary}"}
                )

                new_history.extend(self.chat_history[preserve_start_idx:])

                self.chat_history = new_history
                logger.debug(f"内存清理完成，新历史长度: {len(self.chat_history)}")
                logger.info(
                    f"{self.__class__.__name__}:记忆清除完成，压缩至：{len(self.chat_history)}条记录"
                )
            else:
                logger.info(f"{self.__class__.__name__}:无需清除记忆，记录数量合理")

        except Exception as e:
            logger.error(f"记忆清除失败，使用简单切片策略: {str(e)}")
            safe_history = self._get_safe_fallback_history()
            self.chat_history = safe_history

    def _find_safe_preserve_point(self) -> int:
        """找到安全的保留起始点，确保不会破坏工具调用序列"""
        min_preserve = min(3, len(self.chat_history))
        preserve_start = len(self.chat_history) - min_preserve
        logger.debug(
            f"寻找安全保留点: 历史长度={len(self.chat_history)}, 最少保留={min_preserve}, 开始位置={preserve_start}"
        )

        for i in range(preserve_start, -1, -1):
            if i >= len(self.chat_history):
                continue

            is_safe = self._is_safe_cut_point(i)
            logger.debug(f"检查位置 {i}: 安全={is_safe}")
            if is_safe:
                logger.debug(f"找到安全保留点: {i}")
                return i

        fallback = len(self.chat_history) - 1
        logger.debug(f"未找到安全点，使用备用位置: {fallback}")
        return fallback

    def _is_safe_cut_point(self, start_idx: int) -> bool:
        """检查从指定位置开始切割是否安全（不会产生孤立的tool消息）"""
        if start_idx >= len(self.chat_history):
            logger.debug(f"切割点 {start_idx} >= 历史长度，安全")
            return True

        tool_messages = []
        for i in range(start_idx, len(self.chat_history)):
            msg = self.chat_history[i]
            if isinstance(msg, dict) and msg.get("role") == "tool":
                tool_call_id = msg.get("tool_call_id")
                tool_messages.append((i, tool_call_id))
                logger.debug(f"发现tool消息在位置 {i}, tool_call_id={tool_call_id}")

                if tool_call_id:
                    found_tool_call = False
                    for j in range(start_idx, i):
                        prev_msg = self.chat_history[j]
                        if (
                            isinstance(prev_msg, dict)
                            and "tool_calls" in prev_msg
                            and prev_msg["tool_calls"]
                        ):
                            for tool_call in prev_msg["tool_calls"]:
                                if tool_call.get("id") == tool_call_id:
                                    found_tool_call = True
                                    logger.debug(f"找到对应的tool_call在位置 {j}")
                                    break
                            if found_tool_call:
                                break

                    if not found_tool_call:
                        logger.debug(
                            f"❌ tool消息 {tool_call_id} 没有找到对应的tool_call，切割点不安全"
                        )
                        return False

        logger.debug(f"切割点 {start_idx} 安全，检查了 {len(tool_messages)} 个tool消息")
        return True

    def _get_safe_fallback_history(self) -> list:
        """获取安全的后备历史记录，确保不会有孤立的tool消息"""
        if not self.chat_history:
            return []

        safe_history = []
        if self.chat_history and self.chat_history[0]["role"] == "system":
            safe_history.append(self.chat_history[0])

        for preserve_count in range(1, min(4, len(self.chat_history)) + 1):
            start_idx = len(self.chat_history) - preserve_count
            if self._is_safe_cut_point(start_idx):
                safe_history.extend(self.chat_history[start_idx:])
                return safe_history

        for i in range(len(self.chat_history) - 1, -1, -1):
            msg = self.chat_history[i]
            if isinstance(msg, dict) and msg.get("role") != "tool":
                safe_history.append(msg)
                break

        return safe_history

    def _format_history_for_summary(self, history: list[dict]) -> str:
        """格式化历史记录用于总结"""
        formatted = []
        for msg in history:
            role = msg["role"]
            content = (
                msg["content"][:500] + "..."
                if len(msg["content"]) > 500
                else msg["content"]
            )
            formatted.append(f"{role}: {content}")
        return "\n".join(formatted)
