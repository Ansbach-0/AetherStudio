# Voice Cloning SaaS - Planejamento de Desenvolvimento

## 📋 Visão Geral do Projeto

**Objetivo:** Plataforma de voice cloning para criadores brasileiros/latinos dublarem conteúdo em múltiplos idiomas usando suas próprias vozes.

**Stack Principal:**
- **Backend:** FastAPI + Uvicorn
- **Voice Cloning:** F5-TTS (melhor qualidade/velocidade 2026) + RVC (conversão em tempo real)
- **Infraestrutura:** PyTorch ROCm 6.2+ (AMD 7800XT gfx1101)
- **Gerenciamento de Dependências:** Conda + UV
- **Pagamento:** Mercado Pago API

**Hardware Alvo:**
- GPU: AMD Radeon RX 7800XT (16GB VRAM, gfx1101)
- CPU: AMD Ryzen 9800X3D
- Driver: AMD Adrenalin 26.1.1
- SO: Windows 11 com WSL2 Ubuntu 24.04 (recomendado para ROCm)

---

## 🎯 Modelos Open Source Selecionados

### Voice Cloning - F5-TTS (Modelo Principal)
- **Link:** https://github.com/SWivid/F5-TTS
- **HuggingFace:** https://huggingface.co/spaces/mrfakename/F5-TTS
- **Capacidades:**
  - Zero-shot voice cloning (6 segundos de áudio)
  - Suporte multilíngue (EN, PT, ES, ZH, etc)
  - Latência ~200-500ms
  - Qualidade próxima ao humano (WER baixo)
  - Controle emocional via reference audio
- **VRAM:** ~4-6GB para inferência
- **Suporte ROCm:** Sim, via PyTorch ROCm

### Voice Conversion - RVC (Retrieval-based Voice Conversion)
- **Link:** https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI
- **Capacidades:**
  - Conversão voz-para-voz em tempo real
  - Preservação de timbre e qualidade
  - Ajuste de pitch e formantes
  - Treinamento com poucos dados (10-30 min de áudio)
- **VRAM:** ~2-4GB para inferência
- **Suporte ROCm:** Sim, via Docker ROCm 5.4.2+ ou nativo

### Emotion/Style Transfer - StyleTTS2 (Opcional)
- **Link:** https://github.com/yl4579/StyleTTS2
- **HuggingFace:** https://huggingface.co/yl4579/StyleTTS2-LibriTTS
- **Uso:** Transferência de estilo emocional mais refinada

---

## 🛠️ Setup de Ambiente (Pré-requisito)

### Instalação Base ROCm + PyTorch

```bash
# 1. Criar ambiente conda com Python 3.10 (melhor compatibilidade)
conda create -n voice-clone python=3.10 -y
conda activate voice-clone

# 2. Instalar UV dentro do conda
pip install uv

# 3. Instalar PyTorch com ROCm 6.2 (compatível com 7800XT gfx1101)
# Via pip (recomendado):
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.2

# 4. Verificar GPU
python -c "import torch; print(f'GPU disponível: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}')"

# 5. Configurar variável de ambiente para 7800XT
export HSA_OVERRIDE_GFX_VERSION=11.0.1
# Adicionar ao ~/.bashrc para persistir
```

**Nota Importante:** Se ROCm não funcionar no Windows, use WSL2 Ubuntu 24.04 (suporte oficial ROCm).

---

## 📦 Sprint 0: Configuração Inicial (3 dias)

### Objetivo
Preparar ambiente de desenvolvimento e validar que os modelos rodam na sua GPU.

### Tarefas

#### [ ] 0.1 - Setup do Repositório
- Criar estrutura de pastas do projeto
- Inicializar git repo
- Configurar `.gitignore` (modelos grandes, venv, etc)

#### [ ] 0.2 - Ambiente Conda + UV
- Criar ambiente conda `voice-clone` com Python 3.10
- Instalar UV: `pip install uv`
- Criar `pyproject.toml` e `uv.lock` para gerenciar dependências

