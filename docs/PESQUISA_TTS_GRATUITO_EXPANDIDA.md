# PESQUISA EXPANDIDA: TTS EMOCIONAL GRATUITO COM ALTA QUALIDADE DE VOZ

**Objetivo:** Levantamento COMPLETO de TODAS as opções gratuitas de TTS emocional em 2024-2026 com foco em QUALIDADE DE VOZ (natural/humana), PT-BR, latência < 2.5s, e compatibilidade com GTX 1050 Ti 4GB VRAM.

**Requisito Crítico:** 100% GRATIS ou free tier extremamente generoso (não aceito planos que só funcionam bem pagando $14+/mês).

---

## TAREFA 1: CLOUD APIs COM FREE TIER GENEROSO OU GRATIS

### 1.1 ElevenLabs

- **Free tier:** 10,000 créditos/mês (~10,000 caracteres)
- **Se pago:** $5/mês (Starter) até $990/mês (Business)
- **Free tier eh suficiente para uso diario?** NÃO - 10k chars = ~10 min audio/mês. Uso pessoal (1-2h/dia = 300k-600k chars/mês) = precisa plano pago
- **PT-BR no free tier:** SIM (Portuguese Brazil e Portugal suportados)
- **Quality voz free tier:** 5/5 (SOTA qualidade, vozes ultra-realistas)
- **Latência:** 75-300ms (Flash v2.5 para 32 idiomas)
- **Emocao no free tier:** AVANCADO (audio tags: [curious] [crying] [mischievous] etc)
- **Veredito:** PRECISA PAGAR (free tier muito limitado para uso diário)

### 1.2 Azure Speech Services (Microsoft)

- **Free tier:** 500,000 caracteres/mês (F0 pricing tier)
- **Se pago:** Pay-as-you-go após free tier
- **Free tier eh suficiente para uso diario?** SIM - 500k chars/mês é generoso para uso pessoal
- **PT-BR no free tier:** SIM (Neural voices PT-BR disponíveis)
- **Quality voz free tier:** 4/5 (Neural voices de alta qualidade)
- **Latência:** 100-300ms (depende de região)
- **Emocao no free tier:** AVANCADO (SSML completo com prosody, emotion, style)
- **Veredito:** USAVEL GRATIS (free tier generoso + SSML emocional completo)

### 1.3 Google Cloud Text-to-Speech

- **Free tier:** 1 milhão caracteres/mês (WaveNet voices), 4 milhões (Standard voices)
- **Se pago:** Pay-as-you-go após free tier
- **Free tier eh suficiente para uso diario?** SIM - 1M chars WaveNet/mês é muito generoso
- **PT-BR no free tier:** SIM (WaveNet voices PT-BR disponíveis)
- **Quality voz free tier:** 4/5 (WaveNet voices de alta qualidade)
- **Latência:** 200-500ms (depende de região)
- **Emocao no free tier:** BASICO (SSML prosody limitado, sem controle emocional avançado)
- **Veredito:** USAVEL GRATIS (free tier muito generoso, qualidade alta)

### 1.4 Amazon Polly (AWS)

- **Free tier:** 100,000 caracteres/mês (Generative voices) por 12 meses para novos clientes
- **Se pago:** Pay-as-you-go após 12 meses
- **Free tier eh suficiente para uso diario?** NÃO - 100k chars/mês = ~100 min/mês. Insuficiente para uso diário intenso
- **PT-BR no free tier:** SIM (Neural voices PT-BR disponíveis)
- **Quality voz free tier:** 4/5 (Neural voices de alta qualidade)
- **Latência:** 150-400ms
- **Emocao no free tier:** BASICO (SSML prosody, sem controle emocional avançado)
- **Veredito:** PRECISA PAGAR (free tier limitado a 12 meses + quota baixa)

### 1.5 Play.ht

- **Free tier:** 12,500 caracteres/mês
- **Se pago:** $39/mês (Creator)
- **Free tier eh suficiente para uso diario?** NÃO - 12.5k chars/mês = ~12.5 min/mês. Muito limitado
- **PT-BR no free tier:** SIM (vozes PT-BR disponíveis)
- **Quality voz free tier:** 4/5 (Premium voices de alta qualidade)
- **Latência:** 200-500ms
- **Emocao no free tier:** BASICO (prosody control, sem emoção avançada)
- **Veredito:** PRECISA PAGAR (free tier muito limitado)

### 1.6 OpenAI TTS (tts-1 / tts-1-hd)

