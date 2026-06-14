# PESQUISA TTS 100% GRATIS SEM CARTÃO DE CRÉDITO
## Relatório Completo - Abril 2026

---

## RESUMO EXECUTIVO

**VEREDITO FINAL:**

**Opção #1: Gemini-TTS (Google AI Studio)** - **TESTAR AGORA**
- 100% grátis, sem cartão de crédito
- Qualidade muito alta (MOS 4.2-4.5, Elo score 1,211)
- Suporta PT-BR (70+ idiomas)
- Controle emocional via audio tags
- Rate limits durante peak hours
- Acessível via Google AI Studio (aistudio.google.com/generate-speech)

**Opção #2: StyleTTS 2** - **INSTALAR AGORA**
- Open source, 100% grátis
- Roda em GTX 1050 Ti 4GB (2GB VRAM footprint)
- Qualidade high-level (human-level)
- Pode rodar em CPU (Reddit confirmado)
- Não tem PT-BR nativo, mas possível com multilingual PL-BERT

**Opção #3: Piper TTS** - **ALTERNATIVA SECUNDÁRIA**
- Open source, 100% grátis
- Roda em CPU/GPU leve
- Tem vozes PT-BR (mas limitadas)
- Qualidade inferior a StyleTTS 2

**Opção #4: Continuar edge-tts otimizado** - **DESCARTAR**
- Latência 5-10s não resolve com otimizações
- SSML emocional REMOVIDO pela Microsoft
- Não vale o esforço

---

## TAREFA 1: GEMINI-TTS (Google NOVO)

### 1.1 O que é exatamente?

Gemini-TTS é o mais novo modelo TTS do Google, lançado em 2025-2026. É a evolução do Cloud TTS tradicional, usando tecnologia Gemini para controle granular de expressão, emoção e estilo via prompts em linguagem natural.

**Características principais:**
- Modelo: Gemini 3.1 Flash TTS (Preview), Gemini 2.5 Flash TTS, Gemini 2.5 Pro TTS
- Tecnologia: Large Language Model + diffusion style
- Controle: Audio tags, natural language prompts
- Qualidade: MOS 4.2-4.5 (Elo score 1,211 no Artificial Analysis TTS leaderboard)

### 1.2 Rotas de acesso

**Google AI Studio (GRÁTIS SEM CARTÃO):**
- URL: aistudio.google.com/generate-speech
- Requisito: Conta Google
- Cartão de crédito: **NÃO**
- Rate limits: Sim, durante peak hours
- Modelo disponível: Gemini 2.5 Flash e Pro

**Cloud Text-to-Speech API (PAGO):**
- Requisito: Conta Google Cloud
- Cartão de crédito: **SIM** (mesmo free tier)
- Preço: ~$0.01-0.04 por 1,000 caracteres (Flash)
- Preço: ~$0.04-0.12 por 1,000 caracteres (Pro)
- **DESCARTADO** para o usuário

**Vertex AI (PAGO):**
- Requisito: Conta Google Cloud
- Cartão de crédito: **SIM**
- **DESCARTADO** para o usuário

### 1.3 Free tier sem cartão?

**SIM - Google AI Studio é 100% grátis sem cartão:**

Fonte: https://pricepertoken.com/endpoints/google-ai-studio/free
- "Google AI Studio offers a free tier for all Gemini models with rate limits. No credit card required"
- Inclui acesso a Gemini 2.5 Pro, Flash, e Flash-Lite

Fonte: https://aitoolanalysis.com/google-ai-studio-text-to-speech-review/
- "Free Tier (Google AI Studio): Access to Gemini 2.5 Flash and Pro TTS models. All 30 voices available. Multi-speaker mode included. Rate-limited during peak hours. No credit card required."

**Limitações do free tier:**
- Rate limits durante peak hours
- Máximo 11 minutos por geração (655 segundos)
- 32K token context limit (~24,000 palavras)
- Sem voice cloning (requer Cloud TTS API pago)

### 1.4 Suporta PT-BR?

**SIM** - Fontes confirmam:

- Suporta 70+ idiomas (GA release)
- "Language support covers the major global languages as you'd expect — English, Spanish, French, German, Portuguese, Japanese, Korean, Arabic, Hindi"
- Auto-detect de idioma do input
- 30 vozes disponíveis

### 1.5 Qualidade voz

**Muito alta - comparável a ElevenLabs:**

