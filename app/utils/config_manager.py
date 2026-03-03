import os
import json
from typing import Optional
from cryptography.fernet import Fernet
from app.utils.log_util import logger

class ConfigManager:
    """配置管理器，负责安全存储和读取配置"""
    
    def __init__(self, config_file: str = "config.json"):
        # 使用绝对路径，确保在任何工作目录下都能找到配置文件
        import os
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.base_dir, config_file)
        self.config = self._load_config()
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)
    
    def _get_or_create_key(self) -> bytes:
        """获取或创建加密密钥"""
        key_file = os.path.join(self.base_dir, "secret.key")
        
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(key)
            logger.info("创建新的加密密钥")
            return key
    
    def _load_config(self) -> dict:
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
                return {}
        return {}
    
    def _save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
    
    def _encrypt(self, data: str) -> str:
        """加密数据"""
        try:
            encrypted = self.cipher.encrypt(data.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"加密数据失败: {e}")
            return data
    
    def _decrypt(self, encrypted_data: str) -> str:
        """解密数据"""
        try:
            decrypted = self.cipher.decrypt(encrypted_data.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"解密数据失败: {e}")
            return encrypted_data
    
    def set_api_key(self, api_key: str, provider: str = "deepseek"):
        """设置API密钥（加密存储）"""
        try:
            if "api_keys" not in self.config:
                self.config["api_keys"] = {}
            
            encrypted_key = self._encrypt(api_key)
            self.config["api_keys"][provider] = encrypted_key
            self._save_config()
            logger.info(f"成功保存 {provider} API密钥")
            return True
        except Exception as e:
            logger.error(f"保存API密钥失败: {e}")
            return False
    
    def get_api_key(self, provider: str = "deepseek") -> Optional[str]:
        """获取API密钥（解密）"""
        try:
            if "api_keys" not in self.config or provider not in self.config["api_keys"]:
                logger.warning(f"未找到 {provider} API密钥")
                return None
            
            encrypted_key = self.config["api_keys"][provider]
            return self._decrypt(encrypted_key)
        except Exception as e:
            logger.error(f"获取API密钥失败: {e}")
            return None
    
    def set_config(self, key: str, value: any):
        """设置配置项"""
        self.config[key] = value
        self._save_config()
    
    def get_config(self, key: str, default: any = None) -> any:
        """获取配置项"""
        return self.config.get(key, default)
    
    def remove_api_key(self, provider: str = "deepseek"):
        """删除API密钥"""
        try:
            if "api_keys" in self.config and provider in self.config["api_keys"]:
                del self.config["api_keys"][provider]
                self._save_config()
                logger.info(f"成功删除 {provider} API密钥")
                return True
            return False
        except Exception as e:
            logger.error(f"删除API密钥失败: {e}")
            return False

# 全局配置管理器实例
config_manager = ConfigManager()

def get_api_key(provider: str = "deepseek") -> Optional[str]:
    """获取API密钥的便捷函数"""
    return config_manager.get_api_key(provider)

def set_api_key(api_key: str, provider: str = "deepseek") -> bool:
    """设置API密钥的便捷函数"""
    return config_manager.set_api_key(api_key, provider)