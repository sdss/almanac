


def get_sqlite_database_and_schema(path=":memory:"):
    """
    Return a database and schema for all base models.

    Currently this only returns a SQLite in-memory database for testing purposes.
    """
    from playhouse.sqlite_ext import SqliteExtDatabase

    sqlite_kwargs = dict(
        thread_safe=True,
        pragmas={
            'journal_mode': 'wal',
            'cache_size': -1 * 64000,  # 64MB
            'foreign_keys': 1,
            'ignore_check_constraints': 0,
            'synchronous': 0
        }
    )

    database = SqliteExtDatabase(path, **sqlite_kwargs)
    schema = None
    return (database, schema)



def get_postgresql_database_and_schema(**kwargs):
    from peewee import PostgresqlDatabase

    database = PostgresqlDatabase(
        "sdss5db",
        user="u6020307",
        host="pipelines.sdss.org",
    )
    return (database, "almanac")


get_database_and_schema = get_postgresql_database_and_schema