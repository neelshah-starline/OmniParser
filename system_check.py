#!/usr/bin/env python3
"""
Comprehensive system diagnostic script for OmniParser
Checks Python, PyTorch, CUDA, Transformers, and other key dependencies
"""

import sys
import platform
import subprocess

def run_command(cmd):
    """Run a command and return output, or None if failed"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else None
    except:
        return None

def check_python():
    """Check Python version and info"""
    print("🐍 Python Information:")
    print(f"   Version: {sys.version}")
    print(f"   Platform: {platform.platform()}")
    print(f"   Architecture: {platform.architecture()}")
    print()

def check_pytorch():
    """Check PyTorch and CUDA"""
    print("🔥 PyTorch Information:")
    try:
        import torch
        print(f"   PyTorch version: {torch.__version__}")

        # CUDA info
        cuda_available = torch.cuda.is_available()
        print(f"   CUDA available: {cuda_available}")

        if cuda_available:
            print(f"   CUDA version: {torch.version.cuda}")
            print(f"   CUDNN version: {torch.backends.cudnn.version()}")
            print(f"   GPU count: {torch.cuda.device_count()}")

            for i in range(torch.cuda.device_count()):
                print(f"   GPU {i}: {torch.cuda.get_device_name(i)}")
                print(f"   GPU {i} memory: {torch.cuda.get_device_properties(i).total_memory / 1024**3:.1f} GB")
        else:
            print("   Running on CPU")

        # Current device
        device = torch.device('cuda' if cuda_available else 'cpu')
        print(f"   Using device: {device}")

    except ImportError:
        print("   ❌ PyTorch not installed")
    print()

def check_transformers():
    """Check Transformers library"""
    print("🤗 Transformers Information:")
    try:
        import transformers
        print(f"   Transformers version: {transformers.__version__}")
    except ImportError:
        print("   ❌ Transformers not installed")
    print()

def check_key_dependencies():
    """Check other key dependencies"""
    print("📦 Key Dependencies:")

    dependencies = [
        ('numpy', 'numpy'),
        ('opencv-python', 'cv2'),
        ('PIL', 'PIL'),
        ('easyocr', 'easyocr'),
        ('supervision', 'supervision'),
        ('gradio', 'gradio'),
        ('ultralytics', 'ultralytics'),
        ('huggingface_hub', 'huggingface_hub'),
    ]

    for name, import_name in dependencies:
        try:
            __import__(import_name)
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ❌ {name} - not installed")
    print()

def check_nvidia_tools():
    """Check NVIDIA tools and drivers"""
    print("🖥️  NVIDIA Tools:")

    # Check nvidia-smi
    nvidia_smi = run_command("nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits")
    if nvidia_smi:
        print("   ✅ NVIDIA drivers detected")
        print("   GPU details:")
        for line in nvidia_smi.split('\n'):
            if line.strip():
                name, memory = line.split(', ')
                print(f"      {name}: {memory} MB")
    else:
        print("   ❌ NVIDIA drivers not detected or nvidia-smi not available")

    # Check NVCC
    nvcc_version = run_command("nvcc --version")
    if nvcc_version:
        print("   ✅ NVCC (CUDA compiler) available")
        # Extract version from output
        for line in nvcc_version.split('\n'):
            if 'release' in line:
                print(f"      {line.strip()}")
                break
    else:
        print("   ❌ NVCC not available")

    print()

def check_huggingface():
    """Check Hugging Face tools"""
    print("🤗 Hugging Face Tools:")

    # Check hf command
    hf_version = run_command("hf --version")
    if hf_version:
        print(f"   ✅ Hugging Face CLI: {hf_version}")
    else:
        print("   ❌ Hugging Face CLI not available")

    # Check if models directory exists
    import os
    if os.path.exists('weights'):
        print("   ✅ Weights directory exists")
        subdirs = [d for d in os.listdir('weights') if os.path.isdir(os.path.join('weights', d))]
        if subdirs:
            print(f"   Model directories: {', '.join(subdirs)}")
        else:
            print("   ⚠️  Weights directory empty - run download_weights.bat")
    else:
        print("   ❌ Weights directory missing - run download_weights.bat")

    print()

def main():
    """Main diagnostic function"""
    print("=" * 60)
    print("🔍 OmniParser System Diagnostic")
    print("=" * 60)
    print()

    check_python()
    check_pytorch()
    check_transformers()
    check_key_dependencies()
    check_nvidia_tools()
    check_huggingface()

    print("=" * 60)
    print("✅ Diagnostic complete!")
    print("If you see any ❌ items, you may need to install missing dependencies.")
    print("=" * 60)

if __name__ == "__main__":
    main()
