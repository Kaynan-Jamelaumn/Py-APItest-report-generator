from setuptools import setup, find_packages

setup(
    name="PyTestDocx",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "certifi==2025.1.31",
        "charset-normalizer==3.4.1",
        "contourpy==1.3.2",
        "cycler==0.12.1",
        "dotenv==0.9.9",
        "fonttools==4.57.0",
        "idna==3.10",
        "kiwisolver==1.4.8",
        "lxml==5.3.2",
        "matplotlib==3.10.1",
        "numpy==2.2.5",
        "packaging==25.0",
        "pillow==11.2.1",
        "pyparsing==3.2.3",
        "python-dateutil==2.9.0.post0",
        "python-docx==1.1.2",
        "python-dotenv==1.0.1",
        "requests==2.32.3",
        "requests-toolbelt==1.0.0",
        "six==1.17.0",
        "typing_extensions==4.13.1",
        "urllib3==2.3.0",
    ],
    entry_points={
        'console_scripts': [
            'pytx=PyTestDocx.main:main',
        ],
    },
)