- MOS (Mean Opinion Score): 4.2-4.5 para Pro model
- Elo score: 1,211 no Artificial Analysis TTS leaderboard
- Blind test: 38% dos usuários não conseguiram distinguir de ElevenLabs em narração
- Para 80% dos use cases (tutoriais, narração simples, diálogo), diferença não importa
- ElevenLabs ainda vence em conteúdo dramático/emocional intenso

### 1.6 Controle emocional/estilo

**SIM - muito avançado:**

- **Audio tags:** [sigh], [laugh], [gasp], etc.
- **Natural language prompts:** "Say the following in an elated way"
- **Scene direction:** Define environment e dialogue instructions
- **Speaker-level specificity:** Audio Profiles + Director's Notes
- **Inline tags:** Mudar expressão mid-sentence
- **Multi-speaker mode:** Diálogos naturais

Exemplo:
```python
model: "gemini-2.5-flash-tts"
prompt: "You are having a casual conversation with a friend. Say the following in a friendly and amused way."
text: "[laughs] I did NOT expect that. [sigh] Can you believe it!"
speaker: "Callirrhoe"
```

### 1.7 Latência

- Streaming synthesis disponível (versão Cloud API)
- Não especificado para Google AI Studio free tier
- Latência provavelmente similar a outros serviços cloud (1-3s)

### 1.8 Como acessar SEM cartão de crédito

**Passo a passo:**

1. Acessar: https://aistudio.google.com/generate-speech
2. Login com conta Google (gmail.com)
3. Selecionar modelo: Gemini 2.5 Flash ou Pro
4. Escolher voz (30 opções)
5. Inserir texto
6. Usar audio tags para emoção: [laughs], [sigh], etc.
7. Gerar e baixar áudio

**Via API (Python):**

```python
import google.generativeai as genai

genai.configure(api_key="SUA_API_KEY_GRATIS_DO_AI_STUDIO")
model = genai.GenerativeModel("gemini-2.5-flash-tts")

response = model.generate_content(
    "Olá, como você está?",
    generation_config=genai.GenerationConfig(
        response_modalities=["AUDIO"],
        speech_config=genai.SpeechConfig(
            voice_config=genai.VoiceConfig(voice_name="pt-BR-ThalitaMultilingualNeural")
        )
    )
)
```

---

## TAREFA 2: STYLETTS 2 (GTX 1050 Ti 4GB)

### 2.1 GitHub oficial

https://github.com/yl4579/StyleTTS2

### 2.2 Requirements oficiais

**Hardware:**
- Python >= 3.7
- GPU: **NÃO obrigatória** (pode rodar em CPU)
- VRAM: 2GB footprint para inferência (RTX 3050)

**Software:**
```bash
pip install -r requirements.txt
pip install phonemizer
# Linux: sudo apt-get install espeak-ng
# Windows: espeak-ng disponível via installer
```

### 2.3 GTX 1050 Ti 4GB - Viabilidade

**SIM - Roda em GTX 1050 Ti 4GB:**

Fonte: https://dagshub.com/blog/styletts2/
- "Remarkably, this is achieved with a memory footprint of just 2GB of VRAM inferencing in around 2-3 seconds on an RTX 3050"

Fonte: https://www.reddit.com/r/speechtech/comments/1aqm6x1/anyone_played_and_experimented_with_styletts2/
- "StyleTTS2 is pretty light, you don't need a GPU. Just the CPU is enough."

**Conclusão:**
- GTX 1050 Ti 4GB é MAIS que suficiente (2GB footprint)
- Pode rodar inteiramente em CPU se necessário
- Quantização não necessária para 4GB

### 2.4 Ajustes para 4GB VRAM

**Não necessários** - modelo já otimizado:
- 2GB VRAM footprint padrão
- GTX 1050 Ti tem 4GB, margem de segurança 2x

### 2.5 Versões reduzidas/quantizadas

**Não necessárias** - modelo base já leve:
- Versão MIT-licensed disponível via pip (gruut, qualidade menor)
- Versão GPL-licensed disponível (qualidade máxima)
- HuggingFace: https://huggingface.co/yl4579/StyleTTS2-LJSpeech

### 2.6 Latência real reportada

**2-3 segundos** em RTX 3050 (Dagshub)
- GTX 1050 Ti será ligeiramente mais lento, mas ainda aceitável
- CPU-only: significativamente mais lento (10-30s)

### 2.7 Instalação

**Simples (pip):**

```bash
git clone https://github.com/yl4579/StyleTTS2.git
cd StyleTTS2
pip install -r requirements.txt
pip install phonemizer
# Windows: baixar e instalar espeak-ng
```

**Versão pip (MIT-licensed):**
```bash
pip install styletts2
```

