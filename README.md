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

#### Ambiente Conda RVC (separado)
O RVC usa Python 3.10 em um ambiente separado devido a incompatibilidades:

```powershell
# Ambiente principal (F5-TTS, backend)
conda activate voicecloner           # Python 3.11

# Ambiente RVC (inferência RVC via subprocess)
conda activate voicecloner-rvc-py310  # Python 3.10

# O backend chama RVC via subprocess automaticamente:
# C:\Users\minei\miniconda3\Scripts\conda.exe run -n voicecloner-rvc-py310 python ...
```

**Por que ambientes separados?**
- F5-TTS requer Python 3.11+ e PyTorch recente
- RVC WebUI requer Python 3.10 e fairseq (incompatível com Py3.11+)
- O backend orquestra ambos via subprocess

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

#### 6. RVC Trava no Windows (multiprocessing.Manager deadlock)
O módulo `rvc_for_realtime.py` cria um `multiprocessing.Manager()` global que **causa deadlock** 
quando executado via `conda run` no Windows. 

**Solução implementada:** 
- Monkeypatch do `multiprocessing.Manager` antes de importar módulos RVC
- `DummyQueue` substitui as queues reais (não são usadas para métodos rmvpe/crepe/fcpe/pm)

```python
# backend/scripts/rvc_inference_runner.py
class DummyManager:
    def Queue(self):
        return DummyQueue()

multiprocessing.Manager = DummyManager
```

#### 7. PyTorch 2.6+ quebra RVC/fairseq (weights_only=True)
A partir do PyTorch 2.6, `torch.load()` usa `weights_only=True` por padrão, 
o que quebra fairseq e o RVC WebUI.

**Solução implementada:**
```python
# backend/scripts/rvc_inference_runner.py
_original_torch_load = torch.load
def _patched_torch_load(*args, **kwargs):
    if 'weights_only' not in kwargs:
        kwargs['weights_only'] = False
    return _original_torch_load(*args, **kwargs)
torch.load = _patched_torch_load
```

#### 8. RVC get_synthesizer.py: tuple vs list
O checkpoint RVC pode ter `cpt["config"]` como tupla, causando erro:
```
TypeError: 'tuple' object does not support item assignment
```

**Solução implementada em** `third_party/rvc-webui/infer/lib/jit/get_synthesizer.py`:
```python
if isinstance(cpt["config"], tuple):
    cpt["config"] = list(cpt["config"])
```

#### 9. Voz gerada não corresponde ao perfil (RVC genérico)
O modelo RVC `baicai357k.pth` é **genérico** e converte para outra voz qualquer.
Se você não tem um modelo RVC treinado especificamente para a voz do perfil, 
o RVC vai **destruir** o voice cloning do F5-TTS.

**Solução:** `apply_rvc=False` é o padrão correto. O F5-TTS já faz voice cloning 
baseado no áudio de referência, sem precisar de RVC.

```python
# backend/models/schemas.py
apply_rvc: bool = Field(
    False,  # Era True - mudado para False
    description="Se deve aplicar RVC (requer modelo treinado para a voz específica)"
)
```

#### 10. UnicodeDecodeError no subprocess (cp1252 vs UTF-8)
Windows usa encoding `cp1252` por padrão no subprocess, causando erro com caracteres UTF-8.

**Solução implementada:**
```python
result = subprocess.run(
    cmd,
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='replace'  # Evita UnicodeDecodeError
)
```

### Arquitetura de Voice Cloning

```
┌─────────────────────────────────────────────────────────────────┐
│                     PIPELINE DE VOZ                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                  │
│  │  Texto   │───▶│  F5-TTS  │───▶│  Áudio   │  (apply_rvc=F)  │
│  │          │    │          │    │  Final   │                  │
│  └──────────┘    └──────────┘    └──────────┘                  │
│       │               │                                         │
│       │         ┌─────┴─────┐                                   │
│       │         │  Áudio    │                                   │
│       │         │Referência │                                   │
│       │         │(6-10 seg) │                                   │
│       │         └───────────┘                                   │
│       │                                                         │
│  ┌────▼─────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │  Texto   │───▶│  F5-TTS  │───▶│   RVC    │───▶│  Áudio   │  │
│  │          │    │          │    │(modelo   │    │  Final   │  │
│  └──────────┘    └──────────┘    │treinado) │    └──────────┘  │
│                                  └──────────┘  (apply_rvc=T)   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

IMPORTANTE:
- F5-TTS: Zero-shot voice cloning (funciona com qualquer voz, 6s suficiente)
- RVC: Só use se tiver modelo TREINADO para a voz específica do perfil
- Modelo genérico (baicai357k.pth): Converte para VOZ DIFERENTE, não usar!
```

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

### Testes Automatizados
```bash
# Rodar testes
pytest

# Com cobertura
pytest --cov=backend
```

### Teste Manual da Pipeline de Voz

```powershell
# 1. Iniciar servidor
.\dev.ps1

# 2. Login e obter token
$login = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/users/login" `
  -Method POST `
  -ContentType "application/x-www-form-urlencoded" `
  -Body "username=test@example.com&password=password123"

$token = $login.access_token

# 3. Listar perfis de voz
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/voice/profiles?user_id=1" `
  -Headers @{"Authorization"="Bearer $token"}

# 4. Testar síntese (substitua profile_id pelo ID correto)
$body = @{
    text = "Olá, este é um teste de voz clonada!"
    profile_id = 2  # <-- ID do perfil
    emotion = "neutral"
    apply_rvc = $false  # F5-TTS only (recomendado)
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/voice/pipeline?user_id=1" `
  -Method POST `
  -Headers @{"Authorization"="Bearer $token"; "Content-Type"="application/json"} `
  -Body $body
```

### Teste Manual do RVC (isolado)

```powershell
# Ativar ambiente RVC
conda activate voicecloner-rvc-py310

# Executar inferência diretamente
python backend/scripts/rvc_inference_runner.py `
  --repo-dir "third_party/rvc-webui" `
  --model-path "models/rvc/baicai357k.pth" `
  --input "outputs\seu-audio.wav" `
  --output "test_output.wav" `
  --pitch 0 `
  --index-rate 0 `
  --f0method rmvpe `
  --device cpu
```

### Conta de Teste
- **Email:** test@example.com
- **Senha:** password123
- **Créditos:** ~999.999.999 (conta de desenvolvimento)

## 📖 Documentação da API

Acesse a documentação interativa em:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🤝 Contribuindo

PRs são bem-vindos! Veja [CONTRIBUTING.md](CONTRIBUTING.md) para diretrizes.

## 📄 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.
