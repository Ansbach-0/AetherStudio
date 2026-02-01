"""
Script standalone para inferência RVC via subprocesso.

Suporta inferência via RVC WebUI com PyTorch ROCm/DirectML para GPUs AMD.

IMPORTANTE: Este script precisa parsear seus próprios argumentos ANTES de 
importar módulos do RVC WebUI, pois o Config do RVC também usa argparse.
"""

from __future__ import annotations

import contextlib
import os
import sys
from pathlib import Path


def get_args_dict() -> dict:
    """
    Parse argumentos manualmente para evitar conflitos com argparse do RVC.
    
    Os argumentos precisam ser parseados ANTES de importar módulos do RVC
    porque o Config do RVC também chama argparse.parse_args().
    """
    args = {
        "repo_dir": None,
        "model_path": None, 
        "index_path": "",
        "input": None,
        "output": None,
        "pitch": 0,
        "index_rate": 0.75,
        "f0method": "rmvpe",
        "device": "cpu",
        "threads": 4,
        "use_rocm": False,
        "hsa_gfx_version": "11.0.0",
        "rocm_arch": "gfx1100"
    }
    
    argv = sys.argv[1:]  # Skip script name
    i = 0
    while i < len(argv):
        arg = argv[i]
        
        if arg == "--repo-dir" and i + 1 < len(argv):
            args["repo_dir"] = argv[i + 1]
            i += 2
        elif arg == "--model-path" and i + 1 < len(argv):
            args["model_path"] = argv[i + 1]
            i += 2
        elif arg == "--index-path" and i + 1 < len(argv):
            args["index_path"] = argv[i + 1]
            i += 2
        elif arg == "--input" and i + 1 < len(argv):
            args["input"] = argv[i + 1]
            i += 2
        elif arg == "--output" and i + 1 < len(argv):
            args["output"] = argv[i + 1]
            i += 2
        elif arg == "--pitch" and i + 1 < len(argv):
            args["pitch"] = int(argv[i + 1])
            i += 2
        elif arg == "--index-rate" and i + 1 < len(argv):
            args["index_rate"] = float(argv[i + 1])
            i += 2
        elif arg == "--f0method" and i + 1 < len(argv):
            args["f0method"] = argv[i + 1]
            i += 2
        elif arg == "--device" and i + 1 < len(argv):
            args["device"] = argv[i + 1]
            i += 2
        elif arg == "--threads" and i + 1 < len(argv):
            args["threads"] = int(argv[i + 1])
            i += 2
        elif arg == "--use-rocm":
            args["use_rocm"] = True
            i += 1
        elif arg == "--hsa-gfx-version" and i + 1 < len(argv):
            args["hsa_gfx_version"] = argv[i + 1]
            i += 2
        elif arg == "--rocm-arch" and i + 1 < len(argv):
            args["rocm_arch"] = argv[i + 1]
            i += 2
        else:
            # Skip unknown args
            i += 1
    
    return args


# Parse args ANTES de qualquer import que possa usar argparse
ARGS = get_args_dict()

# Validar argumentos obrigatórios
if not ARGS["repo_dir"]:
    print("Erro: --repo-dir é obrigatório", file=sys.stderr)
    sys.exit(1)
if not ARGS["model_path"]:
    print("Erro: --model-path é obrigatório", file=sys.stderr)
    sys.exit(1)
if not ARGS["input"]:
    print("Erro: --input é obrigatório", file=sys.stderr)
    sys.exit(1)
if not ARGS["output"]:
    print("Erro: --output é obrigatório", file=sys.stderr)
    sys.exit(1)

# Configurar variáveis de ambiente ROCm ANTES de importar torch
if ARGS["use_rocm"] or "cuda" in ARGS["device"]:
    os.environ["HSA_OVERRIDE_GFX_VERSION"] = ARGS["hsa_gfx_version"]
    os.environ["ROCR_VISIBLE_DEVICES"] = "0"
    os.environ["HIP_VISIBLE_DEVICES"] = "0"
    os.environ["PYTORCH_ROCM_ARCH"] = ARGS["rocm_arch"]

# Limpar sys.argv ANTES de importar módulos do RVC para evitar conflitos de argparse
# O Config do RVC WebUI vai parsear sys.argv novamente
sys.argv = ["rvc_inference_runner.py"]

# Imports que dependem de torch
import numpy as np

try:
    import torch
    # WORKAROUND: PyTorch 2.6+ usa weights_only=True por padrão, que quebra fairseq/RVC
    # Precisamos fazer patch global do torch.load para manter compatibilidade
    _original_torch_load = torch.load
    def _patched_torch_load(*args, **kwargs):
        if 'weights_only' not in kwargs:
            kwargs['weights_only'] = False
        return _original_torch_load(*args, **kwargs)
    torch.load = _patched_torch_load
except Exception as exc:
    raise RuntimeError("PyTorch é necessário para inferência RVC") from exc

try:
    import librosa
except Exception as exc:
    raise RuntimeError("librosa é necessário para inferência RVC") from exc

try:
    import soundfile as sf
except Exception as exc:
    raise RuntimeError("soundfile é necessário para inferência RVC") from exc


