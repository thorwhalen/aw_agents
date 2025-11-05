#!/usr/bin/env python
"""
Setup helper for aw-agents

This script helps you get started with aw-agents package.
"""

import subprocess
import sys
from pathlib import Path


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def check_dependencies():
    """Check if required dependencies are available."""
    print_section("Checking Dependencies")
    
    required = ['requests', 'beautifulsoup4', 'graze']
    optional_mcp = ['mcp']
    optional_api = ['fastapi', 'uvicorn', 'pydantic']
    
    missing = []
    
    print("Checking required dependencies...")
    for pkg in required:
        try:
            __import__(pkg.replace('-', '_'))
            print(f"  ✓ {pkg}")
        except ImportError:
            print(f"  ✗ {pkg} (missing)")
            missing.append(pkg)
    
    print("\nChecking optional dependencies (MCP for Claude)...")
    for pkg in optional_mcp:
        try:
            __import__(pkg)
            print(f"  ✓ {pkg}")
        except ImportError:
            print(f"  ✗ {pkg} (install with: pip install aw-agents[mcp])")
    
    print("\nChecking optional dependencies (API for ChatGPT)...")
    for pkg in optional_api:
        try:
            __import__(pkg)
            print(f"  ✓ {pkg}")
        except ImportError:
            print(f"  ✗ {pkg} (install with: pip install aw-agents[api])")
    
    if missing:
        print(f"\n⚠️  Missing required dependencies: {', '.join(missing)}")
        print("   Install with: pip install -e .")
        return False
    
    return True


def test_import():
    """Test that the package can be imported."""
    print_section("Testing Package Import")
    
    try:
        import aw_agents
        print(f"✓ Successfully imported aw_agents")
        print(f"  Version: {aw_agents.__version__}")
        
        from aw_agents.download import DownloadAgent
        print("✓ Successfully imported DownloadAgent")
        
        from aw_agents.adapters import MCPAdapter, OpenAPIAdapter
        print("✓ Successfully imported adapters")
        
        return True
    except ImportError as e:
        print(f"✗ Failed to import: {e}")
        print("\n  Make sure you've installed the package:")
        print("  pip install -e .")
        return False


def show_next_steps():
    """Show next steps for the user."""
    print_section("Next Steps")
    
    print("1. Try the examples:")
    print("   python examples.py")
    print()
    print("2. Test the download agent:")
    print("   python -c 'from aw_agents.download import DownloadAgent; print(DownloadAgent().get_tools())'")
    print()
    print("3. Deploy to Claude:")
    print("   python scripts/deploy_mcp.py DownloadAgent --output ~/mcp_download.py")
    print()
    print("4. Deploy to ChatGPT:")
    print("   python scripts/deploy_api.py DownloadAgent --output ~/api_download.py")
    print("   python ~/api_download.py")
    print()
    print("5. Create your own agent:")
    print("   See README.md for instructions")
    print()
    print("6. Initialize git repository:")
    print("   git init")
    print("   git add .")
    print("   git commit -m 'Initial commit'")
    print()


def main():
    """Main setup function."""
    print("\n╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "aw-agents Setup Helper" + " " * 21 + "║")
    print("╚" + "═" * 58 + "╝")
    
    # Check if we're in the right directory
    if not Path('pyproject.toml').exists():
        print("\n⚠️  Warning: pyproject.toml not found")
        print("   Make sure you're running this from the aw_agents_package directory")
        print()
    
    # Check dependencies
    deps_ok = check_dependencies()
    
    if not deps_ok:
        print("\n❌ Please install missing dependencies first:")
        print("   pip install -e .")
        return 1
    
    # Test import
    import_ok = test_import()
    
    if not import_ok:
        print("\n❌ Package import failed")
        return 1
    
    # Show next steps
    show_next_steps()
    
    print("=" * 60)
    print("✓ Setup check complete!")
    print("=" * 60)
    print()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
