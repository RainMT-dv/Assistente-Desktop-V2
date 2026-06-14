"""Teste rápido do LLM para validar correções do bug crítico."""

import asyncio
import sys
import os

# Adiciona V2 ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import direto para evitar dependências circulares
import importlib.util
spec = importlib.util.spec_from_file_location("llm_fallback", os.path.join(os.path.dirname(__file__), "core", "llm_fallback.py"))
llm_fallback = importlib.util.module_from_spec(spec)
spec.loader.exec_module(llm_fallback)

chat_completion = llm_fallback.chat_completion
get_llm = llm_fallback.get_llm


async def test_llm_multiple_messages():
    """Testa enviar múltiplas mensagens consecutivas para verificar se o bug foi corrigido."""
    
    print("=" * 60)
    print("TESTE DE CORREÇÃO DO BUG CRÍTICO DO LLM")
    print("=" * 60)
    print()
    
    # Mostra quais providers estão disponíveis
    llm = get_llm()
    print("Providers disponíveis:")
    for p in llm.text_providers:
        status = "✅" if p.available else "❌"
        print(f"  {status} {p.config.name}: {p.config.model}")
    print()
    
    # Teste 1: Primeira mensagem
    print("-" * 40)
    print("TESTE 1: Primeira mensagem")
    print("-" * 40)
    
    messages1 = [
        {"role": "system", "content": "Você é um Assistente, uma IA debochada e direta. Responda em até 10 palavras."},
        {"role": "user", "content": "Oi, tudo bem?"}
    ]
    
    try:
        response1 = await chat_completion(messages1, mode="text", temperature=0.7, max_tokens=50)
        print(f"✅ Resposta 1: {response1}")
    except Exception as e:
        print(f"❌ ERRO na primeira mensagem: {type(e).__name__}: {e}")
    
    print()
    
    # Teste 2: Segunda mensagem (AQUI ERA O BUG - falhava sempre!)
    print("-" * 40)
    print("TESTE 2: Segunda mensagem (onde ocorria o bug)")
    print("-" * 40)
    
    messages2 = [
        {"role": "system", "content": "Você é um Assistente, uma IA debochada e direta. Responda em até 10 palavras."},
        {"role": "user", "content": "Oi, tudo bem?"},
        {"role": "assistant", "content": response1 if 'response1' in locals() else "Tô bem, e você?"},
        {"role": "user", "content": "Qual seu nome?"}
    ]
    
    try:
        response2 = await chat_completion(messages2, mode="text", temperature=0.7, max_tokens=50)
        print(f"✅ Resposta 2: {response2}")
    except Exception as e:
        print(f"❌ ERRO na segunda mensagem: {type(e).__name__}: {e}")
    
    print()
    
    # Teste 3: Terceira mensagem
    print("-" * 40)
    print("TESTE 3: Terceira mensagem")
    print("-" * 40)
    
    messages3 = [
        {"role": "system", "content": "Você é um Assistente, uma IA debochada e direta. Responda em até 10 palavras."},
        {"role": "user", "content": "Oi, tudo bem?"},
        {"role": "assistant", "content": response1 if 'response1' in locals() else "Tô bem, e você?"},
        {"role": "user", "content": "Qual seu nome?"},
        {"role": "assistant", "content": response2 if 'response2' in locals() else "Assistente"},
        {"role": "user", "content": "O que você faz?"}
    ]
    
    try:
        response3 = await chat_completion(messages3, mode="text", temperature=0.7, max_tokens=50)
        print(f"✅ Resposta 3: {response3}")
    except Exception as e:
        print(f"❌ ERRO na terceira mensagem: {type(e).__name__}: {e}")
    
    print()
    print("=" * 60)
    print("TESTE CONCLUÍDO")
    print("=" * 60)
    print()
    print("Se todas as 3 mensagens retornaram respostas (✅), o bug foi corrigido!")
    print("Se alguma falhou (❌), verifique os logs acima para o erro específico.")


if __name__ == "__main__":
    asyncio.run(test_llm_multiple_messages())
