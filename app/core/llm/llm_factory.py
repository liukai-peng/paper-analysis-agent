from app.core.llm.llm import LLM

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