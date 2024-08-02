from setuptools import setup, find_packages

setup(
    name='bytesviewnotifiactionclient',
    version='1.0.1',
    packages=find_packages(),
    install_requires=[
        'firebase-admin','rq','redis',
    ],
    author='BytesView',
    author_email='contact@bytesview.com',
    description='A plugin for Notification',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/bytesview/bytesview-notifiaction-client',
    keywords=[
        'bytesview notification',
        'bytesview notification client',
        ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)

