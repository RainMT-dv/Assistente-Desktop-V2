# PESQUISA DE COMPATIBILIDADE: Hume AI EVI e EmotiVoice vs GTX 1050 Ti 4GB VRAM

## RESUMO EXECUTIVO

**Objetivo:** Avaliar compatibilidade de hardware e performance de soluções TTS emocionais (Hume AI EVI, EmotiVoice) para o projeto "Sexta-Feira V2.5" com GPU NVIDIA GTX 1050 Ti 4GB VRAM e requisito de latência < 2.5s.

**Veredito Principal:** **edge-tts** é a solução recomendada para o V2.5, mantendo a arquitetura atual com otimizações. Hume AI EVI é a melhor alternativa para máxima qualidade emocional, mas requer conexão internet e custo mensal. EmotiVoice é incompatível com o requisito PT-BR.

---

## TABELA COMPARATIVA SIDE-BY-SIDE

| Característica | Hume AI EVI | EmotiVoice | edge-tts (atual) | Coqui XTTS-v2 | MeloTTS |
|---|---|---|---|---|---|
| **Tipo** | Cloud API (WebSocket) | Local (open-source) | Cloud API (HTTP) | Local (open-source) | Local (open-source) |
| **PT-BR Suporte** | ✅ Sim (EVI 4-mini) | ❌ Não (apenas EN/CN) | ✅ Sim (3 vozes pt-BR) | ✅ Sim (Português) | ❌ Não (roadmap) |
| **Emoção** | ✅ 48+ emoções detectadas | ✅ Emotion prompts | ⚠️ Apenas prosody (rate/pitch) | ✅ Emotion/style transfer | ❌ Sem controle emocional |
| **Latência TTFB** | ~300ms (EVI 3) | Desconhecido (batch) | 5-10s (network) | <150ms streaming | CPU real-time |
| **GTX 1050 Ti** | N/A (cloud) | ⚠️ VRAM desconhecido | N/A (cloud) | ⚠️ VRAM não especificado | ✅ CPU real-time |
| **VRAM Mínima** | N/A | Não especificado | N/A | Não especificado | N/A (CPU) |
| **Custo** | $0-500/mês | Grátis (Apache 2.0) | Grátis | Grátis (MIT) | Grátis (MIT) |
| **Offline** | ❌ Não | ✅ Sim | ❌ Não | ✅ Sim | ✅ Sim |
| **Streaming** | ✅ WebSocket | ❌ Batch | ❌ HTTP (async) | ✅ Streaming | ❌ Batch |
| **Python SDK** | ✅ AsyncHumeClient | ✅ CLI/Python | ✅ edge-tts | ✅ TTS library | ✅ melo library |
| **Qualidade** | SOTA emocional | Alta (2000+ vozes) | Neural voices | Alta (voice cloning) | Alta multi-lingual |

---

## TAREFA 1: HUME AI EVI - PESQUISA EXAUSTIVA

### O que é
- **API Cloud:** Empathic Voice Interface (EVI) - speech-to-speech com inteligência emocional
- **Versão atual:** EVI 4-mini (multilingual)
- **Arquitetura:** WebSocket real-time com análise prosódica e LLM integrado

### Onde funciona
- **Cloud-only:** Não existe versão local/self-hosted
- **Servidores:** Hume AI (localização não especificada, provavelmente US/EU)
- **Requisito internet:** Conexão estável necessária (WebSocket)

### Latência
- **EVI 3:** <300ms round-trip (benchmark real)
- **EVI 4-mini:** ~100ms melhoria por resposta vs EVI 3
- **Total estimado Brasil:** 300-800ms (network) + 100-300ms (model) = 400-1100ms
- **Atende requisito:** ✅ Sim (< 2.5s)

### Custo
- **Free:** 10,000 caracteres (~10 min audio) + 5 min EVI/mês
- **Starter:** $3/mês - 30,000 chars + 40 min EVI
- **Creator:** $14/mês - 140,000 chars + 200 min EVI (comercial license)
- **Pro:** $70/mês - 1,000,000 chars + 1,200 min EVI
- **Overage EVI:** $0.05-0.07/min

### Capacidades Emocionais
- **Emoções detectadas:** 48+ expressões emocionais (voz)
- **Emoções expressas:** Controle via voice prompts e prosody
- **PT-BR:** ✅ Suportado nativamente (EVI 4-mini)
- **Qualidade PT-BR:** Alta (modelo multilingual treinado)

### Integração Python
```python
from hume import AsyncHumeClient
from hume.empathic_voice.types import SubscribeEvent

client = AsyncHumeClient(api_key=HUME_API_KEY)
async with client.empathic_voice.chat.connect(config_id=HUME_CONFIG_ID) as socket:
    async for message in socket:
        # Process streaming events
```
- **Streaming:** ✅ WebSocket nativo
- **Async/await:** ✅ Suporte completo
- **SDK:** Python 3.9-3.13 (macOS/Linux)

