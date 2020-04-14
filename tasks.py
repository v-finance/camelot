import os

from invoke import task

build_dir = 'build'
default_test_env = os.path.join(build_dir, 'env')

@task()
def test(ctx):
    """
    Run unittests
    """
    env_dir = default_test_env
    ctx.run(
        '{}/bin/python -m nose.core -v -s test'.format(env_dir),
        env = {'QT_QPA_PLATFORM': 'offscreen'}
    )

@task()
def create_test_environment(ctx):
    """
    Create a virtual environment to  run tests
    """
    env_dir = default_test_env
    if not os.path.exists(env_dir):
        ctx.run('pyvenv-3 {} --symlinks'.format(env_dir))
    ctx.run('{}/bin/pip3 install --upgrade pip'.format(env_dir))
    ctx.run('{}/bin/pip3 install nose'.format(env_dir))
    ctx.run('{}/bin/pip3 install -r requirements.txt'.format(env_dir))