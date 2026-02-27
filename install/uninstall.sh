#!/bin/bash

# Descriptor Uninstallation Script
# Removes the descriptor video processing pipeline installation
# Usage: ./uninstall.sh

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
CLI_SCRIPT="$SCRIPT_DIR/descriptor-cli"
SYSTEM_BIN="/usr/local/bin/descriptor"

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

# Confirm uninstallation
confirm_uninstall() {
    echo "⚠️  This will remove the descriptor installation from your system."
    echo ""
    echo "The following will be removed:"
    echo "  - System-wide 'descriptor' command"
    echo "  - Virtual environment ($VENV_DIR)"
    echo "  - CLI wrapper script ($CLI_SCRIPT)"
    echo ""
    echo "The main project files will remain intact."
    echo ""
    
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Uninstallation cancelled."
        exit 0
    fi
}

# Remove system-wide command
remove_system_command() {
    log_info "Removing system-wide 'descriptor' command..."
    
    if [[ -f "$SYSTEM_BIN" ]]; then
        sudo rm -f "$SYSTEM_BIN"
        log_success "Removed system command: $SYSTEM_BIN"
    else
        log_warning "System command not found at $SYSTEM_BIN"
    fi
}

# Remove CLI wrapper script
remove_cli_script() {
    log_info "Removing CLI wrapper script..."
    
    if [[ -f "$CLI_SCRIPT" ]]; then
        rm -f "$CLI_SCRIPT"
        log_success "Removed CLI wrapper: $CLI_SCRIPT"
    else
        log_warning "CLI wrapper not found at $CLI_SCRIPT"
    fi
}

# Remove virtual environment
remove_venv() {
    log_info "Removing virtual environment..."
    
    if [[ -d "$VENV_DIR" ]]; then
        rm -rf "$VENV_DIR"
        log_success "Removed virtual environment: $VENV_DIR"
    else
        log_warning "Virtual environment not found at $VENV_DIR"
    fi
}

# Test removal
test_removal() {
    log_info "Testing removal..."
    
    # Test that the command is no longer available
    if command -v descriptor &> /dev/null; then
        log_warning "'descriptor' command is still available in PATH"
        log_warning "You may need to restart your terminal or shell session"
    else
        log_success "Command successfully removed from PATH"
    fi
}

# Display completion message
show_completion() {
    echo ""
    echo "========================================"
    echo "🧹 Descriptor Uninstallation Complete!"
    echo "========================================"
    echo ""
    echo "The following has been removed:"
    echo "  ✓ System-wide 'descriptor' command"
    echo "  ✓ Virtual environment"
    echo "  ✓ CLI wrapper script"
    echo ""
    echo "The main project files remain in:"
    echo "  $SCRIPT_DIR"
    echo ""
    echo "If you wish to completely remove the project, delete the entire directory:"
    echo "  rm -rf $SCRIPT_DIR"
    echo ""
    echo "To reinstall, you can:"
echo "  1. Run: ./install/install.sh"
echo "  2. Clone the repository again: git clone [repository-url]"
echo "  3. Download from GitHub: curl -sSL https://raw.githubusercontent.com/yourusername/descriptor/main/install/curl-install.sh | bash"
    echo "========================================"
}

# Main uninstallation function
main() {
    echo "🧹 Starting Descriptor Uninstallation"
    echo "===================================="
    
    confirm_uninstall
    remove_system_command
    remove_cli_script
    remove_venv
    test_removal
    show_completion
    
    log_success "Uninstallation completed successfully!"
}

# Run main function
main "$@"