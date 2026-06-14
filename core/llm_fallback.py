"""LLM Fallback Multi-Provider - Sistema de fallback com múltiplos provedores.
Suporta rotas TEXT (chat) e VISION (análise de imagem).
"""

import os
import time
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from .logger import log


class LLMMode(Enum):
    """Modos de operação do LLM."""
    TEXT = "text"
    VISION = "vision"


@dataclass
class ProviderConfig:
    """Configuração de um provedor LLM."""
    name: str
    model: str
    base_url: str
    env_key: str
    priority: int = 0  # Menor = mais prioritário


# Configuração TEXT (chat de conversa)
# Prioridade: Provedores free com mesmo modelo (gpt-oss-120b:free) para consistência
TEXT_PROVIDERS = [
    ProviderConfig(
        name="OpenRouter",
        model="openai/gpt-oss-120b:free",
        base_url="https://openrouter.ai/api/v1",
        env_key="OPENROUTER_API_KEY",
        priority=1
    ),
    ProviderConfig(
        name="Cerebras",
        model="openai/gpt-oss-120b:free",
        base_url="https://api.cerebras.ai/v1",
        env_key="CEREBRAS_API_KEY",
        priority=2
    ),
    ProviderConfig(
        name="NVIDIA",
        model="openai/gpt-oss-120b:free",
        base_url="https://integrate.api.nvidia.com/v1",
        env_key="NVIDIA_API_KEY",
        priority=3
    ),
    ProviderConfig(
        name="Groq",
        model="llama-3.3-70b-versatile",  # Melhor modelo FREE do Groq
        base_url="https://api.groq.com/openai/v1",
        env_key="GROQ_API_KEY",
        priority=4
    ),
    # Fallback Local - Ollama
    ProviderConfig(
        name="Local (Ollama)",
        model="gemma4:e2b",
        base_url="http://localhost:11434/v1",
        env_key="OLLAMA_API_KEY",
        priority=5  # Último fallback
    ),
]

# Configuração VISION (leitura de tela/imagem)
VISION_PROVIDERS = [
    ProviderConfig(
        name="Groq",
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        base_url="https://api.groq.com/openai/v1",
        env_key="GROQ_API_KEY",
        priority=1
    ),
    ProviderConfig(
        name="SiliconFlow",
        model="Qwen/Qwen2.5-VL-72B-Instruct",
        base_url="https://api.siliconflow.cn/v1",
        env_key="SILICONFLOW_API_KEY",
        priority=2
    ),
    ProviderConfig(
        name="NVIDIA",
        model="meta/llama-3.2-90b-vision-instruct",
        base_url="https://integrate.api.nvidia.com/v1",
        env_key="NVIDIA_API_KEY",
        priority=3
    ),
    ProviderConfig(
        name="OpenRouter",
        model="google/gemma-4-26b-a4b-it:free",
        base_url="https://openrouter.ai/api/v1",
        env_key="OPENROUTER_API_KEY",
        priority=4
    ),
    ProviderConfig(
        name="DeepSeek",
        model="deepseek-chat",
        base_url="https://api.deepseek.com/v1",
        env_key="DEEPSEEK_API_KEY",
        priority=5
    ),
]


