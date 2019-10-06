import setuptools
import re

with open("README.md", "r") as fh:
    long_description = fh.read()

version = re.search(
    r"""__version__\s*=\s*[\'"]([^\'"]*)[\'"]""",
    open("msteams/__init__.py", "r").read(),
).group(1)

setuptools.setup(
    name="msteams",
    version=version,
    author="Johan Jeppsson",
    author_email="johjep@gmail.com",
    description="A builder/formatter for MS Teams cards",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/johanjeppsson/msteams",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=2.7",
)
