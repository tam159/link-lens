"""Idempotent bulk insert: COPY into a staging table, then insert what is new."""

import uuid


def copy_insert(connection, table, rows, columns=None):
    """Insert `rows` into `table`, skipping rows that conflict with existing ones.

    `rows` is an iterable of mappings keyed by column name. Values pass through
    the same SQLAlchemy type conversion as ordinary inserts, so a `Sha256` column
    takes hex strings and a `JSONB` column takes Python objects. Columns left out
    of `columns` receive their database defaults.

    Rows are streamed with COPY into a temporary table and moved with
    `INSERT ... ON CONFLICT DO NOTHING`, so repeating a load inserts nothing.
    Returns the number of rows inserted. The caller owns the transaction.
    """
    dialect = connection.dialect
    quote = dialect.identifier_preparer.quote
    names = list(columns) if columns is not None else [c.name for c in table.columns]
    converters = [
        table.columns[name].type.dialect_impl(dialect).bind_processor(dialect)
        for name in names
    ]
    target = dialect.identifier_preparer.format_table(table)
    column_list = ", ".join(quote(name) for name in names)
    staging = quote("copy_insert_" + uuid.uuid4().hex)

    # CREATE TABLE AS keeps the column types but not NOT NULL or keys, so
    # generated and defaulted columns of the target need no staging value.
    connection.exec_driver_sql(
        f"CREATE TEMP TABLE {staging} AS SELECT {column_list} FROM {target} WITH NO DATA"
    )
    with connection.connection.driver_connection.cursor() as cursor:
        with cursor.copy(f"COPY {staging} ({column_list}) FROM STDIN") as copy:
            for row in rows:
                copy.write_row(
                    [
                        row[name] if convert is None else convert(row[name])
                        for name, convert in zip(names, converters)
                    ]
                )
    inserted = connection.exec_driver_sql(
        f"INSERT INTO {target} ({column_list}) "
        f"SELECT {column_list} FROM {staging} ON CONFLICT DO NOTHING"
    ).rowcount
    connection.exec_driver_sql(f"DROP TABLE {staging}")
    return inserted