class LLMProvider:
    """Representa um provedor LLM com sua configuração."""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.api_key = os.getenv(config.env_key, "")
        self.available = bool(self.api_key and self.api_key.strip())
    
    async def call(
        self,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 150,
        timeout: int = 30
    ) -> str:
        """Chama o provedor via API OpenAI-compatible."""
        
        if not self.available:
            raise ValueError(f"API key {self.config.env_key} não configurada")
        
        # DEBUG: Log detalhado da chamada
        from .logger import log
        log('LLM', f'[DEBUG] Chamando {self.config.name}...')
        log('LLM', f'[DEBUG] URL: {self.config.base_url}/chat/completions')
        log('LLM', f'[DEBUG] Model: {self.config.model}')
        log('LLM', f'[DEBUG] Messages count: {len(messages)}')
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        # Adiciona headers específicos para OpenRouter
        if "openrouter" in self.config.base_url.lower():
            headers["HTTP-Referer"] = "https://github.com/your-repo/personal-assistant"
            headers["X-Title"] = "Personal Assistant AI"
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        async with aiohttp.ClientSession() as session:
            url = f"{self.config.base_url}/chat/completions"

            # Ajusta timeout para Ollama (modelos locais demoram mais na 1050 Ti)
            if self.config.name == "Local (Ollama)":
                timeout = aiohttp.ClientTimeout(total=60)  # 60s para local
                # Ajusta max_tokens para respostas mais curtas e rápidas
                payload["max_tokens"] = min(payload.get("max_tokens", 150), 100)

            async with session.post(
                url,
                headers=headers,
                json=payload,
                timeout=timeout
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    log('ERROR', f'[LLM] {self.config.name} retornou HTTP {response.status}: {error_text[:500]}')
                    raise Exception(f"HTTP {response.status}: {error_text}")
                
                data = await response.json()
                return data['choices'][0]['message']['content']


class MultiProviderLLM:
    """Gerenciador de múltiplos provedores LLM com fallback automático."""

    def __init__(self):
        self.text_providers = [LLMProvider(cfg) for cfg in TEXT_PROVIDERS]
        self.vision_providers = [LLMProvider(cfg) for cfg in VISION_PROVIDERS]
        # NOVO: Dicionário de cooldown {provider_name: timestamp_para_retornar}
        self.cooldowns: Dict[str, float] = {}

    def _get_available_providers(self, mode: LLMMode) -> List[LLMProvider]:
        """Retorna provedores disponíveis ordenados por prioridade."""
        providers = self.text_providers if mode == LLMMode.TEXT else self.vision_providers
        available = []
        now = time.time()

        for p in providers:
            if not p.available:
                continue
            # Checa se está em cooldown
            if p.config.name in self.cooldowns:
                if now < self.cooldowns[p.config.name]:
                    # Ainda está em cooldown, pula
                    log('LLM', f'{p.config.name} em cooldown ({int(self.cooldowns[p.config.name] - now)}s restantes)')
                    continue
                else:
                    # Cooldown expirou, remove da lista
                    del self.cooldowns[p.config.name]

            available.append(p)

        return sorted(available, key=lambda p: p.config.priority)
    
    async def chat_completion(
        self,
        messages: List[Dict],
        mode: str = "text",
        temperature: float = 0.7,
        max_tokens: int = 150,
        timeout: int = 30,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Executa chat completion com fallback automático entre provedores.
        
        Args:
            messages: Lista de mensagens no formato OpenAI
            mode: "text" ou "vision"
            temperature: Temperatura de sampling
            max_tokens: Máximo de tokens na resposta
            timeout: Timeout em segundos
            
        Returns:
            Dict com 'response', 'provider', 'model', 'success', 'error'
        """
        llm_mode = LLMMode.TEXT if mode.lower() == "text" else LLMMode.VISION
        providers = self._get_available_providers(llm_mode)
        
        if not providers:
            raise Exception(
                f"Nenhum provedor {llm_mode.value} disponível. "
                f"Configure as API keys no arquivo .env"
            )
        
        errors = []
        
        for provider in providers:
            try:
                log('LLM', f'Tentando {provider.config.name} ({provider.config.model})...')
                
                response = await provider.call(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=timeout
                )
                
                log('LLM', f'Sucesso com {provider.config.name}')

                # Log especial se foi Ollama (fallback local)
                if provider.config.name == "Local (Ollama)":
                    log('LLM', '⚠️ Usando fallback local (todos os online falharam)')

                return {
                    'response': response,
                    'provider': provider.config.name,
                    'model': provider.config.model,
                    'success': True,
                    'error': None
                }
                
            except asyncio.TimeoutError:
                error_msg = f"Timeout com {provider.config.name}"
                log('LLM', error_msg)
                errors.append(error_msg)
                continue
                
            except Exception as e:
                import traceback
                error_type = type(e).__name__
                error_msg = f"{provider.config.name}: {error_type}: {str(e)}"
                
                # Log detalhado do erro
                log('ERROR', f'[LLM] Provedor {provider.config.name} falhou: {error_type}: {str(e)}')
                log('ERROR', f'[LLM] Traceback: {traceback.format_exc()}')
                
                # Se tiver atributos de response, logar também
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        response_text = e.response.text if hasattr(e.response, 'text') else str(e.response)
                        status = e.response.status if hasattr(e.response, 'status') else 'N/A'
                        log('ERROR', f'[LLM] Response status: {status}, body: {response_text[:500]}')
                    except:
                        pass
                
                errors.append(error_msg)

                # NOVO: Se for Rate Limit (429), coloca em cooldown por 60 segundos
                if "429" in str(e):
                    self.cooldowns[provider.config.name] = time.time() + 60
                    log('LLM', f'{provider.config.name} em cooldown por 60s (Rate Limit)')

                continue
        
        # Todos falharam
        all_errors = " | ".join(errors)
        raise Exception(f"Todos os provedores falharam: {all_errors}")


# Instância global singleton
_llm_instance: Optional[MultiProviderLLM] = None


def get_llm() -> MultiProviderLLM:
    """Retorna instância singleton do MultiProviderLLM."""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = MultiProviderLLM()
    return _llm_instance


# Função principal de conveniência
async def chat_completion(
    messages: List[Dict],
    mode: str = "text",
    **kwargs
) -> str:
    """
    Função principal para chat completion.
    
    Args:
        messages: Lista de mensagens
        mode: "text" ou "vision"
        **kwargs: Parâmetros adicionais (temperature, max_tokens, timeout)
        
    Returns:
        Texto da resposta
        
    Raises:
        Exception: Se todos os provedores falharem
    """
    llm = get_llm()
    result = await llm.chat_completion(messages, mode=mode, **kwargs)
    
    if result['success']:
        return result['response']
    else:
        raise Exception(result['error'])


if __name__ == "__main__":
    import os
    
    async def test():
        # Testa carregamento das configs
        llm = get_llm()
        
        print("\n=== Provedores TEXT disponíveis ===")
        for p in llm.text_providers:
            status = "✅" if p.available else "❌"
            print(f"{status} {p.config.name}: {p.config.model} (env: {p.config.env_key})")
        
        print("\n=== Provedores VISION disponíveis ===")
        for p in llm.vision_providers:
            status = "✅" if p.available else "❌"
            print(f"{status} {p.config.name}: {p.config.model} (env: {p.config.env_key})")
        
        # Testa chamada se houver algum disponível
        test_messages = [{"role": "user", "content": "Oi! Responda com 'OK'"}]
        
        if any(p.available for p in llm.text_providers):
            try:
                print("\n=== Teste TEXT ===")
                result = await llm.chat_completion(test_messages, mode="text")
                print(f"Sucesso: {result['provider']} -> {result['response'][:100]}")
            except Exception as e:
                print(f"Erro: {e}")
        else:
            print("\n=== Configure as API keys no .env para testar ===")
    
    asyncio.run(test())