- **Free tier:** NÃO TEM (pago desde o início)
- **Se pago:** $0.015/1000 chars (tts-1), $0.030/1000 chars (tts-1-hd)
- **Custo estimado mensal:** ~$4.50-9.00 para 300k-600k chars/mês (uso pessoal)
- **PT-BR:** SIM (tts-1 suporta 80+ idiomas incluindo Português)
- **Quality voz:** 4/5 (tts-1-hd é alta qualidade, tts-1 é mais rápido)
- **Latência:** 200-400ms (tts-1 é mais rápido que tts-1-hd)
- **Emocao:** BASICO (sem controle emocional avançado, apenas vozes diferentes)
- **Veredito:** PRECISA PAGAR (não tem free tier, mas custo acessível ~$5-10/mês)

### 1.7 Fish.audio

- **Free tier:** "Free generations per month" (quantidade não especificada claramente)
- **Se pago:** $37.50/mês (Pro)
- **Free tier eh suficiente para uso diario?** TALVEZ (limites não claros, provavelmente insuficiente)
- **PT-BR no free tier:** SIM (suporta 70+ idiomas)
- **Quality voz free tier:** 4/5 (alta qualidade com emotion control)
- **Latência:** 200-500ms
- **Emocao no free tier:** AVANCADO (emotion control integrado)
- **Veredito:** TALVEZ USAVEL GRATIS (limites não claros, provavelmente insuficiente)

### 1.8 Cartesia.ai

- **Free tier:** 10,000 créditos (não especificado se é mensal ou total)
- **Se pago:** Não especificado claramente
- **Free tier eh suficiente para uso diario?** NÃO (10k créditos provavelmente insuficiente)
- **PT-BR no free tier:** SIM (15+ idiomas suportados)
- **Quality voz free tier:** 4/5 (alta qualidade, ultra-low latency 90ms)
- **Latência:** 90ms (Sonic model - ultra-low)
- **Emocao no free tier:** NÃO ESPECIFICADO
- **Veredito:** PRECISA PAGAR (free tier muito limitado)

---

## TAREFA 2: OPEN SOURCE LOCAL 100% GRATIS

### 2.1 MMS (Massively Multilingual Speech) - Meta/Facebook

- **Licenca:** MIT (open source)
- **100% gratis?** SIM (sem API key necessária)
- **PT-BR:** SIM (modelo específico: facebook/mms-tts-por)
- **Quality:** 3/5 (qualidade decente, mas não SOTA como ElevenLabs)
- **GTX 1050 Ti:** RODA (modelo VITS leve, VRAM não especificado mas provavelmente < 2GB)
- **Latencia local:** 500-1000ms (inferência batch, não streaming)
- **Emocao/estilo:** NENHUM (sem controle emocional)
- **Dificuldade instalacao:** FACIL (pip install transformers, huggingface)
- **Veredito:** RECOMENDACO MODERADA (gratis, PT-BR, GTX 1050 Ti compatível, mas sem emoção)

### 2.2 StyleTTS 2

- **Licenca:** MIT (open source)
- **100% gratis?** SIM (sem API key necessária)
- **PT-BR:** SIM (suporta multi-lingua incluindo Português)
- **Quality:** 4/5 (alta qualidade, "human-level TTS synthesis")
- **GTX 1050 Ti:** TESTAR (VRAM não especificado, depende de probe_batch_max)
- **Latencia local:** 1000-2000ms (diffusion model, lento)
- **Emocao/estilo:** AVANCADO (style diffusion, adversarial training, controle de estilo)
- **Dificuldade instalacao:** MEDIA (requer PyTorch, dependências complexas)
- **Veredito:** RECOMENDACO FORTE (se VRAM suficiente - qualidade alta + emoção)

### 2.3 ChatTTS

- **Licenca:** MIT (open source)
- **100% gratis?** SIM (sem API key necessária)
- **PT-BR:** SIM (suporta multi-lingua)
- **Quality:** 4/5 (otimizado para conversação, prosody superior)
- **GTX 1050 Ti:** TESTAR (VRAM não especificado)
- **Latencia local:** 500-1500ms (otimizado para diálogo, mas não streaming real-time)
- **Emocao/estilo:** AVANCADO (controle de laughter, pauses, interjections)
- **Dificuldade instalacao:** MEDIA (requer PyTorch, dependências)
- **Veredito:** RECOMENDACO FORTE (foco em conversação + prosody avançado)

### 2.4 CosyVoice (Alibaba)

