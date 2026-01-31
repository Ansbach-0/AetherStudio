# 🎙️ Voice Cloning SaaS

> Plataforma de clonagem e conversão de voz com qualidade profissional usando F5-TTS e RVC.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## ✨ Features

- 🎙️ **Voice Cloning** - Clone qualquer voz com apenas 6 segundos de áudio
- 🔄 **Voice Conversion** - Converta sua voz para outra em tempo real
- 🌐 **Multi-idioma** - Suporte a PT, EN, ES e mais 6 idiomas
- 😊 **Controle Emocional** - 8 estilos emocionais (happy, sad, angry, etc.)
- 💳 **Sistema de Créditos** - Monetização integrada (Mercado Pago)
- ⚡ **Cache Inteligente** - Cache LRU para respostas rápidas
- 🔔 **Webhooks** - Notificações em tempo real
- 📊 **Dashboard API** - Documentação interativa

## 🚀 Quick Start

### Pré-requisitos

- Python 3.10+ (recomendado: Miniconda/Anaconda)
- Node.js/Bun para frontend
- CUDA/ROCm (opcional, para GPU AMD/NVIDIA)
- FFmpeg (para processamento de áudio)

### Instalação Backend

```bash
# Clonar repositório
git clone https://github.com/seu-usuario/voice-cloning-saas.git
cd voice-cloning-saas

# Criar ambiente conda (recomendado)
conda create -n voicecloner python=3.11
conda activate voicecloner

# Instalar dependências
pip install -r requirements.txt

# Para GPU AMD (ROCm):
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.2

# Para GPU NVIDIA (CUDA):
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### Instalação Frontend

```bash
# Instalar Bun (se não tiver)
irm bun.sh/install.ps1 | iex   # Windows PowerShell
# ou: curl -fsSL https://bun.sh/install | bash  # Linux/Mac

# Instalar dependências
bun install
```

### Iniciar Desenvolvimento

```bash
# Opção 1: Script automático (recomendado)
.\dev.ps1

# Opção 2: Manual
# Terminal 1 - Backend:
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2 - Frontend:
bun run dev
```

**URLs:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## ⚠️ Development Quirks (IMPORTANTE PARA AGENTES/DEVS)

### Caminhos Específicos do Ambiente

Este projeto foi desenvolvido em ambiente Windows com Miniconda. Os agentes de IA e desenvolvedores devem usar os seguintes caminhos:

#### Python (Conda Environment)
```powershell
# Executável Python do ambiente 'voicecloner'
C:\Users\minei\miniconda3\envs\voicecloner\python.exe

# Exemplo de uso:
& "C:\Users\minei\miniconda3\envs\voicecloner\python.exe" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

# Instalar pacotes com uv (mais rápido):
& "C:\Users\minei\miniconda3\envs\voicecloner\python.exe" -m uv pip install <pacote>

# Ou com pip padrão:
& "C:\Users\minei\miniconda3\envs\voicecloner\python.exe" -m pip install <pacote>
```

#### Bun (JavaScript Runtime)
```powershell
# Executável Bun
$env:USERPROFILE\.bun\bin\bun.exe
# Expande para: C:\Users\minei\.bun\bin\bun.exe

# Exemplo de uso:
& "$env:USERPROFILE\.bun\bin\bun" install
& "$env:USERPROFILE\.bun\bin\bun" run dev
```

### Problemas Conhecidos e Soluções

#### 1. Cache Python (.pyc) não atualiza
```powershell
# Se mudanças no código não refletirem, limpar cache:
Remove-Item -Recurse -Force "backend\**\__pycache__" -ErrorAction SilentlyContinue

# Reiniciar backend SEM --reload para teste:
& "C:\Users\minei\miniconda3\envs\voicecloner\python.exe" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

#### 2. Porta em uso (8000 ou 5173)
```powershell
# Verificar e matar processos nas portas:
Get-NetTCPConnection -LocalPort 8000,5173 -State Listen -ErrorAction SilentlyContinue | 
  ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

#### 3. Dependências não instaladas
```powershell
# Instalar todas as dependências de uma vez:
& "C:\Users\minei\miniconda3\envs\voicecloner\python.exe" -m pip install -r requirements.txt

