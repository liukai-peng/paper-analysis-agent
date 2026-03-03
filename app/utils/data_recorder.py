import json
import os
from app.utils.log_util import logger
from typing import Any, Dict, List

class DataRecorder:
    def __init__(self, log_work_dir: str = ""):
        self.total_cost = 0.0
        self.agents_chat_history: Dict[str, List[Dict]] = {}
        self.chat_completion: Dict[str, List[Dict]] = {}
        self.log_work_dir = log_work_dir
        self.token_usage: Dict[str, Dict] = {}
        self.initialized = True
        
        # 确保工作目录存在
        if log_work_dir and not os.path.exists(log_work_dir):
            os.makedirs(log_work_dir, exist_ok=True)

    def print_summary(self):
        """打印统计摘要"""
        logger.info("\n=== Token Usage and Cost Summary ===")

        headers = ["Agent", "Chats", "Prompt", "Completion", "Total", "Cost ($)"]
        rows = []

        for agent_name, usage in self.token_usage.items():
            rows.append([
                agent_name,
                usage.get("chat_count", 0),
                usage.get("prompt_tokens", 0),
                usage.get("completion_tokens", 0),
                usage.get("total_tokens", 0),
                f"{usage.get('cost', 0.0):.4f}",
            ])

        total_chats = sum(usage.get("chat_count", 0) for usage in self.token_usage.values())
        total_prompt = sum(usage.get("prompt_tokens", 0) for usage in self.token_usage.values())
        total_completion = sum(usage.get("completion_tokens", 0) for usage in self.token_usage.values())
        total_tokens = sum(usage.get("total_tokens", 0) for usage in self.token_usage.values())

        rows.append([
            "TOTAL",
            total_chats,
            total_prompt,
            total_completion,
            total_tokens,
            f"{self.total_cost:.4f}",
        ])

        logger.info("Token Usage Summary:")
        for row in rows:
            logger.info(f"{' | '.join(map(str, row))}")

    def write_to_json(self, to_save: dict, file_name: str):
        if self.log_work_dir:
            json_path = os.path.join(self.log_work_dir, file_name)
            try:
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(to_save, f, ensure_ascii=False, indent=4)
                logger.info(f"成功写入文件: {json_path}")
            except Exception as e:
                logger.error(f"写入json文件失败: {e}")

    def append_chat_history(self, msg: dict, agent_name: str) -> None:
        """添加聊天历史记录"""
        if agent_name not in self.agents_chat_history:
            self.agents_chat_history[agent_name] = []
        self.agents_chat_history[agent_name].append(msg)
        self.write_to_json(self.agents_chat_history, "chat_history.json")

    def chat_completion_to_dict(self, completion: Any) -> Dict:
        """将 ChatCompletion 对象转换为可序列化的字典"""
        result = {
            "id": getattr(completion, "id", ""),
            "choices": [],
            "created": getattr(completion, "created", 0),
            "model": getattr(completion, "model", ""),
            "system_fingerprint": getattr(completion, "system_fingerprint", None),
        }

        if hasattr(completion, "choices"):
            for choice in completion.choices:
                choice_dict = {
                    "index": choice.index,
                    "message": {
                        "role": choice.message.role,
                        "content": choice.message.content,
                    },
                    "finish_reason": choice.finish_reason,
                }
                if hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
                    choice_dict["message"]["tool_calls"] = [
                        {
                            "id": tool_call.id,
                            "type": tool_call.type,
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments,
                            },
                        }
                        for tool_call in choice.message.tool_calls
                    ]
                result["choices"].append(choice_dict)

        if hasattr(completion, "usage"):
            result["usage"] = {
                "completion_tokens": completion.usage.completion_tokens,
                "prompt_tokens": completion.usage.prompt_tokens,
                "total_tokens": completion.usage.total_tokens,
            }

        return result

    def append_chat_completion(self, completion: Any, agent_name: str) -> None:
        """添加聊天完成记录"""
        if agent_name not in self.chat_completion:
            self.chat_completion[agent_name] = []

        completion_dict = self.chat_completion_to_dict(completion)
        self.chat_completion[agent_name].append(completion_dict)

        self.update_token_usage(completion, agent_name)

        self.write_to_json(self.chat_completion, "chat_completion.json")

    def update_token_usage(self, completion: Any, agent_name: str) -> None:
        """更新 token 使用统计和费用"""
        if not hasattr(completion, "usage"):
            return

        if agent_name not in self.token_usage:
            self.token_usage[agent_name] = {
                "completion_tokens": 0,
                "prompt_tokens": 0,
                "total_tokens": 0,
                "chat_count": 0,
                "cost": 0.0,
            }

        usage = completion.usage
        model = getattr(completion, "model", "")

        self.token_usage[agent_name]["completion_tokens"] += usage.completion_tokens
        self.token_usage[agent_name]["prompt_tokens"] += usage.prompt_tokens
        self.token_usage[agent_name]["total_tokens"] += usage.total_tokens
        self.token_usage[agent_name]["chat_count"] += 1

        cost = self.calculate_cost(model, usage.prompt_tokens, usage.completion_tokens)
        self.token_usage[agent_name]["cost"] += cost
        self.total_cost += cost

        self.write_to_json(self.token_usage, "token_usage.json")

    def calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """计算API调用费用"""
        model_prices = {
            "deepseek-chat": {"prompt": 0.00015, "completion": 0.0006},
            "gpt-4-turbo-preview": {"prompt": 0.01, "completion": 0.03},
            "gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015},
        }

        model_price = model_prices.get(model, {"prompt": 0.0001, "completion": 0.0001})

        prompt_cost = (prompt_tokens / 1000.0) * model_price["prompt"]
        completion_cost = (completion_tokens / 1000.0) * model_price["completion"]

        return prompt_cost + completion_cost

    def save_raw_response(self, response: str, agent_name: str, step: str):
        """保存原始响应"""
        if not self.log_work_dir:
            return

        raw_dir = os.path.join(self.log_work_dir, "raw_responses")
        os.makedirs(raw_dir, exist_ok=True)

        file_name = f"{agent_name}_{step}.json"
        file_path = os.path.join(raw_dir, file_name)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump({"response": response}, f, ensure_ascii=False, indent=4)
            logger.info(f"成功保存原始响应: {file_path}")
        except Exception as e:
            logger.error(f"保存原始响应失败: {e}")

    def get_latest_response(self, agent_name: str) -> str:
        """获取指定Agent的最新响应"""
        if agent_name not in self.chat_completion:
            return ""
        
        completions = self.chat_completion[agent_name]
        if not completions:
            return ""
        
        latest = completions[-1]
        if latest.get("choices"):
            return latest["choices"][0]["message"].get("content", "")
        return ""

    def save_analysis_result(self, result: dict):
        """保存分析结果"""
        if self.log_work_dir:
            json_path = os.path.join(self.log_work_dir, "analysis_result.json")
            try:
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=4)
                logger.info(f"成功保存分析结果: {json_path}")
            except Exception as e:
                logger.error(f"保存分析结果失败: {e}")
