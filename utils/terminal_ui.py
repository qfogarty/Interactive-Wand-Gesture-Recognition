"""
Terminal UI utilities for console output formatting.

Provides color codes and formatted output functions for consistent
command-line interface across all scripts.
"""


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color


def print_header(text: str) -> None:
    """Print formatted section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.NC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.NC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.NC}\n")


def print_banner() -> None:
    """Display welcome banner"""
    print(f"{Colors.BLUE}TPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPW{Colors.NC}")
    print(f"{Colors.BLUE}Q   Interactive Wand Setup                     Q{Colors.NC}")
    print(f"{Colors.BLUE}ZPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP]{Colors.NC}")
    print()