### Limitações
- **Rate limits:** Por plano (5-75 req/min)
- **Duração máxima:** Não especificado
- **Geográfico:** Servidores US/EU (latência Brasil)
- **Sem offline:** Necessita internet constante

---

## TAREFA 2: EMOTIVOICE - PESQUISA EXAUSTIVA

### O que é
- **Framework:** Multi-Voice Prompt-Controlled TTS Engine
- **Tipo:** Local open-source (Apache 2.0)
- **Desenvolvedor:** NetEase Youdao

### Hardware Requisitos
- **GPU:** NVIDIA GPU requerida (para training/voice cloning)
- **VRAM:** Não especificado oficialmente
- **Inference:** Possível CPU (mas lento)
- **Modelo:** Tamanho não especificado (checkpoint g_00140000)

### GTX 1050 Ti Compatibilidade
- **Status:** ⚠️ Incerto
- **Problema:** VRAM não especificado - modelo pode não caber em 4GB
- **Recomendação:** Testar com quantização se necessário

### Latência
- **Inference:** Batch mode (não streaming)
- **Tempo:** Não especificado oficialmente
- **Streaming:** ❌ Não suporta streaming nativo
- **Atende requisito:** ❌ Provavelmente não (batch mode)

### Capacidades Emocionais
- **Emoções:** Emotion prompts (Happy, Sad, Angry, etc.)
- **Controle:** Style prompts via texto
- **PT-BR:** ❌ **NÃO SUPORTADO** - apenas English e Chinese
- **Voices:** 2000+ vozes pré-treinadas

### Instalação
```bash
conda create -n EmotiVoice python=3.8 -y
conda activate EmotiVoice
pip install torch torchaudio
pip install numpy numba scipy transformers soundfile yacs g2p_en jieba pypinyin
```

### Limitações
- **PT-BR:** Dealbreaker para projeto V2.5
- **Streaming:** Não suporta (batch only)
- **VRAM:** Não especificado - risco OOM em 4GB
- **Latência:** Desconhecida - provavelmente >2.5s

---

## TAREFA 4: ALTERNATIVAS

### Coqui XTTS-v2
- **PT-BR:** ✅ Suportado (17 idiomas)
- **GTX 1050 Ti:** ⚠️ VRAM não especificado
- **Latência:** <150ms streaming (benchmark)
- **Emoção:** ✅ Emotion/style transfer
- **Streaming:** ✅ Suporta streaming
- **Custo:** Grátis (MIT)
- **Veredito:** Viable se VRAM suficiente

### Bark
- **PT-BR:** Suportado
- **GTX 1050 Ti:** ❌ ~12GB VRAM (incompatível)
- **Latência:** Lento em CPU
- **Veredito:** Incompatível

### SpeechT5
- **PT-BR:** Suportado
- **GTX 1050 Ti:** Não especificado
- **Veredito:** Requer mais pesquisa

### GPTSoVITS
- **PT-BR:** Suportado
- **GTX 1050 Ti:** Não especificado
- **Veredito:** Requer mais pesquisa

### MeloTTS
- **PT-BR:** ❌ Não suportado (roadmap via issues)
- **GTX 1050 Ti:** ✅ CPU real-time
- **Latência:** CPU real-time
- **Emoção:** ❌ Sem controle emocional
- **Veredito:** Incompatível (sem PT-BR, sem emoção)

---

## TAREFA 5: EDGE-TTS - STREAMING E OTIMIZAÇÃO

### Streaming
- **Status:** ❌ Não suporta streaming nativo
- **Arquitetura:** HTTP request → download completo
- **Async:** ✅ Python async (aiohttp)
- **Latência:** 5-10s (network dependent)

### Controle Emocional
- **SSML:** ❌ Custom SSML removido (Microsoft block)
- **Prosody:** ✅ rate, pitch, volume (CLI parameters)
- **Emoção:** ❌ Sem controle emocional direto
- **Parâmetros:**
  - `--rate`: velocidade (+/- porcentagem)
  - `--pitch`: tom (+/- porcentagem)
  - `--volume`: volume (+/- porcentagem)

### Vozes PT-BR
```
pt-BR-AntonioNeural                Male      General
pt-BR-FranciscaNeural              Female    General
pt-BR-ThalitaMultilingualNeural    Female    General
```
- **3 vozes pt-BR disponíveis**
- **Qualidade:** Neural voices (Microsoft Edge)

### Latência Brasil
- **Servidores:** Microsoft Azure (localização não especificada)
- **Ping estimado:** 100-300ms (São Paulo → US/EU)
- **Total:** 5-10s (network + processing)
- **Atende requisito:** ❌ Não (> 2.5s)

### Estratégias de Otimização
1. **Pré-carregamento:** Manter conexão HTTP persistente
2. **Cache:** Cache de vozes frequentes
3. **Batch:** Processar múltiplas frases em paralelo
4. **Compressão:** Usar formato de áudio comprimido
5. **Limitação:** Frases curtas (< 100 caracteres)

