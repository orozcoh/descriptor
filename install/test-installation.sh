#!/bin/bash

# Descriptor Installation Test Script
# Tests the installation process and validates functionality
# Usage: ./test-installation.sh

set -e

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Test virtual environment
test_venv() {
    log_info "Testing virtual environment..."
    
    if [[ ! -d "venv" ]]; then
        log_error "Virtual environment not found"
        return 1
    fi
    
    if [[ ! -f "venv/bin/activate" ]]; then
        log_error "Virtual environment activation script not found"
        return 1
    fi
    
    log_success "Virtual environment exists and is properly configured"
}

# Test Python dependencies
test_dependencies() {
    log_info "Testing Python dependencies..."
    
    # Activate virtual environment and test imports
    source venv/bin/activate
    
    # Test MLX dependencies
    python3 -c "import mlx_lm; print('mlx-lm: OK')" || { log_error "mlx-lm import failed"; deactivate; return 1; }
    python3 -c "import mlx_vlm; print('mlx-vlm: OK')" || { log_error "mlx-vlm import failed"; deactivate; return 1; }
    python3 -c "import timm; print('timm: OK')" || { log_error "timm import failed"; deactivate; return 1; }
    
    deactivate
    log_success "All Python dependencies are working correctly"
}

# Test CLI wrapper
test_cli_wrapper() {
    log_info "Testing CLI wrapper..."
    
    if [[ ! -f "descriptor-cli" ]]; then
        log_error "CLI wrapper script not found"
        return 1
    fi
    
    if [[ ! -x "descriptor-cli" ]]; then
        log_error "CLI wrapper script is not executable"
        return 1
    fi
    
    log_success "CLI wrapper exists and is executable"
}

# Test system command
test_system_command() {
    log_info "Testing system-wide command..."
    
    if ! command -v descriptor &> /dev/null; then
        log_error "'descriptor' command not found in PATH"
        return 1
    fi
    
    # Test that it can show help without errors
    if ! descriptor --help &> /dev/null; then
        log_error "'descriptor --help' returned an error"
        return 1
    fi
    
    log_success "System command is working correctly"
}

# Test main script
test_main_script() {
    log_info "Testing main descriptor script..."
    
    if [[ ! -f "descriptor.py" ]]; then
        log_error "Main descriptor script not found"
        return 1
    fi
    
    # Test that the script can be executed
    if ! python3 descriptor.py --help &> /dev/null; then
        log_error "Main script execution failed"
        return 1
    fi
    
    log_success "Main script is working correctly"
}

# Test individual scripts
test_individual_scripts() {
    log_info "Testing individual scripts..."
    
    scripts=("scripts/frame-extractor.py" "scripts/scene-extractor.py" "scripts/describeAI.py" "scripts/des-group.py" "scripts/clear-files.py")
    
    for script in "${scripts[@]}"; do
        if [[ ! -f "$script" ]]; then
            log_error "Script $script not found"
            return 1
        fi
        
        # Test that each script can show help
        if ! python3 "$script" --help &> /dev/null; then
            log_warning "Script $script help command failed (may not have --help option)"
        fi
    done
    
    log_success "All individual scripts are present"
}

# Test FFmpeg
test_ffmpeg() {
    log_info "Testing FFmpeg..."
    
    if ! command -v ffmpeg &> /dev/null; then
        log_error "FFmpeg not found"
        return 1
    fi
    
    # Test FFmpeg functionality
    if ! ffmpeg -version &> /dev/null; then
        log_error "FFmpeg version check failed"
        return 1
    fi
    
    log_success "FFmpeg is installed and working"
}

# Test Python version
test_python_version() {
    log_info "Testing Python version..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 not found"
        return 1
    fi
    
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [[ $PYTHON_MAJOR -lt 3 ]] || [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -lt 10 ]]; then
        log_error "Python 3.10 or later is required. Found: $PYTHON_VERSION"
        return 1
    fi
    
    log_success "Python version is compatible: $PYTHON_VERSION"
}

# Display test results summary
show_test_summary() {
    echo ""
    echo "========================================"
    echo "🧪 Installation Test Summary"
    echo "========================================"
    echo ""
    echo "All tests completed successfully!"
    echo ""
    echo "✅ Virtual environment: Working"
    echo "✅ Python dependencies: Working"
    echo "✅ CLI wrapper: Working"
    echo "✅ System command: Working"
    echo "✅ Main script: Working"
    echo "✅ Individual scripts: Working"
    echo "✅ FFmpeg: Working"
    echo "✅ Python version: Compatible"
    echo ""
    echo "🎉 Descriptor is ready to use!"
    echo ""
    echo "Usage:"
    echo "  descriptor [directory] [options]"
    echo ""
    echo "Examples:"
    echo "  descriptor .                    # Process current directory"
    echo "  descriptor /path/to/videos      # Process specific directory"
    echo "========================================"
}

# Main test function
main() {
    echo "🧪 Starting Descriptor Installation Tests"
    echo "========================================"
    
    test_python_version
    test_ffmpeg
    test_venv
    test_dependencies
    test_cli_wrapper
    test_main_script
    test_individual_scripts
    test_system_command
    show_test_summary
    
    log_success "All tests passed! Installation is working correctly."
}

# Run main function
main "$@"