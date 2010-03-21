import sqlalchemy.sql.operators

def like_op(column, string):
    return sqlalchemy.sql.operators.like_op(column, '%%%s%%'%string)
