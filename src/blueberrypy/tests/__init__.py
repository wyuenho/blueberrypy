try:
    from psycopg2cffi import compat
except ImportError:
    pass
else:
    compat.register()
    del compat
