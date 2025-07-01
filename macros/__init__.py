import datetime

from sqlglot import exp
from sqlmesh import macro


@macro()
def my_current_time(evaluator):
    # Return the current time as a SQL string literal
    return exp.Literal.string(datetime.datetime.now())