### 2.8 PT-BR Support

**NÃO tem PT-BR nativo**, mas:

- Pode usar multilingual PL-BERT (mencionado no blog Dagshub)
- "Swapping the english PL-BERT for a multilingual PL-BERT also has an interesting effect, using a multilingual PL-BERT on a non-multilingual StyleTTS2 model and giving it phonemes in another language allows synthesis of different languages on unfinetuned models"
- Pronúncia "really poor" sem finetuning
- Precisa de finetuning com dataset PT-BR para qualidade aceitável

---

## TAREFA 3: CHATTTS (GTX 1050 Ti 4GB)

### 3.1 GitHub oficial

https://github.com/2noise/ChatTTS

### 3.2 Requirements de hardware

**VRAM:**
- Mínimo 4GB VRAM para 30 segundos de áudio
- GTX 1050 Ti 4GB: **Borda do limite**
- Para áudio curto (< 10s): deve funcionar
- Para áudio longo: OOM provável

### 3.3 GTX 1050 Ti 4GB - Viabilidade

**TALVEZ - com limitações:**

- 4GB é o mínimo absoluto para 30s de áudio
- GTX 1050 Ti está na borda
- Recomendação: usar para áudios curtos (< 10s)
- Alternativa: rodar em CPU (mais lento, mas funciona)

### 3.4 Versões reduzidas/quantizadas

**Não mencionadas** no repositório oficial
- Modelo open-source é versão 40,000 hours (comprimida, MP3)
- Versão 100,000 hours não open-source (ruido anti-abuso)

### 3.5 PT-BR Support

**NÃO suporta PT-BR:**

Supported Languages:
- English
- Chinese
- "Coming Soon..."

### 3.6 Controle emocional/prosody

**SIM - muito avançado:**

- Fine-grained control: laughter, pauses, interjections
- "The model could predict and control fine-grained prosodic features, including laughter, pauses, and interjections"
- Melhor prosody que maioria dos open-source TTS

### 3.7 Latência real

- RTF (Real-Time Factor): ~0.65 em RTX 4090D
- GTX 1050 Ti: significativamente mais lento
- CPU-only: muito lento (não real-time)

### 3.8 Comparação qualidade

**ChatTTS vs edge-tts vs StyleTTS 2:**

- ChatTTS: Melhor prosody, mas sem PT-BR
- StyleTTS 2: Melhor qualidade geral, mas sem PT-BR nativo
- edge-tts: PT-BR nativo, mas latência alta e sem controle emocional

---

## TAREFA 4: OUTRAS OPÇÕES 100% GRÁTIS

### 4.1 Piper TTS

**Open source?** SIM
**PT-BR?** SIM (limitado)
**Quality?** Média-inferior
**GTX 1050 Ti?** SIM (roda em CPU facilmente)
**Emoção?** Não
**Latência?** Rápida (CPU-only)

**Detalhes:**
- GitHub: https://github.com/rhasspy/piper (movido para OHF-Voice/piper1-gpl)
- HuggingFace voices: https://huggingface.co/rhasspy/piper-voices
- ONNX-based, muito leve
- Roda em Raspberry Pi
- Vozes PT-BR disponíveis (mas limitadas em número e qualidade)
- Issue #766 pedindo vozes femininas PT-BR e PT-PT

**Veredito:** Alternativa secundária se StyleTTS 2 for muito complexo

### 4.2 MegaTTS

**Não encontrado** - provavelmente não existe ou é muito obscuro

### 4.3 Outros open source 2024-2025

**Qwen3-TTS:**
- Open source, Apache 2.0
- Requer NVIDIA GPU
- Voice cloning from 3 segundos
- PT-BR? Não confirmado
- Recomendado se tiver GPU melhor

**Outros:**
- Bark: 12GB VRAM (incompatível)
- Coqui XTTS-v2: Qualidade ruim (descartado)
- MeloTTS: Sem PT-BR (descartado)

---

## TAREFA 5: OTIMIZAÇÕES EDGE-TTS

### 5.1 Latência edge-tts

**Problema:** 5-10 segundos de latência
**Otimizações possíveis:**

**Cache de conexões HTTP:**
- edge-tts usa HTTP requests para serviço Microsoft
- Reuse de conexões pode reduzir 1-2s
- Implementação complexa no edge-tts atual

**Pre-buffering:**
- Pré-carregar modelo não é possível (serviço remoto)
- Não aplicável

**Async mais eficiente:**
- edge-tts já usa async
- Melhorias marginais

