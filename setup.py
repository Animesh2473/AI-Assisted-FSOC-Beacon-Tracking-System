from setuptools import setup, find_packages

setup(
    name="fsoc_tracker",
    version="1.0.0",
    description="AI-assisted virtual camera tracking system for FSOC coarse alignment (SIH PS4)",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "numpy>=1.23",
        "opencv-python>=4.7",
        "matplotlib>=3.6",
        "pyyaml>=6.0",
    ],
    python_requires=">=3.8",
)
