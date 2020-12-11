from setuptools import setup

setup(
   name='ml-fingerprint',
   version='0',
   description='Add an integrity and authenticity verification layer for all scikit-learn models.',
   author='Jaime Solsona',
   author_email='j.solsonaa@alumnos.urjc.es',
   packages=['ml_fingerprint'],
   install_requires=['scikit-learn', 'orjson', 'pycryptodome', 'pandas'],
)