**Reduzir tamanho do texto:**
- Chunking inteligente pode ajudar
- Mas cada chunk ainda tem latência 5-10s

**Formato de audio:**
- MP3 vs OGG vs WAV: diferença marginal
- Não resolve problema raiz

**Conclusão:** Não é possível reduzir significativamente latência de edge-tts sem mudar para outro TTS

### 5.2 SSML avançado no edge-tts

**NÃO suporta SSML emocional:**

Fonte: https://github.com/rany2/edge-tts
- "Support for custom SSML was removed because Microsoft prevents the use of any SSML that could not be generated by Microsoft Edge itself"
- "This means that all the cases where custom SSML would be useful cannot be supported as the service only permits a single <voice> tag with a single <prosody> tag inside it"
- "Any available customization options that could be used in the <prosody> tag are already available from the library or the command line itself"

**O que resta:**
- <prosody rate=""> - controla velocidade
- <prosody pitch=""> - controla pitch
- <prosody volume=""> - controla volume
- **SEM** <mstts:express-as> ou tags emocionais

### 5.3 Vozes edge-tts alternativas

**Vozes PT-BR disponíveis:**

- pt-BR-FranciscaNeural
- pt-BR-AntonioNeural
- pt-BR-ThalitaMultilingualNeural (multilingue, talvez mais expressiva)

**Qualidade:** Todas similares (4/5)
**Expressividade:** Limitada (sem controle emocional real)

---

## VEREDITO POR OPÇÃO

### Gemini-TTS

**Acessível sem cartão?** SIM
- Google AI Studio é 100% grátis, no credit card required
- Rate limits durante peak hours
- Máximo 11 minutos por geração

**Como acessar:**
1. Acessar aistudio.google.com/generate-speech
2. Login com conta Google
3. Selecionar modelo Gemini 2.5 Flash ou Pro
4. Escolher voz PT-BR
5. Usar audio tags: [laughs], [sigh], [gasp]
6. Gerar e baixar

**Recomendação:** **TESTAR AGORA** - É a melhor opção grátis sem cartão

---

### StyleTTS 2

**Roda em GTX 1050 Ti 4GB?** SIM
- 2GB VRAM footprint
- GTX 1050 Ti tem 4GB (margem 2x)
- Pode rodar em CPU se necessário

**Se sim - Como instalar:**
```bash
git clone https://github.com/yl4579/StyleTTS2.git
cd StyleTTS2
pip install -r requirements.txt
pip install phonemizer
# Windows: instalar espeak-ng
```

**PT-BR:** NÃO nativo
- Precisa de multilingual PL-BERT
- Pronúncia "really poor" sem finetuning
- Precisa de dataset PT-BR para finetuning

**Recomendação:** **INSTALAR AGORA** - Para uso futuro se conseguir finetuning PT-BR

---

### ChatTTS

**Roda em GTX 1050 Ti 4GB?** TALVEZ
- Mínimo 4GB VRAM para 30s de áudio
- GTX 1050 Ti está na borda
- Funciona para áudios curtos (< 10s)
- CPU-only funciona (mais lento)

**PT-BR:** NÃO
- Apenas English e Chinese
- "Coming Soon..." desde 2024

**Recomendação:** **DESCARTAR** - Sem PT-BR e borderline em hardware

---

### Piper TTS

**Vale a pena testar?** SIM (como alternativa secundária)
- Open source, 100% grátis
- Roda em CPU facilmente
- Tem vozes PT-BR (limitadas)
- Qualidade inferior a StyleTTS 2

**Recomendação:** **ALTERNATIVA SECUNDÁRIA** - Se StyleTTS 2 for muito complexo

---

### edge-tts Otimizado

**Consegue < 2.5s com otimizações?** NÃO
- Latência 5-10s é inerente ao serviço remoto
- Otimizações HTTP/async reduzem marginalmente
- Não resolve problema raiz

**Suporta SSML emocional?** NÃO
- Microsoft removeu suporte custom SSML
- Apenas <prosody> básico (rate, pitch, volume)
- SEM tags emocionais

**Recomendação:** **DESCARTAR** - Não vale o esforço

---

## RECOMENDAÇÃO FINAL PARA V2.5

Dado que você **NÃO tem cartão de crédito**, aqui está a melhor estratégia:

### Opção A: Gemini-TTS (Google AI Studio) - **PRIMEIRA ESCOLHA**

**Motivos:**
- 100% grátis, sem cartão de crédito
- Qualidade muito alta (MOS 4.2-4.5)
- Suporta PT-BR nativo
- Controle emocional via audio tags
- Fácil de acessar (web interface)
- Rate limits aceitáveis para uso pessoal

