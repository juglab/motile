from setuptools import setup

setup(
        name='motile',
        version='0.1',
        description='Multi-Object Tracker using Integer Linear Equations',
        url='https://github.com/funkelab/motile',
        author='Jan Funke',
        author_email='funkej@janelia.hhmi.org',
        license='MIT',
        packages=[
            'motile',
            'motile.constraints',
            'motile.costs'
        ],
        install_requires=[
            'networkx',
            'pylp',
            'numpy'
        ]
)
