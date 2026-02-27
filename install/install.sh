#!/bin/bash

# Descriptor Installation Script
# Installs the descriptor video processing pipeline with CLI access
# Usage: ./install.sh

set -e

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="descriptor"
VENV_DIR="$SCRIPT_DIR/venv"
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"
CLI_SCRIPT="$SCRIPT_DIR/descriptor-cli"
SYSTEM_BIN="/usr/local/bin/descriptor"
PYTHON_CMD="python3"

# Logging function
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root (should not be)
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root."
        log_error "Please run without sudo."
        exit 1
    fi
}

# Check macOS and Apple Silicon
check_system() {
    log_info "Checking system requirements..."
    
    # Check if macOS
    if [[ "$OSTYPE" != "darwin"* ]]; then
        log_error "This script only works on macOS."
        exit 1
    fi
    
    # Check Apple Silicon
    ARCH=$(uname -m)
    if [[ "$ARCH" != "arm64" ]]; then
        log_error "This script requires Apple Silicon (arm64). Current architecture: $ARCH"
        exit 1
    fi
    
    log_success "System requirements met (macOS + Apple Silicon)"
}

# Check Python version
check_python() {
    log_info "Checking Python installation..."
    
    # Prefer Homebrew Python
    if command -v /opt/homebrew/bin/python3.11 >/dev/null 2>&1; then
        PYTHON_CMD="/opt/homebrew/bin/python3.11"
    elif command -v python3 >/dev/null 2>&1; then
        PYTHON_CMD="python3"
    else
        log_warning "Python 3 not found. Installing python@3.11 via Homebrew..."
        brew install python@3.11
        eval "$(/opt/homebrew/bin/brew shellenv)"
        PYTHON_CMD="/opt/homebrew/bin/python3.11"
    fi
    
    PYTHON_PATH="$PYTHON_CMD"
    log_info "Python3 located at: $PYTHON_PATH"
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [[ $PYTHON_MAJOR -lt 3 ]] || [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -lt 10 ]]; then
        log_error "Python 3.10+ required. Found: $PYTHON_VERSION at $PYTHON_PATH"
        exit 1
    fi
    
    log_success "Python version: $PYTHON_VERSION"
}

# Check and install Homebrew
check_brew() {
    log_info "Checking Homebrew..."
    
    if ! command -v brew &> /dev/null; then
        log_warning "Homebrew not found. Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Add Homebrew to PATH for this session
        if [[ "$SHELL" == *"zsh"* ]]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        elif [[ "$SHELL" == *"bash"* ]]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.profile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
    else
        log_success "Homebrew is installed"
    fi
    
    log_info "Evaluating Homebrew shellenv for PATH..."
    eval "$(/opt/homebrew/bin/brew shellenv)"
}

# Check and install FFmpeg
check_ffmpeg() {
    log_info "Checking FFmpeg..."
    
    if ! command -v ffmpeg &> /dev/null; then
        log_info "Installing FFmpeg via Homebrew..."
        brew install ffmpeg
    else
        FF_VERSION=$(ffmpeg -version 2>&1 | head -n1)
        log_success "FFmpeg is installed: $FF_VERSION"
    fi
}

# Create virtual environment
create_venv() {
    log_info "Creating virtual environment..."
    
    if [[ -d "$VENV_DIR" ]]; then
        log_warning "Virtual environment already exists. Removing..."
        rm -rf "$VENV_DIR"
    fi
    
    $PYTHON_CMD -m venv "$VENV_DIR"
    log_success "Virtual environment created at $VENV_DIR"
}

# Install Python dependencies
install_dependencies() {
    log_info "Installing Python dependencies..."
    
    if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
        log_error "requirements.txt not found in $SCRIPT_DIR"
        exit 1
    fi
    
    # Activate virtual environment and install
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip
    pip install -r "$REQUIREMENTS_FILE"
    
    deactivate
    log_success "Dependencies installed successfully"
}

# Create CLI wrapper script
create_cli_script() {
    log_info "Creating CLI wrapper script..."
    
    cat > "$CLI_SCRIPT" << 'EOF'
#!/bin/bash

# Descriptor CLI Wrapper
# This script activates the virtual environment and runs the main descriptor script

SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
MAIN_SCRIPT="$PROJECT_DIR/descriptor.py"

# Check if virtual environment exists
if [[ ! -d "$VENV_DIR" ]]; then
    echo "Error: Virtual environment not found. Please run install.sh first."
    exit 1
fi

# Check if main script exists
if [[ ! -f "$MAIN_SCRIPT" ]]; then
    echo "Error: Main descriptor script not found at $MAIN_SCRIPT"
    exit 1
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Run the main descriptor script with all arguments
python3 "$MAIN_SCRIPT" "$@"

# Exit with the same code as the descriptor script
exit $?
EOF

    chmod +x "$CLI_SCRIPT"
    log_success "CLI wrapper created at $CLI_SCRIPT"
}

# Install system-wide command
install_system_command() {
    log_info "Installing system-wide 'descriptor' command..."
    
    # Remove existing symlink or file
    sudo rm -f "$SYSTEM_BIN"
    
    # Create symlink to CLI script
    sudo ln -sf "$CLI_SCRIPT" "$SYSTEM_BIN"
    
    log_success "System command symlinked at $SYSTEM_BIN -> $CLI_SCRIPT"
}

# Test installation
test_installation() {
    log_info "Testing installation..."
    
    # Test that the command is available
    if ! command -v descriptor &> /dev/null; then
        log_error "Installation test failed: 'descriptor' command not found in PATH"
        exit 1
    fi
    
    # Test the CLI logic using local script (system symlink resolution may vary)
    if ! bash "$CLI_SCRIPT" --help &> /dev/null; then
        log_error "Installation test failed: CLI logic error"
        exit 1
    fi
    
    log_success "Installation test passed!"
}

# Display usage information
show_usage() {
    echo ""
    echo "========================================"
    echo "🎉 Descriptor Installation Complete!"
    echo "========================================"
    echo ""
    echo "Usage:"
    echo "  descriptor [directory] [options]"
    echo ""
    echo "Examples:"
    echo "  descriptor .                    # Process current directory"
    echo "  descriptor /path/to/videos      # Process specific directory"
    echo "  descriptor --help               # Show help"
    echo ""
    echo "The 'descriptor' command is now available system-wide!"
    echo "You can run it from any directory without activating the virtual environment."
    echo ""
    echo "To uninstall, run: ./uninstall.sh"
    echo "========================================"
}

# Main installation function
main() {
    echo "🚀 Starting Descriptor Installation"
    echo "=================================="
    
    check_root
    check_system
    check_brew
    check_python
    check_ffmpeg
    create_venv
    install_dependencies
    create_cli_script
    install_system_command
    test_installation
    show_usage
    
    log_success "Installation completed successfully!"
}

# Run main function
main "$@"