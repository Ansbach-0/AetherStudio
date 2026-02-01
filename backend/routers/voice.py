"""
Endpoints de clonagem e conversão de voz.

Fornece endpoints para operações de voice cloning usando F5-TTS e RVC.
Inclui pipeline híbrido para geração de voz estilizada.
"""

import time
import uuid
import os
import shutil
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.models.database import get_db
from backend.models.entities import OperationType, Transaction, User, VoiceProfile
from backend.models.schemas import (
    AvailableEmotionsResponse,
    EmotionInfo,
    LanguageInfo,
    PipelineStatusResponse,
    SupportedLanguagesResponse,
    VoiceCloneRequest,
    VoiceCloneResponse,
    VoiceConvertResponse,
    VoicePipelineRequest,
    VoicePipelineResponse,
    VoiceProfileCreate,
    VoiceProfileResponse,
    VoiceProfileUpdate,
)
from backend.services.audio_processor import AudioProcessor
from backend.services.credits_service import CreditsService
from backend.services.tts_service import TTSService
from backend.services.rvc_service import RVCService
from backend.services.voice_pipeline import VoicePipeline, get_voice_pipeline
from backend.services.language_detector import get_language_detector
from backend.services.background_tasks import get_task_manager
from backend.services.cache_service import get_cache_service
from backend.utils.exceptions import (
    AudioValidationError,
    InsufficientCreditsError,
    VoiceProfileNotFoundError,
)
from backend.utils.logger import get_logger
from backend.routers.user import get_current_user

router = APIRouter(prefix="/voice", tags=["Voice"])
logger = get_logger(__name__)
settings = get_settings()

# Instanciar serviços
audio_processor = AudioProcessor()
tts_service = TTSService()
rvc_service = RVCService()
credits_service = CreditsService()
voice_pipeline = VoicePipeline(tts_service, rvc_service)
language_detector = get_language_detector()


def _profile_to_response(profile: VoiceProfile) -> VoiceProfileResponse:
    """
    Converte uma entidade VoiceProfile para VoiceProfileResponse.
    
    Transforma o caminho do arquivo de áudio em uma URL acessível.
    
    Args:
        profile: Entidade VoiceProfile do banco de dados
    
    Returns:
        VoiceProfileResponse: Schema de resposta com reference_audio_url
    """
    # Converter o caminho do arquivo para URL
    audio_url = None
    if profile.reference_audio_path:
        # Caminho salvo: ./uploads/profiles/{user_id}/{file_id}.wav
        # URL: /uploads/profiles/{user_id}/{file_id}.wav
        audio_url = profile.reference_audio_path.replace("./", "/").replace("\\", "/")
    
    return VoiceProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        name=profile.name,
        description=profile.description,
        language=profile.language,
        reference_audio_url=audio_url,
        reference_text=profile.reference_text,
        color=profile.color,
        tags=profile.tags,
        is_public=profile.is_public,
        created_at=profile.created_at,
    )