#### [ ] 0.3 - Instalar PyTorch ROCm
- Instalar PyTorch ROCm 6.2 para 7800XT
- Configurar `HSA_OVERRIDE_GFX_VERSION=11.0.1`
- Validar GPU: `torch.cuda.is_available()` retorna `True`

#### [ ] 0.4 - Baixar e Testar F5-TTS
```bash
git clone https://github.com/SWivid/F5-TTS.git
cd F5-TTS
uv pip install -e .
python gradio_app.py --port 7860
```
- Acessar `localhost:7860`
- Testar clonagem de voz com áudio de 6 segundos
- Medir tempo de inferência (target: <2s para 10s de áudio)

#### [ ] 0.5 - Baixar e Testar RVC
```bash
git clone https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git
cd Retrieval-based-Voice-Conversion-WebUI
# Instalar dependências ROCm conforme README
python infer-web.py
```
- Testar conversão de voz com modelo pré-treinado
- Validar latência (<500ms para 1s de áudio)

### Critérios de Aceite
- [x] Conda env criado e ativável
- [x] PyTorch detecta GPU AMD 7800XT corretamente
- [x] F5-TTS roda localmente e clona voz com sucesso
- [x] RVC converte voz em tempo aceitável
- [x] Repositório git inicializado com estrutura básica

### Estrutura de Pastas (Sprint 0)
```
voice-clone-saas/
├── backend/              # FastAPI app (criado em Sprint 1)
├── models/               # Diretório para checkpoints
│   ├── f5-tts/
│   └── rvc/
├── data/
│   ├── reference_audios/ # Áudios de referência dos usuários
│   └── generated/        # Áudios gerados
├── scripts/              # Scripts auxiliares
├── tests/                # Testes automatizados
├── pyproject.toml        # Config UV/UV
├── requirements.txt      # Fallback pip
└── README.md
```

---

## 🏗️ Sprint 1: API Base + Inferência F5-TTS (5 dias)

### Objetivo
Criar API REST funcional que recebe texto + áudio de referência e retorna áudio clonado.

### Tarefas

#### [ ] 1.1 - Estrutura Base FastAPI
```python
# backend/main.py
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
import uvicorn

app = FastAPI(title="Voice Clone API", version="0.1.0")

@app.get("/health")
async def health_check():
    return {"status": "ok", "gpu_available": torch.cuda.is_available()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```
- Criar estrutura modular (routers, services, models)
- Configurar CORS para desenvolvimento
- Adicionar logging estruturado

#### [ ] 1.2 - Service de Carregamento do F5-TTS
```python
# backend/services/tts_service.py
import torch
from f5_tts.api import F5TTS

class TTSService:
    def __init__(self):
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
    
    def load_model(self):
        """Carrega F5-TTS no startup"""
        self.model = F5TTS.from_pretrained("F5-TTS")
        self.model.to(self.device)
    
    async def generate_speech(
        self, 
        text: str, 
        reference_audio_path: str,
        language: str = "pt"
    ) -> bytes:
        """Gera áudio clonado"""
        # Implementar lógica de inferência
        pass
```
- Implementar carregamento lazy do modelo (ao receber primeira request)
- Gerenciar memória GPU (limpar cache entre requests)
- Tratar erros de VRAM insuficiente

#### [ ] 1.3 - Endpoint de Voice Cloning
```python
# backend/routers/voice.py
@router.post("/clone-voice")
async def clone_voice(
    text: str = Form(...),
    reference_audio: UploadFile = File(...),
    language: str = Form("pt"),
    tts_service: TTSService = Depends(get_tts_service)
):
    """
    Clona voz usando F5-TTS
    - text: texto a ser falado (max 500 chars)
    - reference_audio: áudio de referência (6-30s, mp3/wav)
    - language: pt, en, es
    """
    # Validar áudio (duração, formato, qualidade)
    # Salvar reference_audio temporariamente
    # Chamar tts_service.generate_speech()
    # Retornar FileResponse com áudio gerado
    pass
```
- Validação de input (duração do áudio, tamanho do texto)
- Processamento assíncrono para não bloquear
- Rate limiting básico (ex: 10 req/min por IP)