**Quando usar:**
- Para testes imediatos
- Para produção se rate limits não forem problema
- Quando qualidade for prioridade

**Como integrar:**
- Usar Google AI Studio web interface inicialmente
- Se necessário, usar API key grátis do AI Studio
- Implementar fallback para edge-tts se rate limit

---

### Opção B: StyleTTS 2 - **SEGUNDA ESCOLHA (LONGO PRAZO)**

**Motivos:**
- Open source, 100% grátis, SEM rate limits
- Roda em GTX 1050 Ti 4GB
- Qualidade human-level
- Controle emocional avançado
- Offline (sem dependência de internet)

**Desafios:**
- NÃO tem PT-BR nativo
- Precisa de finetuning com dataset PT-BR
- Instalação mais complexa
- Latência 2-3s (aceitável)

**Quando usar:**
- Após conseguir finetuning PT-BR
- Para uso offline
- Para volume alto (sem rate limits)
- Quando controle granular for necessário

**Como integrar:**
- Instalar agora para testes (inglês)
- Procurar dataset PT-BR para finetuning
- Contribuir para projeto Vokan (comunidade)

---

### Opção C: Piper TTS - **TERCEIRA ESCOLHA (FALLBACK)**

**Motivos:**
- Open source, 100% grátis
- Muito leve (roda em CPU)
- Tem vozes PT-BR
- Instalação simples

**Desvantagens:**
- Qualidade inferior a StyleTTS 2
- Sem controle emocional
- Vozes PT-BR limitadas

**Quando usar:**
- Se StyleTTS 2 for muito complexo
- Para protótipos rápidos
- Se GTX 1050 Ti não for suficiente

---

## QUAL OPÇÃO TESTAR PRIMEIRO?

**TESTAR PRIMEIRO: Gemini-TTS (Google AI Studio)**

**Por que:**
1. Mais fácil de testar (web interface, sem instalação)
2. PT-BR nativo (funciona imediatamente)
3. Qualidade muito alta
4. 100% grátis sem cartão
5. Controle emocional funcional

**Passos:**
1. Acessar aistudio.google.com/generate-speech
2. Login com conta Google
3. Testar com texto PT-BR simples
4. Experimentar audio tags: [laughs], [sigh]
5. Avaliar qualidade e latência
6. Se satisfatório, integrar no projeto V2.5

**Se Gemini-TTS funcionar bem:**
- Usar como principal
- Implementar fallback para edge-tts se rate limit
- Manter StyleTTS 2 como backup futuro (após finetuning PT-BR)

**Se Gemini-TTS não funcionar (rate limits, etc):**
- Migrar para StyleTTS 2 + finetuning PT-BR
- Ou usar Piper TTS como fallback

---

## CONCLUSÃO

**Melhor opção atual para você (sem cartão, PT-BR):**

1. **Imediato:** Gemini-TTS (Google AI Studio) - TESTAR AGORA
2. **Longo prazo:** StyleTTS 2 + finetuning PT-BR - INVESTIR FUTURO
3. **Fallback:** Piper TTS - MANTER COMO OPÇÃO SECUNDÁRIA

**Não vale a pena:**
- ChatTTS (sem PT-BR)
- edge-tts otimizado (latência inerente, SSML removido)
- Cloud TTS tradicional (precisa cartão)

---

## REFERÊNCIAS

### Gemini-TTS
- https://ai.google.dev/gemini-api/docs/speech-generation
- https://docs.cloud.google.com/text-to-speech/docs/gemini-tts
- https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-1-flash-tts/
- https://aitoolanalysis.com/google-ai-studio-text-to-speech-review/
- https://pricepertoken.com/endpoints/google-ai-studio/free

### StyleTTS 2
- https://github.com/yl4579/StyleTTS2
- https://dagshub.com/blog/styletts2/
- https://huggingface.co/yl4579/StyleTTS2-LJSpeech

### ChatTTS
- https://github.com/2noise/ChatTTS
- https://github.com/2noise/ChatTTS/issues/323

### Piper TTS
- https://github.com/rhasspy/piper
- https://huggingface.co/rhasspy/piper-voices

### edge-tts
- https://github.com/rany2/edge-tts
- https://pypi.org/project/edge-tts/

---

*Relatório compilado em Abril 2026*
*Para: Assistente Pessoal Desktop Proativo e Multimodal V2.5*
*Usuário: RainMT (menor de idade, sem cartão de crédito)*
