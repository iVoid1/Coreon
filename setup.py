from setuptools import setup, find_packages

setup(
    name="coreon-ai",
    version="0.2.0",
    packages=find_packages(where="backend"),
    package_dir={"": "backend"},
    install_requires=[
        "ollama",
        "faiss-cpu", 
        "numpy",
        "rich"
    ],
    python_requires=">=3.8",
)