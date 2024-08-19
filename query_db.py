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

def create_table_commits(name):
    conn = connect_db()
    cursor = conn.cursor()

    name = name.replace("-", "_")

    create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {name}_commits (
            id SERIAL PRIMARY KEY,
            sha TEXT,
            author VARCHAR(255),
            date DATE,
            comment TEXT,
            filename VARCHAR(255),
            action VARCHAR(50),
            code TEXT )
            """
    cursor.execute(create_table_query)
    print(f"New table {name}_commits created successfully")

    conn.commit()
    cursor.close()
    conn.close()

def create_table_pr(name):
    conn = connect_db()
    cursor = conn.cursor()

    name = name.replace("-", "_")

    create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {name}_pr (
            number INTEGER PRIMARY KEY,
            author VARCHAR(255),
            date DATE,
            title TEXT,
            state VARCHAR(50),
            branch VARCHAR(50),
            merge VARCHAR(50) 
            )
            """
    cursor.execute(create_table_query)
    print(f"New table {name}_pr created successfully")

    conn.commit()
    cursor.close()
    conn.close()

def create_table_pr_files(name):
    conn = connect_db()
    cursor = conn.cursor()

    name = name.replace("-", "_")

    create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {name}_pr_files (
            id SERIAL PRIMARY KEY,
            number INTEGER,
            filename VARCHAR(255),
            status VARCHAR(50),
            code TEXT )
            """
    cursor.execute(create_table_query)
    print(f"New table {name}_pr_files created successfully")

    conn.commit()
    cursor.close()
    conn.close()


#FileCodes
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

def file_exists_in_db(table, file_path):
    """Check if a file path already exists in the database."""
    conn = connect_db()
    cursor = conn.cursor()

    query = f"SELECT COUNT(1) FROM {table} WHERE url = %s"
    cursor.execute(query, (file_path,))
    exists = cursor.fetchone()[0] > 0
    cursor.close()
    return exists

def update_file_in_db(table , file_path, filename, content):
    """Update the file content in the database."""
    conn = connect_db()
    cursor = conn.cursor()

    query = f"UPDATE {table} SET content = %s WHERE url = %s"
    cursor.execute(query, (content, file_path))
    cursor.close()
    print(f"File {filename} updated successfully")

def update_filepath_in_db(table , new_file_path, old_file_path):
    """Update the filename in the database."""
    conn = connect_db()
    cursor = conn.cursor()

    query = f"UPDATE {table} SET url = %s WHERE url = %s"
    cursor.execute(query, (new_file_path, old_file_path))
    cursor.close()
    print(f"File {new_file_path} updated successfully")


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

def fetch_repo_tables():
    """Fetch all table names in the database, excluding those ending with 'commits'."""
    conn = connect_db()
    cur = conn.cursor()
    query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name NOT LIKE '%commits'
          AND table_name NOT LIKE '%pr_files'
          AND table_name NOT LIKE '%pr'

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


def insert_to_db_commits(table, sha, author, date, comment, filename, action, code):
    """Insert a file into the database"""
    conn = connect_db()
    cursor = conn.cursor()

    # query
    insert_data_query = f"""
        INSERT INTO {table} (sha, author, date, comment, filename, action, code)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
    cursor.execute(insert_data_query, (f'{sha}', f'{author}', f'{date}', f'{comment}', f'{filename}', f'{action}', f'{code}'))

    # Commit the transaction
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Data inserted successfully")


def fetch_records_in_date_range(table, start_date, end_date):
    """Fetch records from the database within a specific date range."""
    conn = connect_db()
    cur = conn.cursor()
    query = f"""
        SELECT *
        FROM {table}
        WHERE date BETWEEN %s AND %s
    """
    cur.execute(query, (start_date, end_date))
    records = cur.fetchall()
    cur.close()
    conn.close()
    return records


def fetch_records_in_date_range_and_author(table, author, start_date, end_date):
    """Fetch records from the database within a specific date range and author."""
    conn = connect_db()
    cur = conn.cursor()
    query = f"""
        SELECT *
        FROM {table}
        WHERE date BETWEEN %s AND %s
        AND author = %s
        ORDER BY date DESC
    """
    cur.execute(query, (start_date, end_date, author))
    records = cur.fetchall()
    cur.close()
    conn.close()
    return records

def fetch_records_in_date_range_author_comment(table, author, start_date, end_date, comment):
    """Fetch records from the database within a specific date range and author."""
    conn = connect_db()
    cur = conn.cursor()
    query = f"""
        SELECT *
        FROM {table}
        WHERE date BETWEEN %s AND %s
        AND author = %s
        AND comment = %s
    """
    cur.execute(query, (start_date, end_date, author, comment))
    records = cur.fetchall()
    cur.close()
    conn.close()
    return records

def commit_exist(table, sha):
    """Looks if a commit already exist in the table"""
    conn = connect_db()
    cur = conn.cursor()
    query = f"""
            SELECT COUNT(1)
            FROM {table}
            WHERE sha = %s
        """
    cur.execute(query, (sha, ))
    commit_count = cur.fetchone()[0]
    cur.close()
    conn.close()

    return commit_count > 0

#pull requests queries
def insert_to_db_pr(table, number, author, date, title, state, branch, merge):
    """Insert a file into the database"""
    conn = connect_db()
    cursor = conn.cursor()

    # query
    insert_data_query = f"""
        INSERT INTO {table}_pr (number, author, date, title, state, branch, merge)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
    cursor.execute(insert_data_query, (f'{int(number)}', f'{author}', f'{date}', f'{title}', f'{state}', f'{branch}',f'{merge}'))

    # Commit the transaction
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Data inserted successfully")

def insert_to_db_pr_files(table, number, filename, status, code):
    """Insert a file into the database"""
    conn = connect_db()
    cursor = conn.cursor()

    # query
    insert_data_query = f"""
        INSERT INTO {table}_pr_files (number, filename, status, code)
        VALUES (%s, %s, %s, %s);
        """
    cursor.execute(insert_data_query, (f'{int(number)}', f'{filename}', f'{status}', f'{code}'))

    # Commit the transaction
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Data inserted successfully")

def fetch_records_by_pr_number(table, number):
    """Fetch records from the database within a specific Pull Request number"""
    conn = connect_db()
    cur = conn.cursor()
    query = f"""
        SELECT *
        FROM {table}
        WHERE number = %s
    """
    cur.execute(query, (number,))
    records = cur.fetchall()
    cur.close()
    conn.close()
    return records


"""

print(fetch_all_table_names())

d = fetch_all_data('codingmaster8_argos_commits')
for i in d:
    print(i)

files = fetch_file('polo280_kl25z_labs', 'RGB.c')
print(files)

file = search_by_shorturl('polo280_kl25z_labs', 'PCB Inspector/PCB_Inspect.c')
print(file)

"""