# Dependências essenciais mínimas (se requirements.txt falhar):
& "C:\Users\minei\miniconda3\envs\voicecloner\python.exe" -m pip install fastapi uvicorn python-multipart pydub soundfile sqlalchemy aiosqlite pydantic pydantic-settings python-dotenv structlog slowapi httpx aiofiles langdetect numpy scipy
```

#### 4. Frontend mostra "Offline" 
- Verificar se backend está rodando: `curl.exe -s http://localhost:8000/health`
- O frontend espera o endpoint `/health` (não `/api/v1/health`)

#### 5. Sistema de Pagamentos em Manutenção
- Normal se `MERCADOPAGO_ACCESS_TOKEN` não estiver configurado
- Log mostra: `🚧 MODO MANUTENÇÃO: Sistema de pagamentos desativado`
- Configure no `.env` para ativar pagamentos

### Estrutura de Diretórios Criados Automaticamente

```
VoiceCloner/
├── uploads/          # Arquivos de áudio enviados (criado no startup)
├── outputs/          # Áudios gerados
│   └── cache/        # Cache de áudios frequentes
└── models/           # Checkpoints ML (F5-TTS, RVC)
```

### Variáveis de Ambiente (.env)

```env
# Aplicação
DEBUG=true
SECRET_KEY=desenvolvimento-apenas-mude-em-producao

# Diretórios (opcional - usa padrões se não definido)
UPLOAD_DIR=uploads
OUTPUT_DIR=outputs
MODELS_DIR=models

# GPU (opcional)
GPU_DEVICE=cuda:0

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60

# Cache
CACHE_MAX_SIZE=50
CACHE_TTL_SECONDS=3600

# Mercado Pago (deixe vazio para modo manutenção)
MERCADOPAGO_ACCESS_TOKEN=
```

---

## 📚 API Endpoints

### Health & Status

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/health` | Health check básico |
| GET | `/health/detailed` | Status detalhado com GPU e cache |
| GET | `/health/gpu` | Informações da GPU |
| GET | `/health/ready` | Readiness check |

### Voice Cloning

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/voice/clone` | Clonar voz |
| POST | `/api/v1/voice/clone-async` | Clonar voz (background) |
| POST | `/api/v1/voice/convert` | Converter voz |
| GET | `/api/v1/voice/profiles` | Listar perfis |
| POST | `/api/v1/voice/profiles` | Criar perfil |

### Pipeline Avançado

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/voice/pipeline` | TTS + RVC combinado |
| GET | `/api/v1/voice/pipeline/emotions` | Listar emoções |
| GET | `/api/v1/voice/pipeline/languages` | Listar idiomas |

### Usuários e Créditos

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/users/register` | Criar usuário |
| POST | `/api/v1/users/login` | Login (OAuth2) |
| GET | `/api/v1/users/me` | Perfil do usuário |
| GET | `/api/v1/users/credits` | Consultar saldo |

### Pagamentos

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/payments/plans` | Listar planos |
| GET | `/api/v1/payments/status` | Status do sistema |
| POST | `/api/v1/payments/checkout` | Iniciar compra |

### Tasks (Background Jobs)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/tasks/{task_id}` | Status de uma task |
| GET | `/api/v1/tasks` | Listar tasks |
| POST | `/api/v1/tasks/{task_id}/cancel` | Cancelar task |

### Webhooks

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/webhooks` | Registrar webhook |
| GET | `/api/v1/webhooks` | Listar webhooks |
| DELETE | `/api/v1/webhooks/{id}` | Remover webhook |

## 🔧 Configuração

### Variáveis de Ambiente (.env)

```env
# Aplicação
DEBUG=false
SECRET_KEY=sua-chave-secreta

# GPU (opcional)
GPU_DEVICE=cuda:0

# Mercado Pago (opcional - modo manutenção se vazio)
MERCADOPAGO_ACCESS_TOKEN=
```

## 📦 Estrutura do Projeto

```
voice-cloning-saas/
├── backend/
│   ├── main.py           # Entry point FastAPI
│   ├── config.py         # Configurações
│   ├── routers/          # Endpoints REST
│   ├── services/         # Lógica de negócio
│   ├── models/           # ORM e Schemas
│   └── utils/            # Utilitários
├── src/                  # Frontend React
├── models/               # Checkpoints ML
├── outputs/              # Áudios gerados
└── uploads/              # Uploads temporários
```

## 🧪 Testes

```bash
# Rodar testes
pytest

# Com cobertura
pytest --cov=backend
```

## 📖 Documentação da API

Acesse a documentação interativa em:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🤝 Contribuindo

PRs são bem-vindos! Veja [CONTRIBUTING.md](CONTRIBUTING.md) para diretrizes.

## 📄 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.
