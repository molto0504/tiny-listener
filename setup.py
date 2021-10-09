import re
import os
from setuptools import setup


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    path = os.path.join(package, "__init__.py")
    init_py = open(path, "r", encoding="utf8").read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


setup(
    name="tiny-listener",
    version=get_version("tiny_listener"),
    description="lightning-fast, high-performance event handle framework",
    author="molto",
    author_email="wy6269@gmail.com",
    packages=[
        'tiny_listener',
    ],
    zip_safe=False,
    install_requires=[
        "click>=8.0.1",
    ],
    license="MIT",
    entry_points={
        "console_scripts": ["tiny-listener=tiny_listener.__main__:main"],
    }
)
