#!/usr/bin/env python3
"""
Setup script for Hindi AI Assistant
This script helps set up the development environment
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return None

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def create_virtual_environment():
    """Create Python virtual environment"""
    if os.path.exists('venv'):
        print("📁 Virtual environment already exists")
        return True
    
    return run_command('python -m venv venv', 'Creating virtual environment')

def install_dependencies():
    """Install Python dependencies"""
    # Determine the correct pip path based on OS
    if os.name == 'nt':  # Windows
        pip_path = 'venv\\Scripts\\pip'
    else:  # Unix/Linux/macOS
        pip_path = 'venv/bin/pip'
    
    return run_command(f'{pip_path} install -r requirements.txt', 'Installing Python dependencies')

def create_env_file():
    """Create .env file from template if it doesn't exist"""
    if os.path.exists('.env'):
        print("📁 .env file already exists")
        return True
    
    if os.path.exists('.env.example'):
        shutil.copy('.env.example', '.env')
        print("✅ Created .env file from template")
        print("⚠️  Please edit .env file and add your Google Gemini API key")
        return True
    else:
        print("❌ .env.example file not found")
        return False

def create_directories():
    """Create necessary directories"""
    directories = [
        'backend/services',
        'models',
        'static/audio',
        'logs'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Created necessary directories")
    return True

def download_models():
    """Download required AI models"""
    print("📥 Model download will be handled during first run")
    print("   - Whisper models will be downloaded automatically")
    print("   - Coqui TTS models will be downloaded on first use")
    return True

def main():
    """Main setup function"""
    print("🚀 Setting up Hindi AI Assistant Development Environment")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create virtual environment
    if not create_virtual_environment():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("⚠️  Dependency installation failed. You may need to install manually.")
    
    # Create .env file
    if not create_env_file():
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        sys.exit(1)
    
    # Download models info
    download_models()
    
    print("\n" + "=" * 60)
    print("🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file and add your Google Gemini API key")
    print("2. Activate virtual environment:")
    if os.name == 'nt':  # Windows
        print("   venv\\Scripts\\activate")
    else:  # Unix/Linux/macOS
        print("   source venv/bin/activate")
    print("3. Run the development server:")
    print("   python backend/app.py")
    print("4. Open frontend/index.html in your browser")
    print("\n🔗 Get your free Gemini API key from: https://makersuite.google.com")

if __name__ == "__main__":
    main()