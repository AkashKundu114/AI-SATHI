from setuptools import setup ,find_packages 

setup (
name ="ai-sathi-shared",
version ="0.1.0",
description ="Shared utilities for AI‑SATHI project",
long_description =open ("README.md","r",encoding ="utf-8").read (),
long_description_content_type ="text/markdown",
author ="Akash Kundu",
author_email ="akashkundu1152@gmail.com",
url ="https://github.com/AkashKundu114/AI-SATHI",
license ="MIT",
packages =find_packages (where ="backend"),
package_dir ={"":"backend"},
python_requires =">=3.8",
install_requires =[
"sqlalchemy",
"pydantic",
"fastapi",
"uvicorn",
"python-dotenv",
],
classifiers =[
"Programming Language :: Python :: 3",
"License :: OSI Approved :: MIT License",
"Operating System :: OS Independent",
],
)
