import os

from invoke import task

build_dir = 'build'
default_test_env = os.path.join(build_dir, 'env')
default_python_dir = os.path.join('/', 'usr', 'share', 'conda', 'miniconda3', 'envs', 'py34')

@task()
def test(ctx):
    """
    Run unittests
    """
    env_dir = default_test_env
    ctx.run('{}/bin/python -m nose.core -v -s test'.format(env_dir))

@task()
def create_test_environment(ctx):
    """
    Create a virtual environment to  run tests
    """
    env_dir = default_test_env
    if not os.path.exists(env_dir):
        ctx.run('{}/bin/pyvenv {} --system-site-packages'.format(default_python_dir, env_dir))
    ctx.run('{}/bin/python -m pip install -r requirements.txt'.format(env_dir))