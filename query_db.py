import psycopg2
from psycopg2 import sql


# Database connection parameters
DB_NAME = 'new'
DB_USER = 'pablo'
DB_PASSWORD = 'pablo'
DB_HOST = 'localhost'
DB_PORT = '5432'

def connect_db():
    """Establish a connection to the PostgreSQL database."""
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    return conn

def create_table(name):
    conn = connect_db()
    cursor = conn.cursor()

    name = name.replace("-", "_")

    create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {name} (
        id SERIAL PRIMARY KEY,
        url TEXT UNIQUE,
        filename TEXT,
        content TEXT )
        """
    cursor.execute(create_table_query)
    print(f"New table {name} created successfully")

    conn.commit()
    cursor.close()
    conn.close()

def insert_to_db(table, url, filename, content):
    """Insert a file into the database"""
    conn = connect_db()
    cursor = conn.cursor()

    # query
    insert_data_query = f"""
        INSERT INTO {table} (url, filename, content)
        VALUES (%s, %s, %s)
        ON CONFLICT (url) DO NOTHING;
        """
    cursor.execute(insert_data_query, (f'{url}', f'{filename}', f'{content}'))
    #new_id = cursor.fetchone()[0]
    #print(f"Inserted data with ID: {new_id}")

    # Commit the transaction
    conn.commit()
    cursor.close()
    conn.close()
    print(f"File {filename} inserted successfully")

def delete_file(table, filename):
    """Delete a file from the database based on filename"""
    conn = connect_db()
    cursor = conn.cursor()
    # query
    delete_data_query = f"""
            DELETE FROM {table}
            WHERE filename = %s;
            """
    cursor.execute(delete_data_query, (filename,))

    conn.commit()
    cursor.close()
    conn.close()
    print(f"File {filename} deleted successfully")

def fetch_file(table, filename):
    """Fetch a file from the database based on filename"""
    conn = connect_db()
    cursor = conn.cursor()

    fetch_query = f"""
        SELECT * FROM {table}
        WHERE filename = %s;
        """
    cursor.execute(fetch_query, (filename,))
    file = cursor.fetchone()
    cursor.close()
    conn.close()
    if file:
        print(f"File fetched: {filename}")
        return file
    else:
        print(f"File {filename} not found.")
        return None

def fetch_all_table_names():
    """Fetch all table names in the database."""
    conn = connect_db()
    cur = conn.cursor()
    query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
    """
    cur.execute(query)
    tables = cur.fetchall()
    cur.close()
    conn.close()
    table_names = [table[0] for table in tables]
    return table_names

def fetch_all_data(table_name):
    """Fetch all data from the specified table."""
    conn = connect_db()
    cur = conn.cursor()
    query = sql.SQL("SELECT * FROM {}").format(sql.Identifier(table_name))
    cur.execute(query)
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

def delete_table(table_name):
    """Delete a table from the database."""
    conn = connect_db()
    cur = conn.cursor()
    delete_table_query = sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(table_name))
    cur.execute(delete_table_query)
    conn.commit()
    cur.close()
    conn.close()
    print(f"Table '{table_name}' deleted successfully.")

def get_filenames(table):
    conn = connect_db()
    cursor = conn.cursor()

    fetch_query = f"""
            SELECT filename FROM {table};
            """
    cursor.execute(fetch_query)
    filenames = cursor.fetchall()
    cursor.close()
    conn.close()

    filenames = [filename[0] for filename in filenames]

    return filenames

def get_shorturl(table):
    conn = connect_db()
    cursor = conn.cursor()

    fetch_query = f"""
                SELECT url FROM {table};
                """
    cursor.execute(fetch_query)
    urls = cursor.fetchall()
    cursor.close()
    conn.close()

    #urls = [url[0].split("/")[-2] + "/" + url[0].split("/")[-1] for url in urls]
    urls = ['/'.join(url[0].rsplit('/', 2)[-2:]) for url in urls]

    return urls

def search_by_shorturl(table, shorturl):
    conn = connect_db()
    cursor = conn.cursor()

    query = f"""
        SELECT * FROM {table}
        WHERE url LIKE '%{shorturl}';
    """

    cursor.execute(query)
    file = cursor.fetchone()
    cursor.close()
    conn.close()

    if file:
        print(f"File fetched: {shorturl}")
        return file
    else:
        print(f"File {shorturl} not found.")
        return None

"""

print(fetch_all_table_names())

d = fetch_all_data('polo280_kl25z_labs')
for i in d:
    print(i)

files = fetch_file('polo280_kl25z_labs', 'RGB.c')
print(files)

file = search_by_shorturl('polo280_kl25z_labs', 'PCB Inspector/PCB_Inspect.c')
print(file)

"""