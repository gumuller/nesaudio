from setuptools import setup, find_packages

setup(
    name="nesaudio",
    version="1.0.0",
    description="NES-style terminal audio application with live sound generation and music playback",
    author="NESAudio Team",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.24.0",
        "sounddevice>=0.4.6",
        "textual>=0.82.0",
        "rich>=13.0.0",
        "pyyaml>=6.0",
        "scipy>=1.10.0",
    ],
    entry_points={
        "console_scripts": [
            "nesaudio=nesaudio.__main__:main",
        ],
    },
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Sound/Audio :: Sound Synthesis",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
