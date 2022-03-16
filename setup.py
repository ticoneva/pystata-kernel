from distutils.core import setup

with open('README.md') as f:
    readme = f.read()

setup(
    name='pystata-kernel',
    version='0.1.5',
    packages=['pystata-kernel'],
    description='A simple Jupyter kernel for Stata based on pystata',
    long_description=readme,
    author='Vinci Chow',
    author_email='ticoneva@gmail.com',
    url='https://github.com/ticoneva/pystata-kernel',
    install_requires=[
        'jupyter-client', 'ipython', 'ipykernel','stata-setup'
    ],
    include_package_data=True,
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
    ],
)
