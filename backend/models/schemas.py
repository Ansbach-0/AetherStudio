"""
Schemas Pydantic para validação de dados.

Define os modelos de entrada e saída da API com validação
automática e documentação OpenAPI.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# =============================================================================
# SCHEMAS DE USUÁRIO
# =============================================================================

class UserBase(BaseModel):
    """Schema base com campos comuns de usuário."""
    email: EmailStr = Field(..., description="Email do usuário")
    name: Optional[str] = Field(None, max_length=100, description="Nome de exibição")


class UserCreate(UserBase):
    """
    Schema para criação de novo usuário.
    
    Exemplo de uso:
        POST /api/v1/user/register
        {
            "email": "usuario@exemplo.com",
            "name": "João Silva"
        }
    """
    pass


class UserResponse(UserBase):
    """
    Schema de resposta com dados do usuário.
    
    Retornado após criação ou consulta de usuário.
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="ID único do usuário")
    credits: float = Field(..., description="Saldo atual de créditos")
    plan: str = Field(..., description="Tipo de plano (free, basic, pro, enterprise)")
    api_key: Optional[str] = Field(None, description="Chave de API para acesso programático")
    is_active: bool = Field(..., description="Se o usuário está ativo")
    created_at: datetime = Field(..., description="Data de criação da conta")


# =============================================================================
# SCHEMAS DE CRÉDITOS
# =============================================================================

class CreditBalance(BaseModel):
    """
    Saldo de créditos do usuário.
    
    Retorna informações sobre créditos disponíveis e limites do plano.
    """
    user_id: int = Field(..., description="ID do usuário")
    credits: float = Field(..., description="Créditos disponíveis")
    plan: str = Field(..., description="Plano atual")
    credits_per_second: float = Field(..., description="Custo por segundo de áudio")


class UsageStats(BaseModel):
    """
    Estatísticas de uso do usuário.
    
    Fornece métricas de utilização da plataforma.
    """
    user_id: int = Field(..., description="ID do usuário")
    total_clones: int = Field(0, description="Total de clonagens realizadas")
    total_conversions: int = Field(0, description="Total de conversões realizadas")
    total_credits_used: float = Field(0, description="Total de créditos consumidos")
    total_audio_seconds: float = Field(0, description="Total de segundos de áudio processados")
    voice_profiles_count: int = Field(0, description="Quantidade de perfis de voz")


# =============================================================================
# SCHEMAS DE PERFIL DE VOZ
# =============================================================================

class VoiceProfileBase(BaseModel):
    """Schema base para perfil de voz."""
    name: str = Field(..., min_length=1, max_length=100, description="Nome do perfil")
    description: Optional[str] = Field(None, max_length=500, description="Descrição do perfil")
    language: str = Field("pt-BR", description="Idioma do perfil (pt-BR, en-US, es-ES)")


class VoiceProfileCreate(VoiceProfileBase):
    """
    Schema para criação de perfil de voz.
    
    O áudio de referência é enviado separadamente via multipart/form-data.
    """
    is_public: bool = Field(False, description="Se o perfil é público")


class VoiceProfileUpdate(BaseModel):
    """
    Schema para atualização de perfil de voz.
    
    Todos os campos são opcionais - apenas os fornecidos serão atualizados.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Nome do perfil")
    description: Optional[str] = Field(None, max_length=500, description="Descrição do perfil")
    reference_text: Optional[str] = Field(None, max_length=5000, description="Transcrição do áudio de referência")
    language: Optional[str] = Field(None, description="Idioma do perfil")
    color: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$", description="Cor hexadecimal (ex: #7c3aed)")
    tags: Optional[str] = Field(None, max_length=200, description="Tags separadas por vírgula")
    is_public: Optional[bool] = Field(None, description="Se o perfil é público")


class VoiceProfileResponse(VoiceProfileBase):
    """
    Schema de resposta para perfil de voz.
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="ID único do perfil")
    user_id: int = Field(..., description="ID do usuário proprietário")
    reference_text: Optional[str] = Field(None, description="Transcrição do áudio de referência")
    color: Optional[str] = Field(None, description="Cor hexadecimal para avatar/UI")
    tags: Optional[str] = Field(None, description="Tags de estilo separadas por vírgula")
    is_public: bool = Field(..., description="Se o perfil é público")
    created_at: datetime = Field(..., description="Data de criação")


# =============================================================================
# SCHEMAS DE CLONAGEM DE VOZ
# =============================================================================