#### [ ] 1.4 - Processamento de Áudio
```python
# backend/utils/audio_processor.py
from pydub import AudioSegment
import librosa

class AudioProcessor:
    @staticmethod
    def validate_audio(file_path: str) -> dict:
        """Valida duração, sample rate, canais"""
        audio = AudioSegment.from_file(file_path)
        return {
            "duration": len(audio) / 1000,  # segundos
            "sample_rate": audio.frame_rate,
            "channels": audio.channels
        }
    
    @staticmethod
    def preprocess_reference(file_path: str) -> str:
        """Converte para formato esperado pelo F5-TTS"""
        # Resample para 24kHz
        # Converter para mono
        # Normalizar volume
        pass
```
- Converter formatos (mp3 → wav 24kHz mono)
- Remover silêncio no início/fim
- Normalizar volume

#### [ ] 1.5 - Testes de Integração
- Teste completo do fluxo: upload → processamento → download
- Testar com áudios em PT, EN, ES
- Medir latência end-to-end (target: <5s para 10s de texto)

### Critérios de Aceite
- [x] API FastAPI rodando em `localhost:8000`
- [x] Endpoint `/clone-voice` funcional
- [x] F5-TTS carrega corretamente na GPU
- [x] Áudio clonado tem qualidade aceitável (subjetivo)
- [x] Latência <5s para 10 segundos de áudio falado
- [x] Testes básicos passando

### Dependências (instalar com UV)
```toml
# pyproject.toml
[project]
dependencies = [
    "fastapi>=0.110.0",
    "uvicorn[standard]>=0.27.0",
    "python-multipart>=0.0.9",  # Upload de arquivos
    "pydub>=0.25.1",
    "librosa>=0.10.1",
    "soundfile>=0.12.1",
]
```

---

## 🎨 Sprint 2: RVC Integration + Multi-Speaker (5 dias)

### Objetivo
Adicionar conversão de voz via RVC e suporte a múltiplos idiomas/emoções.

### Tarefas

#### [ ] 2.1 - Service RVC
```python
# backend/services/rvc_service.py
from rvc.api import RVC

class RVCService:
    def __init__(self):
        self.model = None
        self.models_cache = {}  # Cache de modelos treinados
    
    async def convert_voice(
        self, 
        source_audio_path: str,
        target_voice_model: str,
        pitch_shift: int = 0
    ) -> bytes:
        """Converte áudio usando RVC"""
        # Carregar modelo da voz alvo
        # Processar conversão
        # Retornar áudio convertido
        pass
```
- Implementar cache de modelos RVC (evitar reload)
- Suporte a ajuste de pitch (-12 a +12 semitons)
- Processamento em chunks para áudios longos

#### [ ] 2.2 - Pipeline Híbrido F5-TTS + RVC
```python
# backend/services/pipeline_service.py
class VoicePipeline:
    def __init__(self, tts_service: TTSService, rvc_service: RVCService):
        self.tts = tts_service
        self.rvc = rvc_service
    
    async def generate_with_style(
        self,
        text: str,
        reference_audio: str,
        emotion: str = "neutral",  # neutral, happy, sad, angry
        language: str = "pt"
    ) -> bytes:
        """
        Pipeline: F5-TTS (texto → fala) + RVC (estilo emocional)
        """
        # 1. Gerar fala base com F5-TTS
        base_audio = await self.tts.generate_speech(text, reference_audio, language)
        
        # 2. Aplicar estilo emocional via RVC (se não neutral)
        if emotion != "neutral":
            styled_audio = await self.rvc.convert_voice(
                base_audio, 
                f"emotion_{emotion}_model"
            )
            return styled_audio
        
        return base_audio
```
- Criar modelos RVC pré-treinados para emoções (happy, sad, angry)
- Otimizar para minimizar latência do pipeline

