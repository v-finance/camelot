"""
Custom Sqlalchemy expressions to have code portable between postgres and
sqlite

TODO: move this (back) to vfinance/sql/__init__py eventually.
"""
from sqlalchemy.dialects import postgresql, sqlite

def is_sqlite(compiler):
    """
    Function that returns whether the given compiler is of dialect SQLite.
    Can be used as the _create_rule argument of schema constructs to only create them on an SQLite backend.
    """
    return compiler.dialect.name == sqlite.dialect().name

def is_postgres(compiler):
    """
    Function that returns whether the given compiler is of dialect PostgreSQL.
    Can be used as the _create_rule argument of schema constructs to only create them on an Postgres backend.
    """
    return compiler.dialect.name == postgresql.dialect().name