class VoiceCloneRequest(BaseModel):
    """
    Requisição para clonagem de voz.
    
    Envia texto para ser sintetizado com a voz clonada.
    O áudio de referência pode ser enviado via URL ou profile_id.
    
    Exemplo de uso:
        POST /api/v1/voice/clone
        {
            "text": "Olá, esta é minha voz clonada!",
            "profile_id": 1,
            "language": "pt-BR"
        }
    """
    text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Texto a ser sintetizado"
    )
    profile_id: Optional[int] = Field(
        None,
        description="ID do perfil de voz salvo"
    )
    reference_audio_url: Optional[str] = Field(
        None,
        description="URL do áudio de referência (alternativa ao profile_id)"
    )
    language: str = Field(
        "pt-BR",
        description="Idioma da síntese"
    )
    speed: float = Field(
        1.0,
        ge=0.5,
        le=2.0,
        description="Velocidade da fala (0.5 a 2.0)"
    )


class VoiceCloneResponse(BaseModel):
    """
    Resposta da clonagem de voz.
    
    Contém URL do áudio gerado e informações de processamento.
    """
    success: bool = Field(..., description="Se a operação foi bem sucedida")
    audio_url: str = Field(..., description="URL do áudio gerado")
    duration_seconds: float = Field(..., description="Duração do áudio em segundos")
    credits_used: float = Field(..., description="Créditos consumidos")
    processing_time_ms: int = Field(..., description="Tempo de processamento em ms")
    message: Optional[str] = Field(None, description="Mensagem adicional")


# =============================================================================
# SCHEMAS DE CONVERSÃO DE VOZ
# =============================================================================

class VoiceConvertRequest(BaseModel):
    """
    Requisição para conversão de voz (voice-to-voice).
    
    Converte áudio de entrada para a voz do perfil selecionado.
    """
    profile_id: int = Field(..., description="ID do perfil de voz alvo")
    pitch_shift: int = Field(
        0,
        ge=-12,
        le=12,
        description="Ajuste de tom em semitons (-12 a +12)"
    )


class VoiceConvertResponse(BaseModel):
    """
    Resposta da conversão de voz.
    """
    success: bool = Field(..., description="Se a operação foi bem sucedida")
    audio_url: str = Field(..., description="URL do áudio convertido")
    duration_seconds: float = Field(..., description="Duração do áudio")
    credits_used: float = Field(..., description="Créditos consumidos")
    processing_time_ms: int = Field(..., description="Tempo de processamento em ms")


# =============================================================================
# SCHEMAS DE PIPELINE DE VOZ
# =============================================================================

class VoicePipelineRequest(BaseModel):
    """
    Requisição para pipeline completo de voz (TTS + RVC).
    
    Combina síntese de voz com estilização emocional.
    
    Exemplo de uso:
        POST /api/v1/voice/pipeline
        {
            "text": "Olá, esta é minha voz estilizada!",
            "profile_id": 1,
            "emotion": "happy",
            "apply_rvc": true
        }
    """
    text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Texto a ser sintetizado"
    )
    profile_id: Optional[int] = Field(
        None,
        description="ID do perfil de voz"
    )
    reference_audio_url: Optional[str] = Field(
        None,
        description="URL do áudio de referência (alternativa ao profile_id)"
    )
    style_model: Optional[str] = Field(
        None,
        description="Modelo RVC para estilização (opcional)"
    )
    emotion: str = Field(
        "neutral",
        description="Estilo emocional (neutral, happy, sad, angry, calm, excited)"
    )
    language: Optional[str] = Field(
        None,
        description="Idioma da síntese (auto-detecta se None)"
    )
    speed: Optional[float] = Field(
        None,
        ge=0.5,
        le=2.0,
        description="Velocidade da fala (usa preset de emoção se None)"
    )
    pitch_shift: Optional[int] = Field(
        None,
        ge=-12,
        le=12,
        description="Ajuste de tom em semitons (usa preset de emoção se None)"
    )
    apply_rvc: bool = Field(
        True,
        description="Se deve aplicar RVC para estilização"
    )


class VoicePipelineResponse(BaseModel):
    """
    Resposta do pipeline de voz.
    
    Contém resultado do processamento completo TTS + RVC.
    """
    success: bool = Field(..., description="Se a operação foi bem sucedida")
    pipeline_id: str = Field(..., description="ID único do pipeline executado")
    audio_url: str = Field(..., description="URL do áudio final")
    duration_seconds: float = Field(..., description="Duração do áudio")
    credits_used: float = Field(..., description="Créditos consumidos")
    processing_time_ms: int = Field(..., description="Tempo de processamento em ms")
    language: str = Field(..., description="Idioma detectado/usado")
    emotion: str = Field(..., description="Emoção aplicada")
    stages_completed: List[str] = Field(..., description="Etapas completadas (tts, rvc)")
    intermediate_audio: Optional[str] = Field(None, description="URL do áudio intermediário (TTS)")
    message: Optional[str] = Field(None, description="Mensagem adicional")


class EmotionInfo(BaseModel):
    """Informações sobre uma emoção disponível."""
    name: str = Field(..., description="Nome da emoção")
    pitch_shift: int = Field(..., description="Ajuste de pitch padrão")
    speed: float = Field(..., description="Velocidade padrão")