- **Licenca:** Apache 2.0 (open source)
- **100% gratis?** SIM (sem API key necessária)
- **PT-BR:** NÃO (CosyVoice 3 suporta 9 idiomas: CN, EN, JP, KO, etc - sem PT-BR)
- **Quality:** 4/5 (alta qualidade, ultra-low latency 150ms)
- **GTX 1050 Ti:** RODA (0.5B parâmetros, leve)
- **Latencia local:** 150ms (ultra-low)
- **Emocao/estilo:** AVANCADO (voice cloning, emotion control)
- **Dificuldade instalacao:** MEDIA
- **Veredito:** DESCARTAR (sem PT-BR)

### 2.5 Spark TTS

- **Licenca:** Open source
- **100% gratis?** SIM (sem API key necessária)
- **PT-BR:** NÃO (apenas Chinês e Inglês)
- **Quality:** 5/5 (SOTA qualidade, supera CosyVoice2)
- **GTX 1050 Ti:** TESTAR (LLM-based, requer mais VRAM)
- **Latencia local:** Desconhecido
- **Emocao/estilo:** AVANCADO (voice cloning fantástico)
- **Dificuldade instalacao:** MEDIA
- **Veredito:** DESCARTAR (sem PT-BR)

### 2.6 Mini-Omni / Qwen3-Omni (Audio LLMs)

- **Licenca:** Open source
- **100% gratis?** SIM (sem API key necessária)
- **PT-BR:** SIM (Qwen3-Omni suporta 19 idiomas incluindo Português)
- **Quality:** 4/5 (multimodal LLM, alta qualidade)
- **GTX 1050 Ti:** NÃO RODA (requer GPU potente, 30B parâmetros)
- **Latencia local:** Desconhecido
- **Emocao/estilo:** AVANCADO (end-to-end speech, thinking while talking)
- **Dificuldade instalacao:** DIFICIL (requer vLLM, hardware potente)
- **Veredito:** DESCARTAR (incompatível GTX 1050 Ti)

### 2.7 MeloTTS (re-avaliação)