@router.post(
    "/clone",
    response_model=VoiceCloneResponse,
    summary="Clonar voz",
    description="Sintetiza texto usando uma voz clonada (F5-TTS)."
)
async def clone_voice(
    request: VoiceCloneRequest,
    user_id: int = Query(..., description="ID do usuário"),
    db: AsyncSession = Depends(get_db)
) -> VoiceCloneResponse:
    """
    Clona voz usando F5-TTS.
    
    Recebe texto e um perfil de voz (ou áudio de referência)
    e gera áudio sintetizado com a voz clonada.
    
    Args:
        request: Dados da requisição de clonagem
        user_id: ID do usuário fazendo a requisição
        db: Sessão do banco de dados
    
    Returns:
        VoiceCloneResponse: Resultado da clonagem
    
    Raises:
        HTTPException: Se créditos insuficientes ou perfil não encontrado
    """
    start_time = time.time()
    
    # Verificar usuário e créditos
    user = await _get_user_or_raise(user_id, db)
    
    # Estimar duração do áudio baseado no texto
    # Aproximação: 150 palavras por minuto, ~5 caracteres por palavra
    estimated_duration = len(request.text) / (150 * 5 / 60)
    estimated_cost = estimated_duration * settings.credits_per_second
    
    if user.credits < estimated_cost:
        raise InsufficientCreditsError(user.credits, estimated_cost)
    
    # Validar perfil de voz se fornecido
    if request.profile_id:
        profile = await _get_profile_or_raise(request.profile_id, user_id, db)
        reference_path = profile.reference_audio_path
    elif request.reference_audio_url:
        reference_path = request.reference_audio_url
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Forneça profile_id ou reference_audio_url"
        )
    
    # Executar TTS (placeholder)
    logger.info(f"Iniciando clonagem de voz para usuário {user_id}")
    result = await tts_service.synthesize(
        text=request.text,
        reference_audio=reference_path,
        language=request.language,
        speed=request.speed
    )
    
    # Calcular custo real baseado na duração
    actual_cost = result["duration"] * settings.credits_per_second
    
    # Debitar créditos
    await credits_service.debit_credits(
        db=db,
        user_id=user_id,
        amount=actual_cost,
        operation=OperationType.VOICE_CLONE,
        description=f"Clonagem de voz: {len(request.text)} caracteres"
    )
    
    processing_time = int((time.time() - start_time) * 1000)
    
    logger.info(
        f"Clonagem concluída para usuário {user_id}: "
        f"duração={result['duration']:.2f}s, custo={actual_cost:.2f} créditos"
    )
    
    return VoiceCloneResponse(
        success=True,
        audio_url=result["audio_url"],
        duration_seconds=result["duration"],
        credits_used=actual_cost,
        processing_time_ms=processing_time,
        message="Áudio gerado com sucesso"
    )


@router.post(
    "/clone-async",
    summary="Clonar voz (assíncrono)",
    description="Inicia clonagem de voz em background e retorna task_id para consulta."
)
async def clone_voice_async(
    request: VoiceCloneRequest,
    user_id: int = Query(..., description="ID do usuário"),
    db: AsyncSession = Depends(get_db)
):
    """
    Clona voz em background usando F5-TTS.
    
    Retorna imediatamente um task_id que pode ser usado para
    consultar o status e resultado da operação.
    
    Args:
        request: Dados da requisição de clonagem
        user_id: ID do usuário fazendo a requisição
        db: Sessão do banco de dados
    
    Returns:
        task_id para consulta posterior
    """
    # Verificar usuário e créditos
    user = await _get_user_or_raise(user_id, db)
    
    # Estimar custo
    estimated_duration = len(request.text) / (150 * 5 / 60)
    estimated_cost = estimated_duration * settings.credits_per_second
    
    if user.credits < estimated_cost:
        raise InsufficientCreditsError(user.credits, estimated_cost)
    
    # Resolver referência de áudio
    if request.profile_id:
        profile = await _get_profile_or_raise(request.profile_id, user_id, db)
        reference_path = profile.reference_audio_path
    elif request.reference_audio_url:
        reference_path = request.reference_audio_url
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Forneça profile_id ou reference_audio_url"
        )
    
    # Verificar cache primeiro
    cache_service = get_cache_service()
    cache_params = {
        "language": request.language,
        "speed": request.speed
    }
    
    cached = await cache_service.get_cached_audio(
        text=request.text,
        reference_audio=reference_path,
        params=cache_params
    )
    
    if cached:
        logger.info(f"Cache hit para clonagem assíncrona: usuário {user_id}")
        return {
            "task_id": None,
            "status": "completed",
            "cached": True,
            "result": cached
        }
    
    # Submeter para execução em background
    task_manager = get_task_manager()
    
    async def process_clone():
        result = await tts_service.synthesize(
            text=request.text,
            reference_audio=reference_path,
            language=request.language,
            speed=request.speed
        )
        # Cachear resultado
        await cache_service.cache_audio(
            text=request.text,
            reference_audio=reference_path,
            params=cache_params,
            result=result
        )
        return result
    
    task_id = await task_manager.submit(
        process_clone,
        metadata={
            "user_id": user_id,
            "text_length": len(request.text),
            "type": "voice_clone"
        }
    )
    
    logger.info(f"Clonagem assíncrona iniciada: task {task_id[:8]} para usuário {user_id}")
    
    return {
        "task_id": task_id,
        "status": "processing",
        "message": "Clonagem iniciada em background. Use GET /api/v1/tasks/{task_id} para consultar status."
    }


