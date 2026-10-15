"""模型接入网关（可插拔开关）"""

from typing import Optional, Dict, Any
from dataclasses import dataclass

from .config import Config, ModelConfig
from ..exceptions import ModelDisabledError, ModelConfigError


@dataclass
class SkeletonResult:
    """骨架生成结果"""
    code: str
    draft: bool
    uncertainties: list
    model_info: Dict[str, Any]


class ModelGateway:
    """模型接入网关（可插拔开关）"""
    
    def __init__(self, config: ModelConfig):
        self.enabled = config.enabled
        self.endpoint = config.endpoint
        self.api_key = config.api_key
        self.model = config.model
        self.llama_cpp_path = config.llama_cpp_path
        self.omni_infer_url = config.omni_infer_url
    
    def generate_skeleton(self, prompt: str) -> SkeletonResult:
        """
        生成证明骨架
        
        Args:
            prompt: 输入提示
            
        Returns:
            SkeletonResult: 骨架生成结果
            
        Raises:
            ModelDisabledError: 模型已关闭
            ModelConfigError: 模型配置错误
        """
        if not self.enabled:
            raise ModelDisabledError("模型已关闭，请启用后重试")
        
        # 按端点类型分发
        if self.endpoint:
            return self._call_openai_endpoint(prompt)
        elif self.llama_cpp_path:
            return self._call_llama_cpp(prompt)
        elif self.omni_infer_url:
            return self._call_omni_infer(prompt)
        else:
            raise ModelConfigError("未配置模型端点")
    
    def _call_openai_endpoint(self, prompt: str) -> SkeletonResult:
        """调用 OpenAI 兼容端点"""
        # TODO: 实现 OpenAI API 调用
        raise NotImplementedError("OpenAI 端点待实现")
    
    def _call_llama_cpp(self, prompt: str) -> SkeletonResult:
        """调用 llama.cpp server"""
        # TODO: 实现 llama.cpp 调用
        raise NotImplementedError("llama.cpp 端点待实现")
    
    def _call_omni_infer(self, prompt: str) -> SkeletonResult:
        """调用 omni-infer（昇腾）"""
        # TODO: 实现 omni-infer 调用
        raise NotImplementedError("omni-infer 端点待实现")
