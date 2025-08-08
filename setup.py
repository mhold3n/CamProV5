from setuptools import setup, find_packages

setup(
    name="campro",
    version="5.0.0",
    description="CamProV5 - Advanced CAM software with in-the-loop testing capabilities",
    author="CamPro Development Team",
    author_email="dev@campro.example.com",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.20.0",
        "matplotlib>=3.4.0",
        "scipy>=1.6.0",
        "pandas>=1.2.0",
        "PyQt5>=5.15.0",
        "PyQtChart>=5.15.0",
        "tqdm>=4.60.0",
        "colorama>=0.4.4",
    ],
    extras_require={
        "dev": [
            "pytest>=6.2.0",
            "pytest-qt>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "campro=campro.main:main",
            "campro-test-setup=campro.testing.setup_agent:main",
            "campro-test-scenarios=campro.testing.create_scenarios:main",
            "campro-test-session=campro.testing.start_agent_session:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Manufacturing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)