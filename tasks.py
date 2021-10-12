import os
import json

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

def extract_fontawesome_metadata(original_json, output_json):
    """
    Create a json file containing a directionary mapping font awesome names to
    unicode values.

    This json file is needed by the FontIcon class to translate icon names to
    their corresponding unicode code. The original json metadata is large (~3MB)
    and contains much information we don't need. Therefore, a simplified json
    file is created here.

    :param original_json: The icons.json file from the font awesome release
    :param output_json: The json file to generate.
    """
    # open original metadata file
    with open(original_json) as f:
        data = json.load(f)

    # create dict mapping icon name to unicode
    # key = icon name (e.g. 'backspace')
    # value = icon unicode as hexadecimal string (e.g. 'f55a')
    name_to_unicode = {}
    for name in data:
        name_to_unicode[name] = data[name]['unicode']

    # write dict to new json file
    with open(output_json, 'w') as f:
        json.dump(name_to_unicode, f)

@task()
def fontawesome_update(ctx):
    """
    Update font awesome and it's associated metadata

    The metadata is needed to translate icon names to unicode values.

    - Download font awesome release
    - Updates the font file
    - Extract metadata required by FontIcon class
    """
    version = '5.14.0'
    url = 'https://use.fontawesome.com/releases/v{}/fontawesome-free-{}-web.zip'.format(version, version)
    # download font awesome
    if os.path.exists('tmp'):
        ctx.run('rm -r tmp')
    os.mkdir('tmp')
    ctx.run('wget {} -O tmp/fontawesome.zip'.format(url))
    # unzip the file
    ctx.run('cd tmp && unzip -q fontawesome.zip')
    # Copy font file
    ctx.run('cp tmp/fontawesome-free-{}-web/webfonts/fa-solid-900.ttf camelot/art/awesome/fa-solid-900.ttf'.format(version))
    # Update name_to_code.json
    extract_fontawesome_metadata('tmp/fontawesome-free-{}-web/metadata/icons.json'.format(version), 'camelot/art/awesome/name_to_code.json')
    # Cleanup
    ctx.run('rm -r tmp')
