"""
Serviço de detecção automática de idioma.

Detecta o idioma de textos para uso no pipeline de TTS,
permitindo seleção automática da voz correta.
"""

from typing import Any, Dict, List, Optional

from backend.utils.logger import get_logger

# Import condicional do langdetect
try:
    from langdetect import detect, detect_langs, LangDetectException
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    LangDetectException = Exception

logger = get_logger(__name__)


class LanguageDetector:
    """
    Detecta idioma de texto automaticamente.
    
    Usa a biblioteca langdetect para identificar o idioma
    e mapeia para os códigos de idioma suportados pelo TTS.
    
    Attributes:
        SUPPORTED_LANGUAGES: Lista de códigos de idioma suportados
        LANGUAGE_MAP: Mapeamento de código curto para código completo
        DEFAULT_LANGUAGE: Idioma padrão quando detecção falha
    """
    
    # Idiomas suportados pelo sistema
    SUPPORTED_LANGUAGES = ["pt", "en", "es", "fr", "de", "it", "ja", "zh", "ko"]
    
    # Mapeamento de código ISO 639-1 para código completo
    LANGUAGE_MAP = {
        "pt": "pt-BR",
        "en": "en-US",
        "es": "es-ES",
        "fr": "fr-FR",
        "de": "de-DE",
        "it": "it-IT",
        "ja": "ja-JP",
        "zh": "zh-CN",
        "ko": "ko-KR",
    }
    
    # Mapeamento reverso (código completo para curto)
    REVERSE_MAP = {v: k for k, v in LANGUAGE_MAP.items()}
    
    # Idioma padrão
    DEFAULT_LANGUAGE = "pt-BR"
    
    def __init__(self):
        """Inicializa o detector de idioma."""
        self.available = LANGDETECT_AVAILABLE
        
        if not self.available:
            logger.warning(
                "langdetect não instalado. "
                "Detecção de idioma usará fallback para pt-BR."
            )
    
    def detect(self, text: str) -> str:
        """
        Detecta o idioma do texto.
        
        Args:
            text: Texto para detectar idioma
        
        Returns:
            str: Código de idioma no formato "xx-XX" (ex: "pt-BR")
        """
        if not text or not text.strip():
            logger.debug("Texto vazio, retornando idioma padrão")
            return self.DEFAULT_LANGUAGE
        
        if not self.available:
            return self.DEFAULT_LANGUAGE
        
        try:
            # Detectar idioma com langdetect
            lang_code = detect(text)
            
            # Mapear para código completo
            full_code = self.LANGUAGE_MAP.get(lang_code, self.DEFAULT_LANGUAGE)
            
            logger.debug(f"Idioma detectado: {lang_code} -> {full_code}")
            return full_code
            
        except LangDetectException as e:
            logger.warning(f"Erro na detecção de idioma: {e}")
            return self.DEFAULT_LANGUAGE
        except Exception as e:
            logger.error(f"Erro inesperado na detecção: {e}")
            return self.DEFAULT_LANGUAGE
    
    def detect_with_confidence(self, text: str) -> Dict[str, float]:
        """
        Detecta idioma com probabilidades para cada idioma.
        
        Args:
            text: Texto para análise
        
        Returns:
            Dict[str, float]: Mapa de idioma -> probabilidade
        """
        if not text or not text.strip():
            return {self.DEFAULT_LANGUAGE: 1.0}
        
        if not self.available:
            return {self.DEFAULT_LANGUAGE: 1.0}
        
        try:
            # Obter lista de idiomas com probabilidades
            results = detect_langs(text)
            
            probabilities = {}
            for result in results:
                lang_code = str(result.lang)
                full_code = self.LANGUAGE_MAP.get(lang_code)
                
                if full_code:
                    probabilities[full_code] = result.prob
            
            # Se nenhum idioma suportado foi detectado
            if not probabilities:
                return {self.DEFAULT_LANGUAGE: 0.5}
            
            logger.debug(f"Probabilidades de idioma: {probabilities}")
            return probabilities
            
        except Exception as e:
            logger.error(f"Erro na detecção com confiança: {e}")
            return {self.DEFAULT_LANGUAGE: 1.0}
    
    def is_supported(self, language_code: str) -> bool:
        """
        Verifica se um idioma é suportado.
        
        Args:
            language_code: Código do idioma (ex: "pt", "pt-BR")
        
        Returns:
            bool: True se suportado
        """
        # Verificar código curto
        if language_code in self.SUPPORTED_LANGUAGES:
            return True
        
        # Verificar código completo
        if language_code in self.LANGUAGE_MAP.values():
            return True
        
        return False
    
    def normalize_language_code(self, code: str) -> str:
        """
        Normaliza código de idioma para formato completo.
        
        Args:
            code: Código de idioma (ex: "pt", "PT", "pt-BR")
        
        Returns:
            str: Código normalizado (ex: "pt-BR")
        """
        if not code:
            return self.DEFAULT_LANGUAGE
        
        # Limpar código
        code = code.strip().lower()
        
        # Se já está no formato completo
        if "-" in code:
            # Normalizar: "pt-br" -> "pt-BR"
            parts = code.split("-")
            return f"{parts[0].lower()}-{parts[1].upper()}"
        
        # Se é código curto, mapear
        return self.LANGUAGE_MAP.get(code, self.DEFAULT_LANGUAGE)
    
    def get_supported_languages(self) -> List[Dict[str, str]]:
        """
        Retorna lista de idiomas suportados com nomes.
        
        Returns:
            List[Dict]: Lista com código e nome de cada idioma
        """
        language_names = {
            "pt-BR": "Português (Brasil)",
            "en-US": "English (US)",
            "es-ES": "Español (España)",
            "fr-FR": "Français",
            "de-DE": "Deutsch",
            "it-IT": "Italiano",
            "ja-JP": "日本語",
            "zh-CN": "中文 (简体)",
            "ko-KR": "한국어",
        }
        
        return [
            {"code": code, "name": language_names.get(code, code)}
            for code in self.LANGUAGE_MAP.values()
        ]
    
    @property
    def status(self) -> Dict[str, Any]:
        """Retorna status do detector."""
        return {
            "available": self.available,
            "default_language": self.DEFAULT_LANGUAGE,
            "supported_count": len(self.SUPPORTED_LANGUAGES),
        }


# Instância singleton para uso global
_detector_instance: Optional[LanguageDetector] = None


def get_language_detector() -> LanguageDetector:
    """
    Retorna instância singleton do detector de idioma.
    
    Returns:
        LanguageDetector: Instância do detector
    """
    global _detector_instance
    
    if _detector_instance is None:
        _detector_instance = LanguageDetector()
    
    return _detector_instance
