from distutils.core import setup

# from pipenv.project import Project
# from pipenv.utils import convert_deps_to_pip
#
# pfile = Project(chdir=False).parsed_pipfile
# requirements = convert_deps_to_pip(pfile['packages'], r=False)
# dev_requirements = convert_deps_to_pip(pfile['dev-packages'], r=False)

setup(
    name='ron',
    version='0.1',
    packages=['ron', 'ron.web', 'ron.base', 'ron.gluon', 'ron.config',
              'ron.helpers', 'ron.widgets', 'ron.exceptions'],
    url='ron.daxslab.com',
    license='MIT',
    author='Daxslab',
    author_email='info@daxslab.com',
    description='Uncomplicated Python web framework',
    install_requires=[
        'bottle',
        'inflection'
    ]
)
