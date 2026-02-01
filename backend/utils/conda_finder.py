"""
Utilitário para detecção automática de instalações Conda/Miniconda.

Este módulo detecta automaticamente o caminho do conda independente
de estar ou não no PATH do sistema, resolvendo o problema de
"miniconda recomenda não adicionar ao PATH".
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from functools import lru_cache

from backend.utils.logger import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def find_conda_installation() -> Optional[Path]:
    """
    Detecta automaticamente a instalação do Conda/Miniconda.
    
    Procura nas seguintes localizações (em ordem):
    1. Variável de ambiente CONDA_EXE (se conda já foi ativado)
    2. Variável de ambiente CONDA_PREFIX (ambiente ativo)
    3. Diretórios comuns do Windows
    4. Diretórios comuns do Linux/Mac
    5. Registro do Windows (se aplicável)
    
    Returns:
        Path para o diretório raiz do conda, ou None se não encontrado
    """
    
    # 1. Verificar se já temos CONDA_EXE definido
    conda_exe = os.environ.get("CONDA_EXE")
    if conda_exe:
        conda_path = Path(conda_exe)
        if conda_path.exists():
            # CONDA_EXE aponta para Scripts/conda.exe, queremos o diretório raiz
            conda_root = conda_path.parent.parent
            logger.info(f"Conda encontrado via CONDA_EXE: {conda_root}")
            return conda_root
    
    # 2. Verificar CONDA_PREFIX (ambiente ativo)
    conda_prefix = os.environ.get("CONDA_PREFIX")
    if conda_prefix:
        prefix_path = Path(conda_prefix)
        # Subir até encontrar o conda base
        if (prefix_path / "condabin").exists():
            logger.info(f"Conda base encontrado via CONDA_PREFIX: {prefix_path}")
            return prefix_path
        # Se estamos em um env, o base está acima
        potential_base = prefix_path.parent.parent
        if (potential_base / "condabin").exists():
            logger.info(f"Conda base encontrado via CONDA_PREFIX parent: {potential_base}")
            return potential_base
    
    # 3. Locais comuns no Windows
    if sys.platform == "win32":
        windows_locations = [
            # Miniconda padrão
            Path.home() / "miniconda3",
            Path.home() / "Miniconda3",
            # Anaconda padrão
            Path.home() / "anaconda3",
            Path.home() / "Anaconda3",
            # AppData (instalação por usuário)
            Path.home() / "AppData" / "Local" / "miniconda3",
            Path.home() / "AppData" / "Local" / "Continuum" / "miniconda3",
            Path.home() / "AppData" / "Local" / "Continuum" / "anaconda3",
            # Instalação global
            Path("C:/miniconda3"),
            Path("C:/Miniconda3"),
            Path("C:/anaconda3"),
            Path("C:/Anaconda3"),
            Path("C:/ProgramData/miniconda3"),
            Path("C:/ProgramData/Miniconda3"),
            Path("C:/ProgramData/anaconda3"),
        ]
        
        for location in windows_locations:
            if location.exists() and (location / "condabin").exists():
                logger.info(f"Conda encontrado em: {location}")
                return location
    
    # 4. Locais comuns no Linux/Mac
    else:
        unix_locations = [
            Path.home() / "miniconda3",
            Path.home() / "anaconda3",
            Path("/opt/miniconda3"),
            Path("/opt/anaconda3"),
            Path("/usr/local/miniconda3"),
            Path("/usr/local/anaconda3"),
        ]
        
        for location in unix_locations:
            if location.exists() and (location / "condabin").exists():
                logger.info(f"Conda encontrado em: {location}")
                return location
    
    # 5. Tentar via 'where' no Windows ou 'which' no Unix
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ["where", "conda"],
                capture_output=True,
                text=True,
                timeout=5
            )
        else:
            result = subprocess.run(
                ["which", "conda"],
                capture_output=True,
                text=True,
                timeout=5
            )
        
        if result.returncode == 0 and result.stdout.strip():
            conda_path = Path(result.stdout.strip().split("\n")[0])
            if conda_path.exists():
                # Navegar até a raiz do conda
                conda_root = conda_path.parent.parent
                if (conda_root / "condabin").exists():
                    logger.info(f"Conda encontrado via which/where: {conda_root}")
                    return conda_root
    except Exception:
        pass
    
    logger.warning("Instalação do Conda não encontrada automaticamente")
    return None


@lru_cache(maxsize=1)
def get_conda_executable() -> Tuple[Optional[str], Optional[str]]:
    """
    Retorna os caminhos para o executável conda e conda-hook script.
    
    Returns:
        Tuple (conda_exe_path, conda_hook_path) ou (None, None) se não encontrado
    """
    conda_root = find_conda_installation()
    
    if conda_root is None:
        return None, None
    
    if sys.platform == "win32":
        conda_exe = conda_root / "Scripts" / "conda.exe"
        conda_hook = conda_root / "shell" / "condabin" / "conda-hook.ps1"
    else:
        conda_exe = conda_root / "bin" / "conda"
        conda_hook = conda_root / "etc" / "profile.d" / "conda.sh"
    
    if conda_exe.exists():
        return str(conda_exe), str(conda_hook) if conda_hook.exists() else None
    
    return None, None


def get_conda_run_command(env_name: str) -> list:
    """
    Gera o comando para executar um script Python em um ambiente conda.
    
    Args:
        env_name: Nome do ambiente conda
        
    Returns:
        Lista com os argumentos do comando
        
    Raises:
        RuntimeError: Se conda não for encontrado
    """
    conda_exe, _ = get_conda_executable()
    
    if conda_exe is None:
        raise RuntimeError(
            "Conda não encontrado. Por favor, instale Miniconda ou Anaconda e reinicie o servidor."
        )
    
    return [conda_exe, "run", "-n", env_name, "--no-capture-output"]


def get_conda_python_executable(env_name: str) -> Optional[str]:
    """
    Retorna o caminho do Python de um ambiente conda específico.
    
    Args:
        env_name: Nome do ambiente conda
        
    Returns:
        Caminho para o executável Python ou None
    """
    conda_root = find_conda_installation()
    
    if conda_root is None:
        return None
    
    if sys.platform == "win32":
        python_path = conda_root / "envs" / env_name / "python.exe"
    else:
        python_path = conda_root / "envs" / env_name / "bin" / "python"
    
    if python_path.exists():
        return str(python_path)
    
    return None


def conda_env_path(env_name: str) -> Optional[Path]:
    """Retorna o caminho do ambiente conda se o conda base existir."""
    conda_root = find_conda_installation()
    if conda_root is None:
        return None
    return conda_root / "envs" / env_name


def conda_env_exists(env_name: str) -> bool:
    """Verifica se um ambiente conda existe e contém um Python executável."""
    env_path = conda_env_path(env_name)
    if env_path is None or not env_path.exists():
        return False
    return get_conda_python_executable(env_name) is not None


def create_conda_env(env_name: str, python_version: str = "3.11") -> None:
    """Cria um ambiente conda com a versão do Python especificada."""
    conda_exe, _ = get_conda_executable()
    if conda_exe is None:
        raise RuntimeError("Conda não encontrado para criar ambiente RVC")

    cmd = [conda_exe, "create", "-y", "-n", env_name, f"python={python_version}"]
    logger.info(f"Criando ambiente conda: {env_name} (Python {python_version})")
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())


def install_requirements_in_env(env_name: str, requirements_path: Path) -> None:
    """Instala dependências via pip dentro do ambiente conda."""
    conda_exe, _ = get_conda_executable()
    if conda_exe is None:
        raise RuntimeError("Conda não encontrado para instalar dependências RVC")

    # Fix for OmegaConf 2.0.6 metadata with newer pip
    pip_cmd = [
        conda_exe,
        "run",
        "-n",
        env_name,
        "python",
        "-m",
        "pip",
        "install",
        "pip<24.1",
    ]
    pip_result = subprocess.run(pip_cmd, capture_output=True, text=True, check=False)
    if pip_result.returncode != 0:
        raise RuntimeError(pip_result.stderr.strip() or pip_result.stdout.strip())

    # Install uv for faster dependency resolution
    uv_cmd = [
        conda_exe,
        "run",
        "-n",
        env_name,
        "python",
        "-m",
        "pip",
        "install",
        "uv",
    ]
    uv_result = subprocess.run(uv_cmd, capture_output=True, text=True, check=False)
    if uv_result.returncode != 0:
        logger.warning("Falha ao instalar uv, usando pip: %s", uv_result.stderr.strip() or uv_result.stdout.strip())

    # Prefer uv pip when available
    uv_pip_cmd = [
        conda_exe,
        "run",
        "-n",
        env_name,
        "python",
        "-m",
        "uv",
        "pip",
        "install",
        "-r",
        str(requirements_path),
    ]
    logger.info(f"Instalando dependências RVC: {requirements_path}")
    result = subprocess.run(uv_pip_cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        # Fallback to pip
        pip_cmd = [
            conda_exe,
            "run",
            "-n",
            env_name,
            "python",
            "-m",
            "pip",
            "install",
            "-r",
            str(requirements_path),
        ]
        logger.warning("uv pip falhou, tentando pip: %s", result.stderr.strip() or result.stdout.strip())
        result = subprocess.run(pip_cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())


def ensure_conda_env(
    env_name: str,
    requirements_path: Path,
    python_version: str = "3.11"
) -> dict:
    """Garante que o ambiente conda exista e tenha dependências RVC instaladas."""
    result = {
        "env_name": env_name,
        "created": False,
        "dependencies_installed": False,
    }

    if conda_env_exists(env_name):
        if requirements_path.exists():
            install_requirements_in_env(env_name, requirements_path)
            result["dependencies_installed"] = True
        result["status"] = "ready"
        return result

    create_conda_env(env_name, python_version=python_version)
    result["created"] = True

    if requirements_path.exists():
        install_requirements_in_env(env_name, requirements_path)
        result["dependencies_installed"] = True
        result["status"] = "ready"
    else:
        result["status"] = "requirements_missing"
        logger.warning(f"Arquivo de requirements não encontrado: {requirements_path}")

    return result


def initialize_conda_environment() -> dict:
    """
    Inicializa as variáveis de ambiente necessárias para usar conda.
    
    Esta função deve ser chamada no startup do servidor para garantir
    que o conda esteja disponível para subprocessos.
    
    Returns:
        Dict com informações sobre a configuração do conda
    """
    conda_root = find_conda_installation()
    conda_exe, conda_hook = get_conda_executable()
    
    result = {
        "conda_found": conda_root is not None,
        "conda_root": str(conda_root) if conda_root else None,
        "conda_exe": conda_exe,
        "conda_hook": conda_hook,
    }
    
    if conda_root:
        # Definir variáveis de ambiente para subprocessos
        os.environ["CONDA_ROOT"] = str(conda_root)
        
        if conda_exe:
            os.environ["CONDA_EXE"] = conda_exe
            
        # Adicionar condabin ao PATH para subprocessos (não o bin/Scripts principal)
        condabin = str(conda_root / "condabin")
        current_path = os.environ.get("PATH", "")
        
        if condabin not in current_path:
            os.environ["PATH"] = f"{condabin}{os.pathsep}{current_path}"
            result["path_updated"] = True
        else:
            result["path_updated"] = False
            
        logger.info(f"Ambiente conda inicializado: {conda_root}")
    else:
        logger.warning("Conda não encontrado - funcionalidades RVC podem não funcionar")
    
    return result


# Executar detecção no import do módulo para logging antecipado
_conda_info = None

def get_conda_info() -> dict:
    """Retorna informações sobre a instalação do conda."""
    global _conda_info
    if _conda_info is None:
        _conda_info = initialize_conda_environment()
    return _conda_info
