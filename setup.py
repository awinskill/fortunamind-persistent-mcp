#!/usr/bin/env python3
"""
Setup script for FortunaMind Persistent MCP Server

This provides proper package structure and resolves the import issues
identified in the extensibility review.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="fortunamind-persistent-mcp",
    version="1.0.0",
    author="FortunaMind Team",
    author_email="dev@fortunamind.com",
    description="Persistent MCP server with advanced technical analysis and trading journal",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/awinskill/fortunamind-persistent-mcp",
    
    # Package structure
    packages=find_packages("src"),
    package_dir={"": "src"},
    
    # Entry points for command line scripts
    entry_points={
        "console_scripts": [
            "fortunamind-persistent-mcp=fortunamind_persistent_mcp.main:main",
            "fmcp-server=fortunamind_persistent_mcp.main:main",
        ],
    },
    
    # Python version requirement
    python_requires=">=3.11",
    
    # Dependencies
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "sqlalchemy>=2.0.23",
        "alembic>=1.13.0",
        "asyncpg>=0.29.0",
        "supabase>=2.0.0",
        "mcp>=0.4.0",
        "cryptography>=41.0.0",
        "httpx>=0.25.0",
        "pandas>=2.1.0",
        "numpy>=1.24.0",
        "python-dotenv>=1.0.0",
        "structlog>=23.2.0"
    ],
    
    # Development dependencies
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0", 
            "pytest-cov>=4.1.0",
            "black>=23.11.0",
            "isort>=5.12.0",
            "flake8>=6.1.0",
            "mypy>=1.7.0",
            "bandit>=1.7.5",
            "pre-commit>=3.6.0"
        ]
    },
    
    # Package data
    include_package_data=True,
    package_data={
        "fortunamind_persistent_mcp": [
            "py.typed",
        ],
    },
    
    # Classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry", 
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    
    # Keywords
    keywords=[
        "mcp", "trading", "technical-analysis", "journal", 
        "crypto", "portfolio", "persistence", "ai"
    ],
    
    # Project URLs
    project_urls={
        "Bug Reports": "https://github.com/awinskill/fortunamind-persistent-mcp/issues",
        "Source": "https://github.com/awinskill/fortunamind-persistent-mcp",
        "Documentation": "https://github.com/awinskill/fortunamind-persistent-mcp#readme",
    },
)