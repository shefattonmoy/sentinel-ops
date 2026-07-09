
from setuptools import setup, find_packages

setup(
    name="sentinelops-agent",
    version="1.0.0",
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