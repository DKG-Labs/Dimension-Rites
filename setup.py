from setuptools import setup, find_packages

setup(
    name="dimensional_analysis",
    version="1.0.0",
    author="DKG Labs",
    author_email="ojas@dkgrouplabs.com",
    description="A rail inspection system for dimensional analysis and image comparison",
    long_description=open("README.md").read(),  # You can include a README for more detailed description
    long_description_content_type="text/markdown",
    url="https://github.com/ojasdkg/DARITES-Prod",  # Replace with your repository URL if available
    packages=find_packages(include=['dimensional_analysis']),
    install_requires=[
        "opencv-python",
        "mysql-connector-python",
        "numpy",
        "matplotlib",
        "pillow",
        "pixelmatch"
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    test_suite='tests',
    entry_points={
        "console_scripts": [
            "DARITES-dev=dimensional_analysis.main:main_job",  # Entry point for command line usage
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)