import json
import os
import re

from invoke import task

python_interpreter = '/vortex/x86_64-redhat-linux/default/bin/python3'
build_dir = 'build'
default_test_env = os.path.join(build_dir, 'env')

JIRA_project_keys = ['VFIN', 'POLAPP', 'WP']
JIRA_ticket_nr_regex = '('+ '|'.join(JIRA_project_keys) +')-[1-9][0-9]*'

@task()
def test(ctx, tests="test"):
    """
    Run unittests
    """
    env_dir = default_test_env
    ctx.run(
        '{}/bin/python -m nose.core -v -s {}'.format(env_dir, tests),
        env = {'QT_QPA_PLATFORM': 'offscreen',
               # Set the XDB base directory to the current working directory to prevent
               # profile registry intermingling between multiple jobs or test runs.
               'XDG_CONFIG_HOME': os.getcwd()}
    )

@task()
def create_test_environment(ctx):
    """
    Create a virtual environment to  run tests
    """
    env_dir = default_test_env
    if not os.path.exists(env_dir):
        ctx.run('{} -m venv {} --symlinks'.format(python_interpreter, env_dir))
    ctx.run('{}/bin/pip3 install --upgrade pip'.format(env_dir))
    ctx.run('{}/bin/pip3 install nose'.format(env_dir))
    ctx.run('{}/bin/pip3 install pyflakes'.format(env_dir))
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

@task()
def source_check(ctx):
    """
    check the source code for unused imports and unused variables
    """
    ctx.run('{}/bin/python -m pyflakes camelot camelot_example test'.format(default_test_env))
    ctx.run('echo Done')

@task(positional=['ticket_nr', 'msg'], optional=['paths'])
def commit(ctx, ticket_nr, msg, paths=None):
    if not re.match(JIRA_ticket_nr_regex, ticket_nr):
        print('ERROR: the given JIRA ticket number is not valid. It should be in the form of VFIN-xxxx.')
    else:
        message = '{} #comment {}'.format(ticket_nr, msg)
        if paths is None:
            ctx.run('git commit -am "{}"'.format(message))
        else:
            ctx.run('git commit -m "{}" {}'.format(message, ' '.join(paths.split(','))))
