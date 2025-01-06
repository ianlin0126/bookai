from setuptools import setup, find_packages

setup(
    name="bookai",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "fastapi==0.104.1",
        "uvicorn==0.24.0",
        "sqlalchemy==1.4.50",
        "python-dotenv==1.0.0",
        "google-generativeai==0.3.1",
        "openai==1.3.5",
        "requests==2.31.0",
        "python-multipart==0.0.6",
        "alembic==1.8.1",
        "redis==5.0.1",
        "beautifulsoup4==4.12.2",
        "pydantic-settings==2.1.0",
        "jinja2==3.1.2",
        "httpx==0.25.2"
    ],
    python_requires=">=3.8",
)
