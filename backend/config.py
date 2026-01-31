"""
Configurações centralizadas da aplicação.

Utiliza Pydantic Settings para gerenciar variáveis de ambiente
com validação de tipos e valores padrão seguros.
"""

from functools import lru_cache
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_comma_list(v: Union[str, List[str], None], default: List[str]) -> List[str]:
    """Converte string separada por vírgula em lista de forma segura."""
    if v is None or v == "":
        return default
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        return [item.strip() for item in v.split(",") if item.strip()]
    return default


class Settings(BaseSettings):
    """
    Configurações da aplicação carregadas de variáveis de ambiente.
    
    Attributes:
        app_name: Nome da aplicação exibido na API
        app_version: Versão atual da aplicação
        debug: Modo debug (desativar em produção)
        database_url: URL de conexão com o banco SQLite
        gpu_device: Dispositivo GPU para inferência (cuda:0 ou cpu)
        use_rocm: Flag para forçar uso de ROCm em GPUs AMD
        rocm_visible_devices: Qual GPU AMD usar (0, 1, etc)
        hsa_override_gfx_version: Versão GFX para compatibilidade ROCm
        pytorch_rocm_arch: Arquitetura alvo ROCm (gfx1100 para RDNA 3)
        max_audio_duration: Duração máxima de áudio em segundos
        min_audio_duration: Duração mínima de áudio em segundos
        allowed_audio_formats: Formatos de áudio aceitos
        allowed_languages: Idiomas suportados para clonagem
        upload_dir: Diretório para uploads temporários
        models_dir: Diretório onde os modelos ML são armazenados
        default_credits: Créditos iniciais para novos usuários
        credits_per_second: Créditos cobrados por segundo de áudio
        rate_limit_requests: Limite de requisições por minuto
        cors_origins: Origens permitidas para CORS
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Validadores para converter strings separadas por vírgula em listas
    @field_validator("allowed_audio_formats", mode="before")
    @classmethod
    def parse_audio_formats(cls, v):
        return parse_comma_list(v, ["mp3", "wav", "flac", "ogg", "m4a"])
    
    @field_validator("allowed_languages", mode="before")
    @classmethod  
    def parse_languages(cls, v):
        return parse_comma_list(v, ["pt-BR", "en-US", "es-ES"])
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v):
        return parse_comma_list(v, ["http://localhost:5173", "http://localhost:3000"])
    
    # Configurações gerais da aplicação
    app_name: str = "Voice Cloning SaaS API"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # Banco de dados
    database_url: str = "sqlite+aiosqlite:///./voice_cloning.db"
    
    # Configurações de GPU/ML
    gpu_device: str = "cuda:0"
    torch_threads: int = 4
    
    # Configurações ROCm para GPUs AMD (APENAS LINUX NATIVO)
    # IMPORTANTE: ROCm NÃO funciona em WSL2! Requer /dev/dri e /dev/kfd que só existem em Linux nativo.
    # Em WSL2, use DirectML (use_directml=True) que funciona via /dev/dxg.
    #
    # Para usar ROCm, você precisa de:
    # 1. Ubuntu 24.04 ou RHEL 9.4+ NATIVO (dual boot, não WSL)
    # 2. Drivers ROCm instalados: https://rocm.docs.amd.com/projects/install-on-linux/
    # 3. PyTorch ROCm: pip install torch --index-url https://download.pytorch.org/whl/rocm6.2
    #
    # RX 7800 XT = gfx1101 (não gfx1100!)
    use_rocm: bool = False  # Desabilitado - WSL2 não suporta ROCm
    rocm_visible_devices: str = "0"
    hsa_override_gfx_version: str = "11.0.1"  # 11.0.1 para gfx1101 (RX 7800 XT)
    pytorch_rocm_arch: str = "gfx1101"  # gfx1101 para RX 7800 XT (RDNA 3)
    
    # DirectML - ÚNICA opção para GPU AMD em WSL2
    # Funciona via /dev/dxg exposto pelo Windows
    use_directml: bool = True
    directml_device_id: int = 0
    
    # Limites de áudio
    max_audio_duration: int = 300  # 5 minutos
    min_audio_duration: int = 3    # 3 segundos
    max_file_size_mb: int = 50     # 50 MB
    
    # Formatos e idiomas suportados
    allowed_audio_formats: List[str] = ["mp3", "wav", "flac", "ogg", "m4a"]
    allowed_languages: List[str] = ["pt-BR", "en-US", "es-ES"]
    
    # Diretórios
    upload_dir: str = "./uploads"
    models_dir: str = "./models"
    output_dir: str = "./outputs"
    rvc_repo_dir: str = "./third_party/rvc-webui"
    rvc_env_name: str = "voicecloner"
    
    # Sistema de créditos
    default_credits: int = 100
    credits_per_second: float = 0.5
    
    # Rate limiting
    rate_limit_requests: int = 60  # por minuto
    rate_limit_period: int = 60    # segundos
    
    # Cache settings
    cache_max_size: int = 50
    cache_ttl_seconds: int = 3600
    max_concurrent_tasks: int = 3
    
    # CORS
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # Segurança
    secret_key: str = "change-me-in-production-use-strong-secret"
    api_key_header: str = "X-API-Key"
    
    # Mercado Pago (deixe vazio para modo placeholder/manutenção)
    mercadopago_access_token: str = ""
    mercadopago_webhook_secret: str = ""


@lru_cache()
def get_settings() -> Settings:
    """
    Retorna instância cacheada das configurações.
    
    Utiliza lru_cache para evitar recarregar o .env
    em cada requisição.
    
    Returns:
        Settings: Configurações da aplicação
    """
    return Settings()
