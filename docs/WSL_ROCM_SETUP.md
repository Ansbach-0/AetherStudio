# 🚀 Configuração WSL + ROCm para AMD GPU (RX 7800XT)

## 📋 Visão Geral do Problema

O projeto usa Conda no Windows (F: pendrive), mas ROCm (AMD GPU acceleration) **só funciona no Linux**.  
A solução é usar **WSL2** para rodar o backend com PyTorch + ROCm, enquanto o frontend continua no Windows.

## 🏗️ Arquitetura Proposta

```
┌─────────────────────────────────────────────────────────────────┐
│                         WINDOWS HOST                             │
│  ┌─────────────────┐                    ┌─────────────────┐     │
│  │   Frontend      │ ◄──── HTTP ────► │   WSL2 Linux     │     │
│  │   (Bun/Vite)    │    localhost:8000  │   Backend        │     │
│  │   :5173         │                    │   PyTorch+ROCm   │     │
│  └─────────────────┘                    └─────────────────┘     │
│                                                │                 │
│                                         ┌──────▼──────┐         │
│                                         │   AMD GPU    │         │
│                                         │   7800XT     │         │
│                                         │   (ROCm)     │         │
│                                         └─────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 Passo a Passo

### 1. Verificar WSL2 e GPU

```powershell
# No Windows PowerShell
wsl --version
# Deve mostrar WSL version: 2.x.x

# Verificar se GPU está passando para WSL
wsl --list --verbose
```

### 2. Instalar Ubuntu no WSL (se ainda não tiver)

```powershell
wsl --install -d Ubuntu-22.04
wsl --set-version Ubuntu-22.04 2
```

### 3. Configurar ROCm no WSL2

```bash
# Dentro do WSL (Ubuntu)
# 1. Adicionar repositório AMD ROCm
wget https://repo.radeon.com/rocm/rocm.gpg.key -O - | sudo gpg --dearmor -o /etc/apt/keyrings/rocm.gpg
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/rocm.gpg] https://repo.radeon.com/rocm/apt/6.2 jammy main" | sudo tee /etc/apt/sources.list.d/rocm.list

# 2. Atualizar e instalar ROCm
sudo apt update
sudo apt install rocm-hip-libraries rocm-dev -y

# 3. Verificar instalação
rocminfo
# Deve mostrar sua GPU AMD
```

### 4. Acessar Pendrive F: no WSL

```bash
# O Windows monta automaticamente drives em /mnt/
cd /mnt/f/DesenvGit/VoiceCloner

# Para melhor performance, copiar projeto para Linux filesystem:
# (OPCIONAL - melhora I/O significativamente)
cp -r /mnt/f/DesenvGit/VoiceCloner ~/VoiceCloner
cd ~/VoiceCloner
```

### 5. Configurar Python Environment no WSL

```bash
# Instalar Miniconda no WSL
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# Criar ambiente
conda create -n voicecloner python=3.11 -y
conda activate voicecloner

# Instalar PyTorch com ROCm
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.2

# Instalar dependências do projeto
pip install -r requirements.txt

# Verificar GPU
python -c "import torch; print(f'ROCm available: {torch.cuda.is_available()}'); print(f'Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"CPU\"}')"
```

### 6. Rodar Backend no WSL

```bash
# No WSL
cd /mnt/f/DesenvGit/VoiceCloner
# ou: cd ~/VoiceCloner

conda activate voicecloner
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

> ⚠️ **IMPORTANTE**: Use `--host 0.0.0.0` para que o Windows possa acessar!

### 7. Rodar Frontend no Windows

```powershell
# No Windows PowerShell
cd F:\DesenvGit\VoiceCloner
bun run dev
```

## 📝 Script Automatizado (dev-wsl.ps1)

Crie um script para rodar backend no WSL automaticamente:

```powershell
# dev-wsl.ps1
param([switch]$BackendOnly, [switch]$FrontendOnly)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# WSL path for project
$WslPath = "/mnt/f/DesenvGit/VoiceCloner"

# Stop existing processes
Write-Host "Cleaning ports..." -ForegroundColor Cyan
Get-NetTCPConnection -LocalPort 8000,5173 -State Listen -ErrorAction SilentlyContinue | 
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 1

if (-not $FrontendOnly) {
    Write-Host "Starting Backend (WSL + ROCm)..." -ForegroundColor Green
    $wslCmd = "cd $WslPath && source ~/miniconda3/etc/profile.d/conda.sh && conda activate voicecloner && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"
    Start-Process wt -ArgumentList "wsl", "-d", "Ubuntu-22.04", "-e", "bash", "-c", "`"$wslCmd`""
}

if (-not $BackendOnly) {
    Write-Host "Waiting for backend to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    Write-Host "Starting Frontend..." -ForegroundColor Green
    Start-Process wt -ArgumentList "pwsh", "-NoExit", "-Command", "cd '$ScriptDir'; bun run dev"
}

Write-Host "Done! Backend: http://localhost:8000 | Frontend: http://localhost:5173" -ForegroundColor Cyan
```

## 🔍 Troubleshooting

### GPU não aparece no ROCm

```bash
# Verificar se kernel tem suporte
dmesg | grep -i amdgpu

# Verificar grupos
sudo usermod -aG video $USER
sudo usermod -aG render $USER
# Reiniciar WSL após isso
```

### Erro de permissão no /mnt/f

```bash
# Montar com permissões corretas
sudo umount /mnt/f
sudo mount -t drvfs F: /mnt/f -o metadata,uid=1000,gid=1000
```

### PyTorch não detecta GPU

```bash
# Verificar ROCm
rocm-smi

# Verificar variáveis de ambiente
export HSA_OVERRIDE_GFX_VERSION=11.0.0  # Para RDNA3 (7800XT)
export PYTORCH_ROCM_ARCH=gfx1100       # Para RDNA3

# Adicionar ao ~/.bashrc para persistir
echo 'export HSA_OVERRIDE_GFX_VERSION=11.0.0' >> ~/.bashrc
echo 'export PYTORCH_ROCM_ARCH=gfx1100' >> ~/.bashrc
```

## ⚡ Performance Tips

1. **Use Linux filesystem** para código fonte (~/VoiceCloner ao invés de /mnt/f)
2. **Modelos ML** devem ficar em ~/VoiceCloner/models (não no pendrive)
3. **Cache** do pip/conda também no Linux: `pip cache purge` se usando /mnt

## 🎯 Resumo de Comandos

```bash
# === SETUP ÚNICO ===
# No WSL:
conda create -n voicecloner python=3.11 -y
conda activate voicecloner
pip install torch --index-url https://download.pytorch.org/whl/rocm6.2
pip install -r /mnt/f/DesenvGit/VoiceCloner/requirements.txt

# === USO DIÁRIO ===
# Terminal 1 (WSL):
cd /mnt/f/DesenvGit/VoiceCloner && conda activate voicecloner && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 (Windows):
cd F:\DesenvGit\VoiceCloner && bun run dev
```