class DummyQueue:
    """
    Queue dummy que não usa multiprocessing.Manager().
    
    No Windows com 'conda run', multiprocessing.Manager() causa deadlock.
    As queues inp_q/opt_q do RVC são usadas APENAS quando:
    - f0method == "harvest" E n_cpu > 1
    
    Para métodos rmvpe/crepe/fcpe/pm ou harvest com n_cpu=1, as queues não são usadas.
    Esta classe permite inicializar o RVC sem Manager e lança erro se alguém
    tentar usar harvest com múltiplos CPUs.
    """
    def put(self, item):
        raise RuntimeError(
            "Multiprocessing queues not supported on Windows. "
            "Use f0method=rmvpe/crepe/fcpe/pm, or set threads=1 for harvest."
        )
    
    def get(self):
        raise RuntimeError(
            "Multiprocessing queues not supported on Windows. "
            "Use f0method=rmvpe/crepe/fcpe/pm, or set threads=1 for harvest."
        )


@contextlib.contextmanager
def temp_cwd(path: Path):
    """Context manager para trocar diretório temporariamente."""
    prev = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev)


def main() -> int:
    """Executa inferência RVC."""
    # Log de device
    device_str = ARGS["device"]
    print(f"[RVC Infer] Device solicitado: {device_str}", file=sys.stderr)
    
    if torch.cuda.is_available():
        device_name = torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else "Unknown"
        print(f"[RVC Infer] GPU detectada: {device_name}", file=sys.stderr)
        if hasattr(torch.version, 'hip') and torch.version.hip:
            print(f"[RVC Infer] ROCm: {torch.version.hip}", file=sys.stderr)
    
    # DirectML não funciona com RVC diretamente, usar CPU
    if device_str.startswith("privateuseone"):
        print("[RVC Infer] DirectML detectado, usando CPU para RVC", file=sys.stderr)
        device_str = "cpu"

    repo_dir = Path(ARGS["repo_dir"]).resolve()
    model_path = Path(ARGS["model_path"]).resolve()
    index_path = Path(ARGS["index_path"]).resolve() if ARGS["index_path"] else ""

    if not repo_dir.exists():
        raise RuntimeError(f"RVC repo não encontrado: {repo_dir}")
    if not model_path.exists():
        raise RuntimeError(f"RVC model não encontrado: {model_path}")

    print(f"[RVC Infer] Repo: {repo_dir}", file=sys.stderr)
    print(f"[RVC Infer] Model: {model_path}", file=sys.stderr)
    print(f"[RVC Infer] Input: {ARGS['input']}", file=sys.stderr)

    # Adicionar repo do RVC ao path
    if str(repo_dir) not in sys.path:
        sys.path.insert(0, str(repo_dir))

    # MONKEYPATCH: Substituir multiprocessing.Manager por DummyManager
    # O rvc_for_realtime.py cria um Manager global (mm = M()) que trava no Windows
    import multiprocessing
    
    class DummyManager:
        """Manager falso que não cria processo servidor."""
        def Queue(self):
            return DummyQueue()
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
    
    # Guardar original e substituir
    _original_manager = multiprocessing.Manager
    multiprocessing.Manager = DummyManager

    # Importar módulos do RVC (sys.argv já foi limpo acima)
    from configs.config import Config
    from tools.rvc_for_realtime import RVC
    
    # Restaurar Manager original (caso algo precise depois)
    multiprocessing.Manager = _original_manager

    # Criar config do RVC com diretório correto
    with temp_cwd(repo_dir):
        config = Config()

    # Configurar device e opções
    config.device = torch.device(device_str)
    if "cpu" in device_str:
        config.is_half = False
    
    if ARGS["threads"]:
        config.n_cpu = ARGS["threads"]

    print(f"[RVC Infer] Config device: {config.device}, is_half: {config.is_half}", file=sys.stderr)

    # Carregar áudio de entrada
    print(f"[RVC Infer] Carregando áudio...", file=sys.stderr)
    audio, sr = librosa.load(str(ARGS["input"]), sr=16000, mono=True)
    audio = audio.astype(np.float32)
    print(f"[RVC Infer] Áudio carregado: {len(audio)} samples, {sr}Hz", file=sys.stderr)

    audio_tensor = torch.from_numpy(audio).to(config.device)

    # Instanciar RVC
    # NOTA: Não usar multiprocessing.Manager() no Windows - causa deadlock com 'conda run'.
    # DummyQueue funciona porque rmvpe/crepe/fcpe/pm não usam as queues.
    inp_q = DummyQueue()
    opt_q = DummyQueue()

    print(f"[RVC Infer] Inicializando modelo RVC...", file=sys.stderr)
    with temp_cwd(repo_dir):
        rvc = RVC(
            ARGS["pitch"],
            str(model_path),
            str(index_path) if index_path else "",
            float(ARGS["index_rate"]),
            config.n_cpu,
            inp_q,
            opt_q,
            config,
            None
        )

        print(f"[RVC Infer] Executando inferência...", file=sys.stderr)
        converted = rvc.infer(
            audio_tensor,
            audio_tensor.shape[0],
            0,
            audio_tensor.shape[0],
            ARGS["f0method"]
        )

    # Converter resultado para numpy
    if torch.is_tensor(converted):
        converted_audio = converted.detach().cpu().numpy().astype(np.float32)
    else:
        converted_audio = np.asarray(converted, dtype=np.float32)

    # Obter sample rate de saída
    target_sr = getattr(rvc, "tgt_sr", sr)
    
    # Salvar áudio
    print(f"[RVC Infer] Salvando: {ARGS['output']} ({target_sr}Hz)", file=sys.stderr)
    sf.write(str(ARGS["output"]), converted_audio, int(target_sr))

    print(f"[RVC Infer] Conversão concluída com sucesso!", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
