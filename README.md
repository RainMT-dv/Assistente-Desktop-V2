<div align="center">

  # Assistente Desktop V2
  *Assistente pessoal de IA proativo com voz, emoções e dashboard web*

  [![Python](https://img.shields.io/badge/Python-3.10+-3776ab?style=flat-square)](https://python.org)
  [![Whisper](https://img.shields.io/badge/STT-faster--whisper-orange?style=flat-square)](https://github.com/SYSTRAN/faster-whisper)
  [![Edge TTS](https://img.shields.io/badge/TTS-edge--tts-blue?style=flat-square)](https://github.com/rany2/edge-tts)
  [![Licença](https://img.shields.io/badge/licença-MIT-blue?style=flat-square)](LICENSE)

  [Funcionalidades](#funcionalidades) • [Primeiros passos](#primeiros-passos) • [Como executar](#como-executar) • [Estrutura](#estrutura-de-pastas)

</div>

---

> [!WARNING]
> Este projeto está **incompleto**. Algumas funcionalidades descritas aqui funcionam na teoria mas não foram totalmente testadas. Veja a [V1](https://github.com/RainMT-dv/Assistente-Desktop-V1) para uma versão mais simples e estável.

Assistente de desktop com interação por voz, personalidade dinâmica com estado emocional e um dashboard web em tempo real. Suporta múltiplos provedores de LLM e é capaz de executar ações no sistema operacional por comando de voz.

## Funcionalidades

- **Transcrição de voz local (STT)** via `faster-whisper` — rápido e sem custo de API
- **Síntese de voz (TTS)** com `edge-tts` — sem custo de API
- **Múltiplos provedores de LLM** com fallback inteligente: OpenRouter, Groq, Cerebras, DeepSeek, SiliconFlow, Nvidia NIM e modelos locais via Ollama
- **Personalidade e emoções dinâmicas** baseadas no contexto da conversa e perfil do usuário
- **Dashboard web** em Flask com WebSockets para estado da IA, transcrição em tempo real e histórico *(incompleto)*
- **Ações locais (OS Bridge)** — ler tela, área de transferência e abrir aplicativos por voz
- **Comentários proativos** — o assistente pode falar de forma autônoma com base no contexto

## Primeiros passos

### Requisitos

- Python 3.10+ (recomendado: **Python 3.12**)
- Drivers NVIDIA CUDA *(opcional, mas recomendado para acelerar o Whisper em GPU)*

### Instalação

**1. Clone o repositório**

```bash
git clone https://github.com/RainMT-dv/Assistente-Desktop-V2.git
cd Assistente-Desktop-V2
```

**2. Configure o ambiente e instale as dependências**

Dê dois cliques em `SETUP.bat` — ele cria o ambiente virtual, instala o PyTorch com suporte a CUDA 12.1 (com fallback para CPU) e baixa o modelo Whisper Base.

```
SETUP.bat
```

> [!TIP]
> Se ocorrer um erro, tente executar como administrador.

**3. Configure as chaves de API**

Duplique o `.env.example` e renomeie para `.env`:

```bash
copy .env.example .env
```

Abra o `.env` e adicione as chaves dos provedores que quiser usar:

| Variável | Provedor |
|---|---|
| `OPENROUTER_API_KEY` | OpenRouter |
| `GROQ_API_KEY` | Groq |
| `CEREBRAS_API_KEY` | Cerebras |
| `DEEPSEEK_API_KEY` | DeepSeek |
| `SILICONFLOW_API_KEY` | SiliconFlow |
| `NVIDIA_API_KEY` | Nvidia NIM |
| `OLLAMA_API_KEY` | Ollama (padrão: `ollama`) |

## Como executar

Com o `.env` configurado, dê dois cliques em `RUN.bat`:

```
RUN.bat
```

O assistente iniciará o servidor do dashboard. Acesse [http://localhost:5000](http://localhost:5000) no navegador para visualizar o painel.

## Estrutura de pastas

```
├── cards/             # Componentes visuais do dashboard
├── config/
│   ├── apps.json             # Caminhos dos apps para abrir por voz
│   ├── settings.json         # Configurações gerais (STT, TTS, LLM...)
│   ├── brain.json            # Estado emocional atual da IA
│   └── slang_dictionary.json # Dicionário de gírias personalizadas
├── core/              # Lógica principal (STT, TTS, LLM, OS Bridge...)
├── dashboard/         # Servidor Flask e arquivos estáticos
├── data/
│   ├── memories.json         # Perfil e memórias do usuário
│   └── mood.json             # Histórico de humor
├── main.py            # Ponto de entrada
├── requirements.txt
├── SETUP.bat          # Instalação automatizada
└── RUN.bat            # Execução automatizada
```

## Contribuindo

Sinta-se à vontade para modificar e melhorar! Crie um fork e publique as suas mudanças.