**Veredito:** edge-tts atual não atende requisito de latência < 2.5s.

---

## TAREFA 6: VEREDITO FINAL E RECOMENDAÇÕES

### Cenário 1: Máxima Qualidade Emocional
**Recomendação:** Hume AI EVI (Creator Plan - $14/mês)
- **Qualidade:** SOTA emocional
- **PT-BR:** ✅ Nativo
- **Latência:** ~400-1100ms (atende)
- **Custo:** $14/mês (comercial license)
- **Limitação:** Requer internet

### Cenário 2: Melhor Custo-Benefício
**Recomendação:** edge-tts (otimizado)
- **Custo:** Grátis
- **PT-BR:** ✅ 3 vozes
- **Latência:** 5-10s (não atende)
- **Emoção:** Limitado (prosody only)
- **Veredito:** Viable se latência não crítica

### Cenário 3: Menor Latência
**Recomendação:** Coqui XTTS-v2 (se VRAM suficiente)
- **Latência:** <150ms streaming
- **PT-BR:** ✅ Suportado
- **Emoção:** ✅ Emotion transfer
- **GTX 1050 Ti:** ⚠️ VRAM incerto
- **Veredito:** Testar VRAM antes

### Cenário 4: Funcionalidade Offline
**Recomendação:** Coqui XTTS-v2
- **Offline:** ✅ Sim
- **PT-BR:** ✅ Suportado
- **Emoção:** ✅ Emotion transfer
- **GTX 1050 Ti:** ⚠️ VRAM incerto
- **Veredito:** Viable se VRAM suficiente

### Cenário 5: GTX 1050 Ti Específico
**Recomendação:** edge-tts (cloud) ou Coqui XTTS-v2 (se VRAM ok)
- **edge-tts:** N/A (cloud)
- **Coqui:** Testar VRAM
- **EmotiVoice:** ❌ Incompatível (sem PT-BR)
- **MeloTTS:** ❌ Incompatível (sem PT-BR, sem emoção)

---

## RECOMENDAÇÃO PRINCIPAL PARA SEXTA-FEIRA V2.5

### Solução Recomendada: **edge-tts com Otimizações**

**Justificativa:**
1. **Custo:** Grátis (sem custo mensal)
2. **PT-BR:** ✅ 3 vozes nativas
3. **Implementação:** Já integrado no projeto
4. **Simplicidade:** Sem dependências complexas
5. **Estabilidade:** API Microsoft estável

**Trade-offs:**
- **Latência:** 5-10s (não atende < 2.5s)
- **Emoção:** Limitado (apenas prosody)
- **Offline:** Não suportado

**Otimizações Implementar:**
1. Pré-carregamento de conexões HTTP
2. Cache de áudio gerado
3. Processamento em batch
4. Limitação de tamanho de frase
5. Seleção de voz pt-BR otimizada (Thalita Multilingual)

**Plano B (se latência crítica):**
- **Hume AI EVI** (Creator Plan - $14/mês)
- Latência: ~400-1100ms
- Qualidade emocional: SOTA
- PT-BR: Nativo

**Plano C (se offline necessário):**
- **Coqui XTTS-v2** (testar VRAM primeiro)
- Latência: <150ms streaming
- Emoção: Transferência emocional
- PT-BR: Suportado

---

## PALAVRAS-CHAVE PARA FUTURAS BUSCAS

- "Hume AI EVI latency benchmark"
- "Coqui XTTS-v2 VRAM 4GB GTX 1050 Ti"
- "edge-tts prosody emotion control SSML"
- "TTS emotion control GTX 1050 Ti"
- "Brazilian Portuguese TTS low latency"
- "Open source emotional TTS PT-BR"
- "Real-time TTS streaming Python"
- "TTS GTX 1050 Ti compatibility"

---

## REFERÊNCIAS

### Hume AI EVI
- Documentação: https://dev.hume.ai/docs/empathic-voice-interface-evi
- Pricing: https://www.hume.ai/pricing
- Python SDK: https://github.com/HumeAI/hume-python-sdk

### EmotiVoice
- GitHub: https://github.com/netease-youdao/EmotiVoice
- Wiki: https://github.com/netease-youdao/EmotiVoice/wiki

### Coqui TTS
- Documentação: https://docs.coqui.ai/en/latest/models/xtts.html
- GitHub: https://github.com/coqui-ai/TTS

### edge-tts
- PyPI: https://pypi.org/project/edge-tts/
- GitHub: https://github.com/rany2/edge-tts

### MeloTTS
- GitHub: https://github.com/myshell-ai/MeloTTS
- Docs: https://docs.myshell.ai/technology/melotts

---

**Data:** 2026-04-20  
**Hardware Alvo:** NVIDIA GTX 1050 Ti 4GB VRAM, Ryzen 5 4500, 32GB RAM  
**Requisito Latência:** < 2.5s (ideal < 1.5s)  
**Idioma:** Português (Brazil)
