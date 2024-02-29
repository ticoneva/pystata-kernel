from distutils.core import setup

with open('README.rst') as f:
    readme = f.read()

setup(
    name='pystata-kernel',
    version='0.3.2',
    packages=['pystata-kernel'],
    package_data={'pystata-kernel': ['logo-64x64.png']},
    description='A simple Jupyter kernel for Stata based on pystata',
    long_description=readme,
    author='Vinci Chow',
    author_email='ticoneva@gmail.com',
    url='https://github.com/ticoneva/pystata-kernel',
    install_requires=[
        'jupyter-client', 
        'ipython', 
        'ipykernel',
        'packaging', 
        'pandas', 
        'numpy',
        'beautifulsoup4'
    ],
    include_package_data=True,
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
    ],
)