#### [ ] 2.3 - Endpoint de Conversão de Voz
```python
@router.post("/convert-voice")
async def convert_voice(
    source_audio: UploadFile = File(...),
    target_voice_id: str = Form(...),
    pitch_shift: int = Form(0),
    rvc_service: RVCService = Depends(get_rvc_service)
):
    """
    Converte voz de um áudio para voz alvo
    - source_audio: áudio original (any voice)
    - target_voice_id: ID da voz salva do usuário
    - pitch_shift: ajuste de tom (-12 a +12)
    """
    pass
```

#### [ ] 2.4 - Sistema de Vozes do Usuário
```python
# backend/models/voice_profile.py
from pydantic import BaseModel
from typing import Optional

class VoiceProfile(BaseModel):
    id: str
    user_id: str
    name: str
    reference_audio_path: str
    language: str
    created_at: datetime
    metadata: Optional[dict] = None  # Tom médio, características
```
- Banco de dados simples (SQLite para MVP) para armazenar perfis de voz
- Endpoint para criar/listar/deletar vozes do usuário
- Validação: usuário pode ter max 5 vozes (plano free)

#### [ ] 2.5 - Multi-Language Support
- Adicionar detecção automática de idioma (langdetect)
- Suportar PT, EN, ES inicialmente
- Configurar pronuncia regional (PT-BR vs PT-PT)

### Critérios de Aceite
- [x] RVC integrado e funcionando
- [x] Pipeline F5-TTS + RVC operacional
- [x] Conversão voz-para-voz funcional
- [x] Sistema de perfis de voz implementado
- [x] Suporte a 3 idiomas (PT, EN, ES)
- [x] Latência pipeline <8s para 10s de áudio

### Dependências Adicionais
```bash
uv pip install sqlalchemy alembic langdetect
```

---

## 💳 Sprint 3: Monetização + Mercado Pago (4 dias)

### Objetivo
Implementar sistema de créditos e integração com Mercado Pago.

### Tarefas

#### [ ] 3.1 - Sistema de Créditos
```python
# backend/models/user.py
class User(BaseModel):
    id: str
    email: str
    credits: int = 100  # 100 créditos iniciais (free tier)
    plan: str = "free"  # free, basic, pro
    created_at: datetime

# backend/services/credits_service.py
class CreditsService:
    COSTS = {
        "clone_voice": 10,      # 10 créditos por minuto de áudio gerado
        "convert_voice": 5,     # 5 créditos por minuto
        "train_model": 50       # 50 créditos para treinar modelo RVC customizado
    }
    
    async def deduct_credits(self, user_id: str, operation: str, duration: float):
        """Deduz créditos baseado na operação e duração"""
        cost = self.COSTS[operation] * (duration / 60)  # Custo por minuto
        # Atualizar banco de dados
        pass
    
    async def check_credits(self, user_id: str, required: int) -> bool:
        """Verifica se usuário tem créditos suficientes"""
        pass
```
- Middleware para deduzir créditos após cada operação
- Endpoint para consultar saldo de créditos

#### [ ] 3.2 - Integração Mercado Pago
```python
# backend/services/payment_service.py
import mercadopago

class PaymentService:
    def __init__(self):
        self.sdk = mercadopago.SDK("ACCESS_TOKEN")
    
    async def create_payment(
        self, 
        user_id: str, 
        plan: str,  # basic, pro
        amount: float
    ) -> dict:
        """Cria preferência de pagamento no Mercado Pago"""
        preference_data = {
            "items": [
                {
                    "title": f"Plano {plan.upper()}",
                    "quantity": 1,
                    "unit_price": amount
                }
            ],
            "back_urls": {
                "success": "https://seusite.com/payment/success",
                "failure": "https://seusite.com/payment/failure",
                "pending": "https://seusite.com/payment/pending"
            },
            "metadata": {
                "user_id": user_id,
                "plan": plan
            }
        }
        
        preference = self.sdk.preference().create(preference_data)
        return preference["response"]
    
    async def handle_webhook(self, payment_data: dict):
        """Processa webhook do Mercado Pago (pagamento aprovado)"""
        # Verificar status do pagamento
        # Adicionar créditos ao usuário
        pass
```
- Endpoint `POST /payment/create` para iniciar pagamento
- Endpoint `POST /webhook/mercadopago` para receber notificações
- Validar assinatura do webhook (segurança)