class AvailableEmotionsResponse(BaseModel):
    """Lista de emoções disponíveis para o pipeline."""
    emotions: List[EmotionInfo] = Field(..., description="Lista de emoções disponíveis")


class LanguageInfo(BaseModel):
    """Informações sobre um idioma suportado."""
    code: str = Field(..., description="Código do idioma (ex: pt-BR)")
    name: str = Field(..., description="Nome do idioma")


class SupportedLanguagesResponse(BaseModel):
    """Lista de idiomas suportados."""
    languages: List[LanguageInfo] = Field(..., description="Lista de idiomas suportados")


class PipelineStatusResponse(BaseModel):
    """Status do pipeline de voz."""
    tts_loaded: bool = Field(..., description="Se TTS está carregado")
    rvc_loaded: bool = Field(..., description="Se RVC está carregado")
    available_emotions: List[str] = Field(..., description="Emoções disponíveis")
    ready: bool = Field(..., description="Se o pipeline está pronto")


# =============================================================================
# SCHEMAS DE STATUS E ERROS
# =============================================================================

class HealthResponse(BaseModel):
    """Resposta do health check."""
    status: str = Field(..., description="Status da API (healthy/unhealthy)")
    version: str = Field(..., description="Versão da API")
    timestamp: datetime = Field(..., description="Timestamp da verificação")


class GPUStatusResponse(BaseModel):
    """Status da GPU."""
    available: bool = Field(..., description="Se GPU está disponível")
    device_name: Optional[str] = Field(None, description="Nome do dispositivo")
    memory_total_gb: Optional[float] = Field(None, description="Memória total em GB")
    memory_used_gb: Optional[float] = Field(None, description="Memória em uso em GB")
    cuda_version: Optional[str] = Field(None, description="Versão do CUDA")


class ErrorResponse(BaseModel):
    """Resposta padrão de erro."""
    error: str = Field(..., description="Código do erro")
    message: str = Field(..., description="Mensagem de erro")
    detail: Optional[str] = Field(None, description="Detalhes adicionais")


class TransactionResponse(BaseModel):
    """Resposta de transação de créditos."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="ID da transação")
    operation: str = Field(..., description="Tipo de operação")
    credits_used: float = Field(..., description="Créditos da transação")
    balance_after: float = Field(..., description="Saldo após transação")
    description: Optional[str] = Field(None, description="Descrição")
    created_at: datetime = Field(..., description="Data da transação")


# =============================================================================
# SCHEMAS DE PAGAMENTO
# =============================================================================

class PlanResponse(BaseModel):
    """
    Resposta com detalhes de um plano.
    
    Contém informações sobre preço, créditos e recursos do plano.
    """
    id: str = Field(..., description="ID do plano (free, basic, pro, enterprise)")
    name: str = Field(..., description="Nome de exibição do plano")
    credits: int = Field(..., description="Quantidade de créditos incluídos")
    price_brl: float = Field(..., description="Preço em reais (BRL)")
    max_voices: int = Field(..., description="Limite de perfis de voz (-1 = ilimitado)")
    features: List[str] = Field(..., description="Lista de recursos incluídos")
    description: str = Field(..., description="Descrição do plano")


class CreditPackageResponse(BaseModel):
    """
    Resposta com detalhes de um pacote de créditos.
    
    Pacotes avulsos para compra de créditos extras.
    """
    index: int = Field(..., description="Índice do pacote")
    credits: int = Field(..., description="Quantidade de créditos")
    price_brl: float = Field(..., description="Preço em reais (BRL)")
    bonus: int = Field(..., description="Créditos bônus incluídos")


class PaymentStatusResponse(BaseModel):
    """
    Status do sistema de pagamentos.
    
    Indica se pagamentos estão disponíveis ou em manutenção.
    """
    available: bool = Field(..., description="Se pagamentos estão disponíveis")
    status: str = Field(..., description="Status do sistema (live, maintenance)")
    message: Optional[str] = Field(None, description="Mensagem de status")
    description: Optional[str] = Field(None, description="Descrição adicional")


class CheckoutResponse(BaseModel):
    """
    Resposta do checkout de pagamento.
    
    Contém URLs para redirecionamento ao Mercado Pago.
    """
    success: bool = Field(..., description="Se a criação do checkout foi bem sucedida")
    payment_id: Optional[str] = Field(None, description="ID do pagamento no Mercado Pago")
    init_point: Optional[str] = Field(None, description="URL para checkout do Mercado Pago")
    sandbox_init_point: Optional[str] = Field(None, description="URL para checkout em sandbox")
    amount: Optional[float] = Field(None, description="Valor do pagamento")
    credits: Optional[int] = Field(None, description="Créditos a receber")
    error: Optional[str] = Field(None, description="Código de erro, se houver")
    message: Optional[str] = Field(None, description="Mensagem de erro ou sucesso")
