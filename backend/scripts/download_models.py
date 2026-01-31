#!/usr/bin/env python3
"""
Script para download dos modelos F5-TTS.

Este script baixa os modelos necessários do HuggingFace Hub
para uso local no projeto Voice Cloning SaaS.

Uso:
    python -m backend.scripts.download_models
    
    Ou diretamente:
    python backend/scripts/download_models.py

Modelos baixados:
    - F5-TTS Base: Modelo principal de Text-to-Speech (~2GB)
"""

import os
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path para imports
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

try:
    from huggingface_hub import hf_hub_download, snapshot_download
    HF_HUB_AVAILABLE = True
except ImportError:
    HF_HUB_AVAILABLE = False
    print("ERRO: huggingface-hub não está instalado.")
    print("Instale com: pip install huggingface-hub")

# Configurações
MODELS_DIR = ROOT_DIR / "models"
F5_TTS_REPO = "SWivid/F5-TTS"

# Arquivos para download
F5_TTS_FILES = [
    "F5TTS_Base/model_1200000.pt",  # Checkpoint principal (~2GB)
    "F5TTS_Base/vocab.txt",          # Vocabulário (opcional)
]


def create_directories():
    """Cria diretórios necessários para os modelos."""
    dirs = [
        MODELS_DIR,
        MODELS_DIR / "f5-tts",
        MODELS_DIR / "f5-tts" / "F5TTS_Base",
    ]
    
    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Diretório criado/verificado: {dir_path}")


def download_f5_tts():
    """
    Baixa modelo F5-TTS do HuggingFace.
    
    O modelo será baixado para ./models/f5-tts/
    """
    if not HF_HUB_AVAILABLE:
        print("ERRO: huggingface-hub não disponível")
        return False
    
    print("\n" + "="*60)
    print("Baixando modelo F5-TTS do HuggingFace...")
    print(f"Repositório: {F5_TTS_REPO}")
    print("="*60 + "\n")
    
    output_dir = MODELS_DIR / "f5-tts"
    
    try:
        for filename in F5_TTS_FILES:
            print(f"\nBaixando: {filename}")
            try:
                local_path = hf_hub_download(
                    repo_id=F5_TTS_REPO,
                    filename=filename,
                    local_dir=output_dir,
                    local_dir_use_symlinks=False
                )
                print(f"✓ Salvo em: {local_path}")
            except Exception as e:
                # Alguns arquivos podem não existir (vocab.txt é opcional)
                print(f"⚠ Aviso ao baixar {filename}: {e}")
                continue
        
        print(f"\n✓ Modelo F5-TTS baixado com sucesso em: {output_dir}")
        return True
        
    except Exception as e:
        print(f"\n✗ Erro ao baixar F5-TTS: {e}")
        return False


def download_vocos():
    """
    Baixa vocoder Vocos (opcional - baixado automaticamente pelo F5-TTS).
    
    O Vocos é o vocoder usado pelo F5-TTS para converter
    mel-spectrograms em áudio. Normalmente é baixado
    automaticamente na primeira execução.
    """
    print("\nNota: O vocoder Vocos será baixado automaticamente")
    print("na primeira execução do F5-TTS se necessário.")


def verify_installation():
    """Verifica se os modelos foram baixados corretamente."""
    print("\n" + "="*60)
    print("Verificando instalação dos modelos...")
    print("="*60 + "\n")
    
    # Verificar F5-TTS
    f5_model = MODELS_DIR / "f5-tts" / "F5TTS_Base" / "model_1200000.pt"
    if f5_model.exists():
        size_gb = f5_model.stat().st_size / (1024**3)
        print(f"✓ F5-TTS Base: {f5_model}")
        print(f"  Tamanho: {size_gb:.2f} GB")
    else:
        print(f"✗ F5-TTS Base não encontrado: {f5_model}")
    
    print()


def main():
    """Função principal do script."""
    print("\n" + "="*60)
    print("Voice Cloning SaaS - Download de Modelos")
    print("="*60)
    
    if not HF_HUB_AVAILABLE:
        print("\nERRO: Instale huggingface-hub primeiro:")
        print("  pip install huggingface-hub")
        sys.exit(1)
    
    # Criar diretórios
    print("\n[1/3] Criando diretórios...")
    create_directories()
    
    # Baixar F5-TTS
    print("\n[2/3] Baixando F5-TTS...")
    success = download_f5_tts()
    
    # Verificar instalação
    print("\n[3/3] Verificando instalação...")
    verify_installation()
    
    if success:
        print("\n" + "="*60)
        print("✓ Download concluído com sucesso!")
        print("="*60)
        print("\nPróximos passos:")
        print("1. Inicie o servidor: uvicorn backend.main:app --reload")
        print("2. Acesse a documentação: http://localhost:8000/docs")
    else:
        print("\n" + "="*60)
        print("⚠ Download concluído com alguns avisos")
        print("="*60)
        print("\nVerifique os logs acima para mais detalhes.")
    
    print()


if __name__ == "__main__":
    main()