#### [ ] 3.3 - Planos de Preço
```python
PLANS = {
    "free": {
        "credits": 100,
        "price": 0,
        "max_voices": 5,
        "features": ["basic_cloning", "3_languages"]
    },
    "basic": {
        "credits": 1000,
        "price": 29.90,  # R$ 29,90/mês
        "max_voices": 20,
        "features": ["basic_cloning", "emotion_control", "5_languages", "api_access"]
    },
    "pro": {
        "credits": 5000,
        "price": 99.90,  # R$ 99,90/mês
        "max_voices": 100,
        "features": ["all_features", "custom_rvc_training", "priority_support"]
    }
}
```
- Endpoint para listar planos
- Lógica de upgrade/downgrade de plano
- Envio de email de confirmação (usar serviço SMTP básico)

#### [ ] 3.4 - Dashboard de Uso
```python
@router.get("/usage/stats")
async def get_usage_stats(user_id: str):
    """Retorna estatísticas de uso do usuário"""
    return {
        "credits_remaining": 750,
        "usage_this_month": {
            "clone_voice": 150,  # minutos
            "convert_voice": 50
        },
        "voices_created": 3,
        "plan": "basic"
    }
```

### Critérios de Aceite
- [x] Sistema de créditos funcional
- [x] Integração Mercado Pago completa (sandbox)
- [x] Webhook processa pagamentos corretamente
- [x] Usuário consegue comprar créditos e usar serviço
- [x] Dashboard de uso mostrando dados corretos

### Dependências
```bash
uv pip install mercadopago python-dotenv
```

---

## 🚀 Sprint 4: Otimização + Produção (4 dias)

### Objetivo
Otimizar performance, adicionar cache, logging e preparar para deploy.

### Tarefas

#### [ ] 4.1 - Cache de Inferência
```python
# backend/services/cache_service.py
import redis
import hashlib

class CacheService:
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379, decode_responses=False)
    
    def get_cache_key(self, text: str, reference_audio_hash: str, params: dict) -> str:
        """Gera chave única para cache"""
        content = f"{text}_{reference_audio_hash}_{params}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def get_cached_audio(self, cache_key: str) -> Optional[bytes]:
        """Busca áudio no cache"""
        return self.redis.get(cache_key)
    
    async def cache_audio(self, cache_key: str, audio_bytes: bytes, ttl: int = 3600):
        """Salva áudio no cache (TTL 1h)"""
        self.redis.setex(cache_key, ttl, audio_bytes)
```
- Cachear áudios gerados (mesma combinação texto+voz = mesmo resultado)
- Reduzir latência em 90% para requests repetidas
- Implementar cleanup automático (TTL)

#### [ ] 4.2 - Fila de Processamento Assíncrono
```python
# backend/services/queue_service.py
from celery import Celery

celery_app = Celery('voice_clone', broker='redis://localhost:6379/0')

@celery_app.task
def process_voice_clone_task(text: str, reference_audio: str, user_id: str):
    """Tarefa assíncrona para voice cloning"""
    # Processar em background
    # Enviar notificação quando pronto
    pass

# Endpoint assíncrono
@router.post("/clone-voice-async")
async def clone_voice_async(
    text: str,
    reference_audio: UploadFile,
    background_tasks: BackgroundTasks
):
    """Retorna task_id imediatamente, processa em background"""
    task_id = str(uuid4())
    background_tasks.add_task(process_voice_clone_task, text, reference_audio, user_id)
    return {"task_id": task_id, "status": "processing"}

@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """Consulta status da tarefa"""
    # Buscar status no Redis/DB
    pass
```
- Implementar Celery + Redis para filas
- Endpoint para consultar progresso da tarefa
- Webhook para notificar usuário quando concluído

