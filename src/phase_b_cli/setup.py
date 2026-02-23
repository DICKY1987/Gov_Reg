"""Setup script for Phase B CLI"""

from setuptools import setup, find_packages

setup(
    name="phase-b-cli",
    version="1.0.0",
    description="Phase B: Execution Compilation CLI",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        # No external dependencies for v1.0
    ],
    entry_points={
        "console_scripts": [
            "plan-refine-b=phase_b_cli.cli:main",
        ],
    },
)
