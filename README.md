# Assistente Pessoal Desktop Proativo e Multimodal (V2)

Este repositório contém o código-fonte do **Assistente Pessoal Desktop Proativo e Multimodal (V2)**. Este assistente interage via voz e interface web (Dashboard), processa comandos locais, possui sistema de emoções em tempo real e reage proativamente ao contexto do usuário.

> **Nota:** Esta é a V2 — Dê uma olhada na [V1](https://github.com/RainMT-dv/Assistente-Pessoal-Desktop-Proativo-e-Multimodal).

---

## 🚀 Funcionalidades da V2

- **Transcrição de Voz Local (STT)**: Utiliza `faster-whisper` em tempo real com alta precisão e baixo consumo de recursos.
- **Síntese de Voz Natural (TTS)**: Integração com `edge-tts` para ter voz (Sim, é robotica infelismente), mas não tem custos de API.
- **Múltiplos Provedores de LLM**: Suporte para OpenRouter, Groq, Cerebras, DeepSeek, SiliconFlow, Nvidia NIM e modelos locais via Ollama com fallback inteligente. (Nunca cheguei a testar, na teoria funciona)
- **Personalidade Dinâmica & Emoções**: Sistema de estado emocional dinâmico baseado no contexto da conversa e perfil do usuário. 
- **Dashboard Web Interativo**: Interface desenvolvida em Flask com WebSockets para visualizar o estado atual da IA, transcrição em tempo real, expressões emocionais e histórico de logs.  <--- INCOMPLETO
- **Ações Locais (OS Bridge)**: Capaz de ler a tela, obter o texto da área de transferência e abrir aplicativos registrados localmente através de comandos de voz.
- **Comentários Proativos**: O assistente pode intervir e falar de forma autônoma com base no contexto do que o usuário está fazendo. (Simples)

---

## 🛠️ Pré-requisitos

Antes de iniciar, você precisará ter instalado em sua máquina:
1. **Python 3.10 ou superior** (Recomendado: **Python 3.12**).
2. Drivers NVIDIA CUDA e Toolkit (Opcional, mas altamente recomendado caso possua GPU dedicada para aceleração do Whisper).

---

## 📦 Instalação e Configuração

### 1. Clonar ou baixar o repositório
Baixe este repositório em sua máquina local.

### 2. Configurar o Ambiente Virtual e Dependências
Na pasta do projeto, há um script automatizado chamado `SETUP.bat`. Ele criará o ambiente virtual em uma pasta chamada `venv`, atualizará o gerenciador de pacotes `pip`, instalará o PyTorch com suporte a **CUDA 12.1** (com fallback automático para CPU caso não encontre GPU compatível), instalará todas as dependências do `requirements.txt` e fará o download do modelo Whisper Base padrão.

Basta dar dois cliques no arquivo:
```bash
SETUP.bat
```
**(Se ocorrer um erro, tente executar como administrador)**

Aguarde a finalização de todas as etapas.

### 3. Configurar as Chaves de API
1. Duplique ou renomeie o arquivo `.env.example` para `.env`:
   ```bash
   copy .env.example .env
   ```

2. Abra o arquivo `.env` com seu editor de texto preferido e adicione as suas chaves de API:
   - `OPENROUTER_API_KEY`: API Key do OpenRouter.
   - `GROQ_API_KEY`: API Key do Groq (muito rápida para respostas em milissegundos).
   - `CEREBRAS_API_KEY`: API Key do Cerebras.
   - `DEEPSEEK_API_KEY`: API Key do DeepSeek.
   - `SILICONFLOW_API_KEY`: API Key do SiliconFlow.
   - `NVIDIA_API_KEY`: API Key da Nvidia.
   - `OLLAMA_API_KEY`: Padrão: `ollama` para chamadas locais.

---

## 🏃 Como Executar

Com as dependências instaladas e o arquivo `.env` configurado, inicie o assistente dando dois cliques no arquivo:
```bash
RUN.bat
```
**(Se ocorrer um erro, tente executar como administrador)**


Após a inicialização do terminal:
1. O assistente iniciará o servidor do dashboard local.
2. Por padrão, você poderá acessar o painel de visualização pelo navegador em: [http://localhost:5000](http://localhost:5000).
3. Pressione a tecla configurada (ou use comandos de voz) para falar com a IA!

---

## 📂 Estrutura de Pastas

```text
├── cards/             # Elementos visuais e componentes do Dashboard
├── config/            # Arquivos de configurações (.json)
│   ├── apps.json             # Lista de caminhos para abrir apps pelo Windows
│   ├── settings.json         # Configurações gerais (STT, TTS, LLM, etc)
│   ├── brain.json            # Estado emocional atual da IA
│   └── slang_dictionary.json # Dicionário de gírias e expressões personalizadas
├── core/              # Lógica principal da aplicação (STT, TTS, LLM, OS Bridge, etc)
├── dashboard/         # Servidor web Flask e arquivos estáticos (HTML/CSS/JS)
├── data/              # Dados de memória persistente da IA
│   ├── memories.json         # Perfil do usuário e memórias coletadas
│   └── mood.json             # Histórico de humor
├── main.py            # Ponto de entrada do programa principal
├── REQUIREMENTS.txt   # Lista de dependências Python
├── SETUP.bat          # Instalação automatizada do ambiente virtual
├── RUN.bat            # Execução automatizada do assistente
└── .gitignore         # Arquivos ignorados pelo Git (.env, venv/, logs/, etc)
```
