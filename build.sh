#!/bin/bash
# BenchLM Build Script for Linux/macOS

set -e  # Exit on error

echo "=========================================="
echo "BenchLM Build Script"
echo "=========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${PROJECT_ROOT}/build"
DIST_DIR="${PROJECT_ROOT}/dist"

# Parse arguments
BUILD_TARGET="all"
CLEAN=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --target)
            BUILD_TARGET="$2"
            shift 2
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            echo "Usage: ./build.sh [options]"
            echo "Options:"
            echo "  --target TARGET    Build target: all, linux, macos, windows, android, ios, web"
            echo "  --clean            Clean build directory before building"
            echo "  --verbose          Verbose output"
            echo "  --help             Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    log_info "Checking dependencies..."

    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi

    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    log_info "Python version: $PYTHON_VERSION"

    # Check uv or pip
    if command -v uv &> /dev/null; then
        PACKAGE_MANAGER="uv"
        log_info "Using uv for package management"
    elif command -v pip3 &> /dev/null; then
        PACKAGE_MANAGER="pip"
        log_info "Using pip for package management"
    else
        log_error "Neither uv nor pip found"
        exit 1
    fi

    # Check flet
    if ! python3 -c "import flet" &> /dev/null; then
        log_warn "Flet not installed, will install via $PACKAGE_MANAGER"
    fi
}

install_dependencies() {
    log_info "Installing dependencies..."

    if [ "$PACKAGE_MANAGER" = "uv" ]; then
        uv sync --all-extras
    else
        pip3 install -e ".[all]"
    fi

    log_info "Dependencies installed"
}

clean_build() {
    if [ "$CLEAN" = true ]; then
        log_info "Cleaning build directories..."
        rm -rf "$BUILD_DIR"
        rm -rf "$DIST_DIR"
        log_info "Clean complete"
    fi
}

build_flet() {
    local target=$1
    log_info "Building for $target..."

    cd "$PROJECT_ROOT"

    case $target in
        linux)
            flet build linux --verbose
            ;;
        macos)
            flet build macos --verbose
            ;;
        windows)
            flet build windows --verbose
            ;;
        android)
            flet build android --verbose
            ;;
        ios)
            flet build ios --verbose
            ;;
        web)
            flet build web --verbose
            ;;
        *)
            log_error "Unknown target: $target"
            return 1
            ;;
    esac

    log_info "Build for $target complete"
}

main() {
    echo "Starting BenchLM build..."
    echo "Target: $BUILD_TARGET"
    echo "Project root: $PROJECT_ROOT"

    check_dependencies
    clean_build
    install_dependencies

    case $BUILD_TARGET in
        all)
            # Build for current platform
            case "$(uname -s)" in
                Linux)
                    build_flet linux
                    ;;
                Darwin)
                    build_flet macos
                    ;;
                CYGWIN*|MINGW*|MSYS*)
                    build_flet windows
                    ;;
                *)
                    log_error "Unknown OS: $(uname -s)"
                    exit 1
                    ;;
            esac
            ;;
        linux|macos|windows|android|ios|web)
            build_flet "$BUILD_TARGET"
            ;;
        *)
            log_error "Invalid target: $BUILD_TARGET"
            exit 1
            ;;
    esac

    log_info "Build completed successfully!"
    echo "Output: $DIST_DIR"
}

main "$@"