- **Licenca:** MIT (open source)
- **100% gratis?** SIM (sem API key necessária)
- **PT-BR:** NÃO (issues #7, #78, #244 - PT-BR em roadmap mas não implementado)
- **Quality:** 4/5 (alta qualidade multi-lingual)
- **GTX 1050 Ti:** RODA (CPU real-time)
- **Latencia local:** CPU real-time
- **Emocao/estilo:** NENHUM (sem controle emocional)
- **Dificuldade instalacao:** FACIL
- **Veredito:** DESCARTAR (sem PT-BR, sem emoção)

### 2.8 Post-processing de audio no edge-tts

- **Licenca:** N/A (bibliotecas open source: pydub, librosa, numpy, scipy)
- **100% gratis?** SIM (bibliotecas gratuitas)
- **PT-BR:** SIM (edge-tts já tem PT-BR)
- **Quality:** 3/5 (edge-tts base 4/5, processamento pode degradar qualidade)
- **GTX 1050 Ti:** RODA (CPU, ou GPU opcional para acelerar)
- **Latencia local:** 50-200ms (processamento adicional)
- **Emocao/estilo:** BASICO (pitch shifting, formant shifting, time stretching - simula emoção mas pode soar artificial)
- **Dificuldade instalacao:** FACIL (pip install pydub librosa)
- **Veredito:** RECOMENDACO MODERADA (viável se processamento não degradar qualidade muito)

### 2.9 Voice Conversion open source (OpenVoice)

- **Licenca:** MIT (open source)
- **100% gratis?** SIM (sem API key necessária)
- **PT-BR:** SIM (suporta multi-lingua incluindo Português)
- **Quality:** 4/5 (instant voice cloning, alta qualidade)
- **GTX 1050 Ti:** TESTAR (VRAM não especificado)
- **Latencia local:** 500-1500ms (voice cloning não é real-time)
- **Emocao/estilo:** AVANCADO (controle de emotion, accent, rhythm, pauses, intonation)
- **Dificuldade instalacao:** MEDIA
- **Veredito:** RECOMENDACO MODERADA (se VRAM suficiente - qualidade alta + emoção)

---

## TAREFA 3: SOLUÇÕES CRIATIVAS / HIBRIDAS GRATUITAS

### 3.1 edge-tts + processamento de audio local

- **Viabilidade:** ALTA (edge-tts já funciona, grátis, PT-BR, qualidade boa)
- **Efeitos de audio para emoção:**
  - Raiva: pitch +10-20%, speed +10-20%, intensidade aumentada
  - Tristeza: pitch -10-20%, speed -10-20%, reverb leve
  - Felicidade: pitch +20-30%, variação de rhythm, energy alta
  - Surpresa: pitch variando rápido, pausas
- **Bibliotecas Python:** pydub (edição simples), librosa (pitch shift, formant shift), numpy (processamento array), scipy (filtros)
- **Latencia adicional:** 50-200ms (processamento CPU)
- **Qualidade resultante:** 3/5 (pode soar artificial se over-processing)
- **Veredito:** VIÁVEL (mais realista que trocar de TTS, mas qualidade pode sofrer)

### 3.2 Multi-engine com seleção automática

- **Viabilidade:** MÉDIA (requer múltiplos TTS instalados, complexidade gerenciamento)
- **Engines grátis disponíveis:** edge-tts, MMS, StyleTTS 2, ChatTTS, OpenVoice
- **Lógica:** detectar emoção da resposta LLM → selecionar TTS apropriado
- **Qualidade:** Depende de cada engine
- **Complexidade:** ALTA (manter múltiplos engines, seleção automática)
- **Veredito:** POSSÍVEL mas complexo (não recomendado para simplicidade)

### 3.3 Fine-tuning de modelo TTS open source com voz gravada

- **Viabilidade:** BAIXA (requer dataset de voz, tempo de fine-tuning, conhecimento técnico)
- **Modelos base:** StyleTTS 2, MMS, OpenVoice
- **GTX 1050 Ti:** TESTAR (fine-tuning requer mais VRAM que inferência)
- **Tempo fine-tuning:** Horas a dias dependendo do dataset
- **Resultado:** Voz personalizada, gratuita, local
- **Veredito:** POSSÍVEL mas complexo (não recomendado para uso imediato)

---

## TAREFA 4: RANKING FINAL TOP 10 TTS GRATIS

Ordenado por QUALIDADE DE VOZ (melhor primeiro):

| Rank | Nome | Tipo | Quality (1-5) | PT-BR | Latência | Emocao | Realmente Gratis? | Veredito |
|---|---|---|---|---|---|---|---|---|
| 1 | Azure Speech Services (F0) | Cloud | 4/5 | SIM | 100-300ms | AVANCADO | SIM | **USAVEL GRATIS** |
| 2 | Google Cloud TTS (WaveNet) | Cloud | 4/5 | SIM | 200-500ms | BASICO | SIM | **USAVEL GRATIS** |
| 3 | StyleTTS 2 | Local | 4/5 | SIM | 1000-2000ms | AVANCADO | SIM | **RECOMENDACO FORTE** (se VRAM ok) |
| 4 | ChatTTS | Local | 4/5 | SIM | 500-1500ms | AVANCADO | SIM | **RECOMENDACO FORTE** (se VRAM ok) |
| 5 | OpenVoice | Local | 4/5 | SIM | 500-1500ms | AVANCADO | SIM | **RECOMENDACO MODERADA** (se VRAM ok) |
| 6 | MMS (Meta) | Local | 3/5 | SIM | 500-1000ms | NENHUM | SIM | **RECOMENDACO MODERADA** |
| 7 | edge-tts + post-processing | Híbrido | 3/5 | SIM | 5-10s + 50-200ms | BASICO | SIM | **VIÁVEL** |
| 8 | ElevenLabs | Cloud | 5/5 | SIM | 75-300ms | AVANCADO | NÃO | **PRECISA PAGAR** |
| 9 | OpenAI TTS | Cloud | 4/5 | SIM | 200-400ms | BASICO | NÃO | **PRECISA PAGAR** (acessível ~$5-10/mês) |
| 10 | Amazon Polly | Cloud | 4/5 | SIM | 150-400ms | BASICO | NÃO | **PRECISA PAGAR** (12 meses grátis + quota baixa) |

---

### TOP 3 CLOUD FREE TIER (precisa de internet mas grátis):

1. **Azure Speech Services (F0)** - 500k chars/mês, PT-BR Neural, SSML emocional completo
2. **Google Cloud TTS (WaveNet)** - 1M chars/mês, PT-BR WaveNet, qualidade alta
3. **Amazon Polly** - 100k chars/mês por 12 meses (limitado, mas grátis)

---

### TOP 3 LOCAL OPEN SOURCE (funciona offline, 100% gratis):

1. **StyleTTS 2** - Qualidade alta, emoção avançada, PT-BR (se VRAM suficiente)
2. **ChatTTS** - Foco conversação, prosody avançado, PT-BR (se VRAM suficiente)
3. **MMS (Meta)** - PT-BR específico, GTX 1050 Ti compatível, sem emoção

---

### TOP 3 IDEIAS CRIATIVAS (hibridas, pos-processamento):

1. **edge-tts + post-processing audio local** - Adicionar emoção via pitch shifting, formant shifting
2. **Multi-engine seleção por emoção** - Usar diferentes TTS para diferentes emoções
3. **Fine-tuning modelo open source** - Personalizar voz com gravações próprias

---

## RECOMENDAÇÃO FINAL PARA V2.5 (APENAS OPÇÕES GRATIS)

### Opção A: Unica solução gratis principal

**Recomendação:** **Azure Speech Services (F0 Free Tier)**

**Justificativa:**
- **Grátis:** 500,000 caracteres/mês (suficiente para uso pessoal intenso)
- **PT-BR:** Neural voices nativas de alta qualidade
- **Emoção:** SSML completo com prosody, emotion, style control
- **Latência:** 100-300ms (atende < 2.5s)
- **Qualidade:** 4/5 (Neural voices Microsoft)
- **Stabilidade:** Azure é enterprise-grade, muito estável

**Trade-offs:**
- Requer internet constante
- Requer conta Azure (gratuita)
- SSML requer implementação mais complexa

---

### Opção B: edge-tts + pos-processamento de audio para emoção

**Justificativa:**
- **Grátis:** 100% grátis, sem API key
- **PT-BR:** 3 vozes nativas (Antonio, Francisca, Thalita)
- **Simplicidade:** Já integrado no projeto
- **Emoção:** Adicionada via processamento local (pitch shifting, etc.)
- **Latência:** 5-10s (network) + 50-200ms (processamento) = NÃO atende < 2.5s

**Trade-offs:**
- Latência muito alta (5-10s)
- Qualidade pode degradar com over-processing
- Emoção simulada pode soar artificial

---

### Opção C: Multi-engine gratis com seleção por emoção

**Justificativa:**
- **Grátis:** Todos engines 100% grátis
- **Emoção:** Selecionar engine apropriado para cada emoção
- **PT-BR:** Múltiplos engines suportam PT-BR

**Trade-offs:**
- Complexidade muito alta (manter múltiplos engines)
- Latência varia por engine
- Difícil de gerenciar e manter

---

### Opção D: Local open source

**Recomendação:** **StyleTTS 2** (se VRAM GTX 1050 Ti suficiente) ou **MMS (Meta)** (fallback sem emoção)

**Justificativa:**
- **Grátis:** 100% grátis, offline
- **PT-BR:** Ambos suportam PT-BR
- **Emoção:** StyleTTS 2 tem controle avançado, MMS não
- **Latência:** 500-2000ms (local)

**Trade-offs:**
- StyleTTS 2: VRAM incerto em GTX 1050 Ti, latência alta
- MMS: Sem controle emocional
- Instalação mais complexa que cloud APIs

---

## ESCOLHA PRINCIPAL GRATUITA RECOMENDADA

### **Azure Speech Services (F0 Free Tier)**

**Por que:**
1. **Free tier generoso:** 500,000 caracteres/mês = ~8 horas de audio/mês (suficiente para uso pessoal intenso)
2. **PT-BR nativo:** Neural voices de alta qualidade específicas para Português Brasil
3. **Emoção avançada:** SSML completo com `<prosody>`, `<emotion>`, `<express-as>` tags
4. **Latência baixa:** 100-300ms (atende requisito < 2.5s facilmente)
5. **Estabilidade:** Azure é enterprise-grade, uptime 99.9%+
6. **Documentação:** Excelente documentação e SDK Python
7. **Custo zero:** Realmente grátis para uso pessoal (sem cartão de crédito necessário)

**Implementação:**
```python
import azure.cognitiveservices.speech as speechsdk

speech_config = speechsdk.SpeechConfig(
    subscription="AZURE_SPEECH_KEY",
    region="brazilsouth"
)
speech_config.speech_synthesis_voice_name = "pt-BR-FranciscaNeural"

# SSML com emoção
ssml = """
<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='pt-BR'>
    <voice name='pt-BR-FranciscaNeural'>
        <prosody rate='10%' pitch='10%'>
            <mstts:express-as style='cheerful'>
                Olá! Como você está hoje?
            </mstts:express-as>
        </prosody>
    </voice>
</speak>
"""
```

**Plano B (se Azure não for opção):**
- **Google Cloud TTS (WaveNet)** - 1M chars/mês grátis, qualidade alta, PT-BR
- **StyleTTS 2 local** - Se VRAM GTX 1050 Ti suficiente (testar primeiro)

---

**Data:** 2026-04-26  
**Hardware Alvo:** NVIDIA GTX 1050 Ti 4GB VRAM, Ryzen 5 4500, 32GB RAM  
**Requisito Latência:** < 2.5s (ideal < 1.5s)  
**Idioma:** Português (Brazil)  
**Custo:** 100% GRATIS (ou free tier extremamente generoso)
