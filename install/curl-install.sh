#!/bin/bash

# GitHub-hosted Descriptor Installation Script
# This script can be run directly from GitHub with curl
# Usage: curl -sSL https://raw.githubusercontent.com/yourusername/descriptor/main/curl-install.sh | bash

set -e

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
GITHUB_REPO="orozcoh/descriptor"
INSTALL_DIR="$HOME/descriptor"
INSTALL_SCRIPT_URL="https://raw.githubusercontent.com/$GITHUB_REPO/main/install/install.sh"

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

# Check if already installed
check_existing_installation() {
    if command -v descriptor &> /dev/null; then
        log_warning "Descriptor is already installed."
        log_warning "Location: $(which descriptor)"
        read -p "Do you want to reinstall? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Installation cancelled."
            exit 0
        fi
    fi
}

# Clone or update repository
setup_repository() {
    log_info "Setting up descriptor repository..."
    
    if [[ -d "$INSTALL_DIR" ]]; then
        log_info "Repository already exists. Updating..."
        cd "$INSTALL_DIR"
        git pull
    else
        log_info "Cloning descriptor repository..."
        git clone "https://github.com/$GITHUB_REPO.git" "$INSTALL_DIR"
        cd "$INSTALL_DIR"
    fi
    
    log_success "Repository setup complete"
}

# Download and run installation script
run_installation() {
    log_info "Downloading installation script..."
    
    # Download the main install script
    curl -sSL "$INSTALL_SCRIPT_URL" -o "$INSTALL_DIR/install.sh"
    chmod +x "$INSTALL_DIR/install.sh"
    
    log_info "Running installation..."
    cd "$INSTALL_DIR"
    ./install/install.sh
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
    echo "Project location: $INSTALL_DIR"
    echo "To uninstall, run: $INSTALL_DIR/uninstall.sh"
    echo "========================================"
}

# Main installation function
main() {
    echo "🚀 Starting Descriptor One-Command Installation"
    echo "=============================================="
    
    check_root
    check_existing_installation
    setup_repository
    run_installation
    show_usage
    
    log_success "One-command installation completed successfully!"
}

# Run main function
main "$@"