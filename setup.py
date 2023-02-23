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
        "click>=8.1.3",
    ],
    license="MIT",
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Topic :: Internet",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "License :: OSI Approved :: MIT License",
        "Typing :: Typed",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    entry_points={
        "console_scripts": ["tiny-listener=tiny_listener.__main__:main"],
    },
    project_urls={
        'Source': 'https://github.com/molto0504/tiny-listener',
    }
)
