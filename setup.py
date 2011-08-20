from distutils.core import setup

# also update in urlnorm.py
version = '0.1'

setup(name='host_pool',
        version=version,
        long_description=open("./README.md", "r").read(),
        description="A generic pool to track a set of remote hosts with the ability to mark hosts down on failures",
        py_modules=['host_pool'],
        license='MIT License',
        author='Jehiah Czebotar',
        author_email='jehiah@gmail.com',
        url='http://github.com/jehiah/host_pool',
        download_url="http://github.com/downloads/jehiah/host_pool/host_pool-%s.tar.gz" % version,
        )
