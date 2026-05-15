from setuptools import find_packages, setup

setup(
    name="sic_applications",
    version="2.0.0",
    packages=find_packages(),
    install_requires=[
        "social-interaction-cloud>=2.0.13",
    ],
    extras_require={
        "dev": [
            "pre-commit==4.0.1",
            "isort==5.13.2",
            "black==24.10.0",
            "yamllint==1.35.1",
        ],
        "mcp": [
            "langchain-mcp-adapters>=0.1.0",
            "langchain>=0.3",
            "langchain-openai>=0.2",
            "langgraph>=1.0",
            "mcp>=1.0",
            "python-dotenv>=1.0.0",
        ],
    },
)