#### [ ] 4.3 - Logging e Monitoramento
```python
# backend/utils/logger.py
import logging
import structlog

def setup_logging():
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ]
    )
    
logger = structlog.get_logger()

# Uso:
logger.info("voice_clone_started", user_id=user_id, text_length=len(text))
logger.error("model_load_failed", error=str(e))
```
- Logs estruturados em JSON
- Rastreamento de latência por operação
- Alertas para erros críticos (GPU OOM, modelo falhou)

#### [ ] 4.4 - Rate Limiting e Segurança
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/clone-voice")
@limiter.limit("10/minute")  # Max 10 requests por minuto
async def clone_voice(...):
    pass
```
- Rate limiting por IP e por usuário
- Validação de tokens de autenticação (JWT)
- Sanitização de inputs (prevenir path traversal em uploads)

#### [ ] 4.5 - Dockerização
```dockerfile
# Dockerfile
FROM rocm/pytorch:rocm6.2_ubuntu24.04_py3.10_pytorch_release_2.3.0

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependências Python
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv pip sync

# Copiar código
COPY . .

# Expor porta
EXPOSE 8000

# Comando de inicialização
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
- Dockerfile multi-stage para otimizar tamanho
- docker-compose.yml com FastAPI + Redis + Postgres
- Volume para modelos (evitar redownload)

#### [ ] 4.6 - Testes de Carga
```python
# tests/load_test.py
import asyncio
import aiohttp

async def test_concurrent_requests(num_requests: int = 100):
    """Simula 100 requests simultâneos"""
    async with aiohttp.ClientSession() as session:
        tasks = [
            session.post(
                "http://localhost:8000/clone-voice",
                data={"text": "teste", "reference_audio": audio_file}
            )
            for _ in range(num_requests)
        ]
        responses = await asyncio.gather(*tasks)
    # Analisar latências, rate de sucesso
```
- Testar com 50-100 requests concorrentes
- Identificar gargalos (GPU, CPU, memória)
- Ajustar workers do Uvicorn conforme necessário

### Critérios de Aceite
- [x] Cache reduz latência em >80% para requests repetidas
- [x] Fila assíncrona processa tarefas em background
- [x] Logs estruturados capturando métricas importantes
- [x] Rate limiting protegendo API
- [x] Docker container buildando e rodando corretamente
- [x] API suporta 50+ requests concorrentes sem degradação

### Dependências Finais
```bash
uv pip install redis celery slowapi structlog pytest-asyncio aiohttp
```

---

## 🎯 Sprint 5: Features Avançadas (Opcional - 5 dias)

### Objetivo
Features diferenciadas para MVP competitivo.

### Tarefas Opcionais

#### [ ] 5.1 - Treinamento de RVC Personalizado
- Endpoint para usuário enviar 10-30 min de áudio próprio
- Pipeline de treinamento RVC em background (Celery)
- Notificação quando modelo estiver pronto (~2-4h)

#### [ ] 5.2 - Edição de Pronúncia Regional
```python
# backend/utils/pronunciation.py
REGIONAL_OVERRIDES = {
    "pt-BR": {
        "leite": "LAY-chee",
        "norte": "NOHR-chee"
    },
    "pt-PT": {
        "leite": "LAY-te",
        "norte": "NOHR-te"
    }
}

def apply_regional_pronunciation(text: str, region: str) -> str:
    """Ajusta pronúncia baseado na região"""
    pass
```

#### [ ] 5.3 - API de Webhook para Integrações
- Usuário configura webhook URL
- Sistema envia POST quando áudio estiver pronto
- Casos de uso: integração com editores de vídeo, CMS

#### [ ] 5.4 - Dashboard Web (React)
- UI minimalista para testar funcionalidades
- Upload de áudio, input de texto, player de resultado
- Histórico de áudios gerados
- Gerenciamento de vozes salvas