@router.post(
    "/convert",
    response_model=VoiceConvertResponse,
    summary="Converter voz",
    description="Converte voz de entrada para voz alvo usando RVC."
)
async def convert_voice(
    user_id: int = Query(..., description="ID do usuário"),
    profile_id: int = Form(..., description="ID do perfil de voz alvo"),
    pitch_shift: int = Form(0, ge=-12, le=12, description="Ajuste de tom"),
    audio_file: UploadFile = File(..., description="Arquivo de áudio para converter"),
    db: AsyncSession = Depends(get_db)
) -> VoiceConvertResponse:
    """
    Converte voz usando RVC (Retrieval-based Voice Conversion).
    
    Recebe áudio de entrada e converte para a voz do perfil selecionado,
    mantendo a entonação e conteúdo original.
    
    Args:
        user_id: ID do usuário
        profile_id: ID do perfil de voz alvo
        pitch_shift: Ajuste de tom (-12 a +12 semitons)
        audio_file: Arquivo de áudio para conversão
        db: Sessão do banco de dados
    
    Returns:
        VoiceConvertResponse: Resultado da conversão
    """
    start_time = time.time()
    
    # Verificar usuário
    user = await _get_user_or_raise(user_id, db)
    
    # Verificar perfil
    profile = await _get_profile_or_raise(profile_id, user_id, db)
    
    # Validar e processar áudio de entrada
    audio_info = await audio_processor.validate_and_process(
        audio_file.file,
        audio_file.filename or "audio"
    )
    
    # Verificar créditos
    estimated_cost = audio_info["duration"] * settings.credits_per_second
    if user.credits < estimated_cost:
        raise InsufficientCreditsError(user.credits, estimated_cost)
    
    # Executar RVC (placeholder)
    logger.info(f"Iniciando conversão de voz para usuário {user_id}")
    result = await rvc_service.convert(
        input_audio_path=audio_info["path"],
        voice_model=profile.reference_audio_path,
        pitch_shift=pitch_shift
    )
    
    # Debitar créditos
    actual_cost = result["duration"] * settings.credits_per_second
    await credits_service.debit_credits(
        db=db,
        user_id=user_id,
        amount=actual_cost,
        operation=OperationType.VOICE_CONVERT,
        description=f"Conversão de voz: {audio_info['duration']:.1f}s"
    )
    
    processing_time = int((time.time() - start_time) * 1000)
    
    logger.info(
        f"Conversão concluída para usuário {user_id}: "
        f"duração={result['duration']:.2f}s, custo={actual_cost:.2f} créditos"
    )
    
    return VoiceConvertResponse(
        success=True,
        audio_url=result["audio_url"],
        duration_seconds=result["duration"],
        credits_used=actual_cost,
        processing_time_ms=processing_time
    )


