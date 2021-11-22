from setuptools import setup

from tiny_listener import __version__


setup(
    name="tiny-listener",
    version=__version__,
    description="lightning-fast, high-performance event handle framework",
    long_description=open("README.md", "r", encoding="utf8").read(),
    long_description_content_type="text/markdown",
    author="molto",
    author_email="wy6269@gmail.com",
    packages=[
        'tiny_listener',
    ],
    zip_safe=False,
    install_requires=[
        "click>=8.0.1",
        "typing-extensions>=3.7.4",
    ],
    license="MIT",
    entry_points={
        "console_scripts": ["tiny-listener=tiny_listener.__main__:main"],
    },
    project_urls={
        'Source': 'https://github.com/molto0504/tiny-listener',
    }
)