---

## 📊 Métricas de Sucesso (KPIs)

### Performance
- **Latência de inferência:** <5s para 10s de áudio (F5-TTS solo)
- **Latência pipeline:** <8s para 10s de áudio (F5-TTS + RVC)
- **Cache hit rate:** >60% após 1 semana de uso
- **GPU utilization:** 80-95% durante inferência

### Qualidade
- **WER (Word Error Rate):** <5% para PT-BR
- **Similaridade de voz:** >85% (métrica subjetiva via teste A/B)
- **Taxa de sucesso:** >95% das requests completam sem erro

### Negócio (pós-lançamento)
- **CAC (Custo Aquisição Cliente):** <R$ 50
- **LTV (Lifetime Value):** >R$ 200
- **Churn rate:** <10% ao mês
- **Conversão free → paid:** >5%

---

## 🗓️ Timeline Resumido

| Sprint | Duração | Entregas Principais |
|--------|---------|---------------------|
| **Sprint 0** | 3 dias | Ambiente configurado, modelos testados |
| **Sprint 1** | 5 dias | API base, endpoint `/clone-voice` funcional |
| **Sprint 2** | 5 dias | RVC integrado, multi-idioma, perfis de voz |
| **Sprint 3** | 4 dias | Mercado Pago, sistema de créditos |
| **Sprint 4** | 4 dias | Cache, filas, Docker, testes de carga |
| **Sprint 5** | 5 dias | Features avançadas (opcional) |

**Total:** 21-26 dias para MVP funcional.

---

## 🔗 Links Úteis

### Modelos
- **F5-TTS:** https://github.com/SWivid/F5-TTS
- **RVC WebUI:** https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI
- **StyleTTS2:** https://github.com/yl4579/StyleTTS2
- **Coqui XTTS-v2:** https://huggingface.co/coqui/XTTS-v2 (alternativa)

### ROCm + PyTorch
- **PyTorch ROCm:** https://pytorch.org/get-started/locally/ (selecionar ROCm)
- **ROCm Docs:** https://rocm.docs.amd.com/
- **Instalação PyTorch ROCm:** https://rocm.docs.amd.com/projects/install-on-linux/en/latest/install/3rd-party/pytorch-install.html

### FastAPI + Tooling
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **UV Package Manager:** https://github.com/astral-sh/uv
- **Celery Docs:** https://docs.celeryq.dev/

### Mercado Pago
- **SDK Python:** https://github.com/mercadopago/sdk-python
- **API Docs:** https://www.mercadopago.com.br/developers/pt/docs

---

## 🚨 Troubleshooting Comum

### GPU não detectada
```bash
# Verificar ROCm
rocminfo | grep gfx

# Verificar PyTorch
python -c "import torch; print(torch.cuda.is_available())"

# Configurar para 7800XT
export HSA_OVERRIDE_GFX_VERSION=11.0.1
```

### OOM (Out of Memory) na GPU
- Reduzir batch size
- Processar em chunks menores
- Limpar cache: `torch.cuda.empty_cache()`
- Usar mixed precision (FP16): `torch.autocast('cuda')`

### F5-TTS muito lento
- Verificar se está rodando na GPU: `model.device`
- Usar compilação: `torch.compile(model)` (PyTorch 2.0+)
- Reduzir qualidade (sample rate 16kHz → 22kHz)

### RVC qualidade ruim
- Aumentar duração do áudio de referência (>10s)
- Treinar modelo RVC personalizado (30 min de áudio limpo)
- Ajustar pitch shift manualmente

---

## 📝 Notas Finais

- **Priorize qualidade sobre quantidade de features** no MVP
- **Teste com criadores reais** desde Sprint 2 (feedback antecipado)
- **Monetização desde o início** (não ofereça tudo grátis)
- **Documente APIs** com OpenAPI (FastAPI auto-gera)
- **Backup regular** de modelos treinados e dados de usuários

**Boa sorte com o projeto! 🚀🎙️**