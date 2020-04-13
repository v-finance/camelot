from invoke import task

@task()
def test(ctx):
    """
    Run unittests
    """
