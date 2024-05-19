async def create_tables(pool):
    async with pool.acquire() as connection:
        await connection.execute('''
        CREATE TABLE IF NOT EXISTS users (
        user_id bigserial PRIMARY KEY,
        block boolean NOT NULL DEFAULT FALSE
        );
        CREATE TABLE IF NOT EXISTS channels (
        channel_id bigint PRIMARY KEY,
        title varchar(255) NOT NULL,
        url varchar(255) NOT NULL
        );
        ''')