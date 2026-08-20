from setuptools import find_packages, setup

setup(
    name="ai-sathi-shared",
    version="2.0.0",
    description="Shared utilities for AI-SATHI project",
    author="Akash Kundu",
    author_email="akashkundu1152@gmail.com",
    license="AGPL-3.0",
    packages=find_packages(where="backend"),
    package_dir={"": "backend"},
    python_requires=">=3.11",
    install_requires=[
        "fastapi",
        "pydantic",
        "sqlalchemy",
        "uvicorn",
        "python-dotenv",
        "boto3",
    ],
    extras_require={"test": ["pytest", "pytest-cov", "pytest-asyncio"]},
    include_package_data=True,
    zip_safe=False,
)
