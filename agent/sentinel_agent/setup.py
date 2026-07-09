# agent/setup.py
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="sentinelops-agent",
    version="1.0.0",
    author="SentinelOps",
    description="SentinelOps Monitoring Agent",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
        "urllib3>=1.26.0",
    ],
    entry_points={
        'console_scripts': [
            'sentinel-agent=sentinel_agent.run:main',
        ],
    },
    python_requires='>=3.8',
)