@router.get(
    "/profiles",
    response_model=List[VoiceProfileResponse],
    summary="Listar perfis de voz",
    description="Retorna todos os perfis de voz do usuário."
)
async def list_profiles(
    include_public: bool = Query(False, description="Incluir perfis públicos"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[VoiceProfileResponse]:
    """
    Lista perfis de voz do usuário.
    
    Args:
        include_public: Se deve incluir perfis públicos de outros usuários
        current_user: Usuário autenticado
        db: Sessão do banco de dados
    
    Returns:
        List[VoiceProfileResponse]: Lista de perfis
    """
    user_id = current_user.id
    
    # Buscar perfis do usuário
    query = select(VoiceProfile).where(VoiceProfile.user_id == user_id)
    
    result = await db.execute(query)
    profiles = result.scalars().all()
    
    # Incluir perfis públicos se solicitado
    if include_public:
        public_query = select(VoiceProfile).where(
            VoiceProfile.is_public.is_(True),
            VoiceProfile.user_id != user_id
        )
        public_result = await db.execute(public_query)
        profiles.extend(public_result.scalars().all())
    
    return [_profile_to_response(p) for p in profiles]


@router.post(
    "/profiles",
    response_model=VoiceProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar perfil de voz",
    description="Cria novo perfil de voz a partir de áudio de referência."
)
async def create_profile(
    user_id: int = Query(..., description="ID do usuário"),
    name: str = Form(..., min_length=1, max_length=100),
    description: str = Form(None, max_length=500),
    reference_text: str = Form(None, max_length=5000, description="Transcrição do áudio de referência para F5-TTS"),
    language: str = Form("pt-BR"),
    is_public: bool = Form(False),
    reference_audio: UploadFile = File(..., description="Áudio de referência"),
    db: AsyncSession = Depends(get_db)
) -> VoiceProfileResponse:
    """
    Cria novo perfil de voz.
    
    Processa e armazena áudio de referência para uso em
    futuras clonagens e conversões.
    
    Args:
        user_id: ID do usuário
        name: Nome do perfil
        description: Descrição opcional
        language: Idioma do perfil
        is_public: Se o perfil é público
        reference_audio: Arquivo de áudio de referência
        db: Sessão do banco de dados
    
    Returns:
        VoiceProfileResponse: Perfil criado
    """
    # Verificar usuário
    user = await _get_user_or_raise(user_id, db)
    
    # Validar áudio
    audio_info = await audio_processor.validate_and_process(
        reference_audio.file,
        reference_audio.filename or "reference"
    )
    
    # Verificar créditos para criação de perfil
    profile_cost = 5.0  # Custo fixo para criar perfil
    if user.credits < profile_cost:
        raise InsufficientCreditsError(user.credits, profile_cost)
    
    # Salvar áudio processado
    file_id = str(uuid.uuid4())
    audio_path = f"{settings.upload_dir}/profiles/{user_id}/{file_id}.wav"
    os.makedirs(os.path.dirname(audio_path), exist_ok=True)
    processed_path = audio_info.get("path")
    if processed_path and os.path.exists(processed_path):
        shutil.move(processed_path, audio_path)
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Áudio processado não encontrado para salvar."
        )
    
    # Criar perfil no banco
    new_profile = VoiceProfile(
        user_id=user_id,
        name=name,
        description=description,
        reference_audio_path=audio_path,
        reference_text=reference_text,  # Transcrição do áudio de referência para F5-TTS
        language=language,
        is_public=is_public
    )
    db.add(new_profile)
    
    # Debitar créditos
    await credits_service.debit_credits(
        db=db,
        user_id=user_id,
        amount=profile_cost,
        operation=OperationType.PROFILE_CREATE,
        description=f"Criação de perfil: {name}"
    )
    
    await db.flush()
    
    logger.info(f"Perfil de voz criado: {name} (ID: {new_profile.id}) para usuário {user_id}")
    
    return _profile_to_response(new_profile)


@router.get(
    "/profiles/{profile_id}",
    response_model=VoiceProfileResponse,
    summary="Obter perfil de voz",
    description="Retorna detalhes de um perfil de voz específico."
)
async def get_profile(
    profile_id: int,
    user_id: int = Query(..., description="ID do usuário"),
    db: AsyncSession = Depends(get_db)
) -> VoiceProfileResponse:
    """
    Busca perfil de voz por ID.
    
    Args:
        profile_id: ID do perfil
        user_id: ID do usuário (para verificar permissão)
        db: Sessão do banco de dados
    
    Returns:
        VoiceProfileResponse: Dados do perfil
    """
    profile = await _get_profile_or_raise(profile_id, user_id, db)
    return _profile_to_response(profile)


@router.patch(
    "/profiles/{profile_id}",
    response_model=VoiceProfileResponse,
    summary="Atualizar perfil de voz",
    description="Atualiza campos de um perfil de voz existente."
)
async def update_profile(
    profile_id: int,
    update_data: VoiceProfileUpdate,
    user_id: int = Query(..., description="ID do usuário"),
    db: AsyncSession = Depends(get_db)
) -> VoiceProfileResponse:
    """
    Atualiza perfil de voz existente.
    
    Apenas os campos fornecidos serão atualizados.
    
    Args:
        profile_id: ID do perfil a atualizar
        update_data: Dados para atualização
        user_id: ID do usuário (para verificar propriedade)
        db: Sessão do banco de dados
    
    Returns:
        VoiceProfileResponse: Perfil atualizado
    """
    # Buscar perfil garantindo que pertence ao usuário
    result = await db.execute(
        select(VoiceProfile)
        .where(VoiceProfile.id == profile_id)
        .where(VoiceProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise VoiceProfileNotFoundError(profile_id)
    
    # Atualizar apenas campos fornecidos
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(profile, field, value)
    
    await db.flush()
    await db.refresh(profile)
    
    logger.info(f"Perfil de voz atualizado: {profile.name} (ID: {profile_id}) - campos: {list(update_dict.keys())}")
    
    return _profile_to_response(profile)


@router.delete(
    "/profiles/{profile_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir perfil de voz",
    description="Remove um perfil de voz do usuário."
)
async def delete_profile(
    profile_id: int,
    user_id: int = Query(..., description="ID do usuário"),
    db: AsyncSession = Depends(get_db)
):
    """
    Exclui perfil de voz.
    
    Args:
        profile_id: ID do perfil a excluir
        user_id: ID do usuário (para verificar propriedade)
        db: Sessão do banco de dados
    """
    # Buscar perfil garantindo que pertence ao usuário
    result = await db.execute(
        select(VoiceProfile)
        .where(VoiceProfile.id == profile_id)
        .where(VoiceProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise VoiceProfileNotFoundError(profile_id)
    
    await db.delete(profile)
    logger.info(f"Perfil de voz excluído: {profile.name} (ID: {profile_id})")


# =============================================================================
# ENDPOINTS DO PIPELINE DE VOZ
# =============================================================================

@router.post(
    "/pipeline",
    response_model=VoicePipelineResponse,
    summary="Pipeline completo de voz",
    description="Executa pipeline TTS + RVC para gerar voz estilizada."
)
async def voice_pipeline_endpoint(
    request: VoicePipelineRequest,
    user_id: int = Query(..., description="ID do usuário"),
    db: AsyncSession = Depends(get_db)
) -> VoicePipelineResponse:
    """
    Executa pipeline completo de geração de voz.
    
    Combina F5-TTS (texto → fala) com RVC (estilização) para
    criar voz personalizada com estilo emocional.
    
    Fluxo:
    1. Sintetiza texto usando F5-TTS com voz de referência
    2. Aplica estilização emocional com RVC (se solicitado)
    
    Args:
        request: Dados da requisição do pipeline
        user_id: ID do usuário fazendo a requisição
        db: Sessão do banco de dados
    
    Returns:
        VoicePipelineResponse: Resultado do pipeline
    """
    start_time = time.time()
    
    # Verificar usuário e créditos
    user = await _get_user_or_raise(user_id, db)
    
    # Estimar custo (TTS + RVC)
    estimated_duration = len(request.text) / (150 * 5 / 60)
    estimated_cost = estimated_duration * settings.credits_per_second
    if request.apply_rvc:
        estimated_cost *= 1.5  # RVC adiciona 50% ao custo
    
    if user.credits < estimated_cost:
        raise InsufficientCreditsError(user.credits, estimated_cost)
    
    # Resolver referência de áudio e texto de referência
    reference_text = None  # Transcrição do áudio de referência (evita Whisper/TorchCodec)
    if request.profile_id:
        profile = await _get_profile_or_raise(request.profile_id, user_id, db)
        reference_path = profile.reference_audio_path
        reference_text = profile.reference_text  # Transcrição salva no perfil
        style_model = request.style_model or profile.reference_audio_path
    elif request.reference_audio_url:
        reference_path = request.reference_audio_url
        style_model = request.style_model
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Forneça profile_id ou reference_audio_url"
        )
    
    logger.info(
        f"Iniciando pipeline de voz para usuário {user_id}: "
        f"emotion={request.emotion}, apply_rvc={request.apply_rvc}, "
        f"has_reference_text={reference_text is not None and len(reference_text or '') > 0}"
    )
    
    # Executar pipeline
    result = await voice_pipeline.text_to_speech_styled(
        text=request.text,
        reference_audio=reference_path,
        style_model=style_model if request.apply_rvc else None,
        emotion=request.emotion,
        language=request.language,
        speed=request.speed,
        pitch_shift=request.pitch_shift,
        apply_rvc=request.apply_rvc,
        reference_text=reference_text  # Passa transcrição para evitar uso do Whisper
    )
    
    # Calcular custo real
    actual_cost = result["duration"] * settings.credits_per_second
    if "rvc" in result.get("stages_completed", []):
        actual_cost *= 1.5
    
    # Debitar créditos
    await credits_service.debit_credits(
        db=db,
        user_id=user_id,
        amount=actual_cost,
        operation=OperationType.VOICE_CLONE,
        description=f"Pipeline de voz ({request.emotion}): {len(request.text)} caracteres"
    )
    
    processing_time = int((time.time() - start_time) * 1000)
    
    logger.info(
        f"Pipeline concluído para usuário {user_id}: "
        f"duração={result['duration']:.2f}s, custo={actual_cost:.2f} créditos, "
        f"etapas={result.get('stages_completed', [])}"
    )
    
    return VoicePipelineResponse(
        success=True,
        pipeline_id=result.get("pipeline_id", str(uuid.uuid4())[:8]),
        audio_url=result["audio_url"],
        duration_seconds=result["duration"],
        credits_used=actual_cost,
        processing_time_ms=processing_time,
        language=result.get("language", request.language or "pt-BR"),
        emotion=request.emotion,
        stages_completed=result.get("stages_completed", ["tts"]),
        intermediate_audio=result.get("intermediate_audio"),
        message="Áudio gerado com sucesso" + (" (mock)" if result.get("mock") else "")
    )


@router.get(
    "/pipeline/emotions",
    response_model=AvailableEmotionsResponse,
    summary="Listar emoções disponíveis",
    description="Retorna lista de estilos emocionais disponíveis para o pipeline."
)
async def list_emotions() -> AvailableEmotionsResponse:
    """
    Lista emoções disponíveis para estilização de voz.
    
    Cada emoção tem presets de pitch e velocidade que podem
    ser sobrescritos na requisição do pipeline.
    
    Returns:
        AvailableEmotionsResponse: Lista de emoções disponíveis
    """
    emotions = voice_pipeline.get_available_emotions()
    
    return AvailableEmotionsResponse(
        emotions=[
            EmotionInfo(
                name=e["name"],
                pitch_shift=e["pitch_shift"],
                speed=e["speed"]
            )
            for e in emotions
        ]
    )


@router.get(
    "/pipeline/languages",
    response_model=SupportedLanguagesResponse,
    summary="Listar idiomas suportados",
    description="Retorna lista de idiomas suportados pelo TTS."
)
async def list_languages() -> SupportedLanguagesResponse:
    """
    Lista idiomas suportados pelo sistema de TTS.
    
    Returns:
        SupportedLanguagesResponse: Lista de idiomas suportados
    """
    languages = language_detector.get_supported_languages()
    
    return SupportedLanguagesResponse(
        languages=[
            LanguageInfo(code=lang["code"], name=lang["name"])
            for lang in languages
        ]
    )


@router.get(
    "/pipeline/status",
    response_model=PipelineStatusResponse,
    summary="Status do pipeline",
    description="Retorna status atual do pipeline de voz."
)
async def pipeline_status() -> PipelineStatusResponse:
    """
    Verifica status do pipeline de voz.
    
    Retorna informações sobre carregamento de modelos
    e disponibilidade de funcionalidades.
    
    Returns:
        PipelineStatusResponse: Status do pipeline
    """
    status_info = voice_pipeline.status
    
    return PipelineStatusResponse(
        tts_loaded=status_info["tts"]["loaded"],
        rvc_loaded=status_info["rvc"]["loaded"],
        available_emotions=status_info["available_emotions"],
        ready=status_info["ready"]
    )


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

async def _get_user_or_raise(user_id: int, db: AsyncSession) -> User:
    """Busca usuário ou levanta exceção se não encontrado."""
    from backend.utils.exceptions import UserNotFoundError
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise UserNotFoundError(user_id)
    
    return user


async def _get_profile_or_raise(
    profile_id: int,
    user_id: int,
    db: AsyncSession
) -> VoiceProfile:
    """Busca perfil de voz ou levanta exceção se não encontrado/não autorizado."""
    result = await db.execute(
        select(VoiceProfile)
        .where(VoiceProfile.id == profile_id)
        .where(
            (VoiceProfile.user_id == user_id) | (VoiceProfile.is_public.is_(True))
        )
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise VoiceProfileNotFoundError(profile_id)
    
    return profile
