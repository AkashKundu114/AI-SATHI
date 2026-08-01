from setuptools import setup, find_packages

setup(
    name="ai-sathi-shared",
    version="0.1.1",
    description="Shared utilities for AI‑SATHI project",
    author="Akash Kundu",
    author_email="akash@example.com",
    license="MIT",
    packages=find_packages(where="backend"),
    package_dir={"": "backend"},
    python_requires=">=3.8",
    install_requires=[
        "fastapi",
        "pydantic",
        "sqlalchemy",
        "uvicorn",
        "python-dotenv",
        "boto3",
    ],
    extras_require={
        "test": ["pytest", "pytest-cov", "pytest-asyncio"]
    },
    include_package_data=True,
    zip_safe=False,
)
