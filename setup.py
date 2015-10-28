from setuptools import setup, find_packages

tests_require = [
    'pytest >= 2.0',
    'pytest-cov',
    'pytest-remove-stale-bytecode',
    'webtest'
]


setup(
    name='graphql-wsgi',
    version='0.1.dev0',
    description="GraphQL server for Python WSGI",
    author="Martijn Faassen",
    author_email="faassen@startifact.com",
    license="BSD",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    exclude=['tests'],
    install_requires=[
        'setuptools',
        'graphql-core',
        'webob'
    ],
    tests_require=tests_require,
    extras_require=dict(
        test=tests_require,
    )
)
