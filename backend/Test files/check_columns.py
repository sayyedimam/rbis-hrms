import pyodbc
import os

def check_columns():
    DEFAULT_URL = "mssql+pyodbc://localhost/attendix_db?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes"
    raw_url = os.getenv("DATABASE_URL") or DEFAULT_URL
    if "localhost" in raw_url:
        conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=attendix_db;Trusted_Connection=yes;TrustServerCertificate=yes"
    else:
        conn_str = raw_url.replace("mssql+pyodbc://", "DRIVER={ODBC Driver 17 for SQL Server};")
        if '?' in conn_str:
            conn_str = conn_str.replace('?', ';').replace('&', ';')

    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    print("Columns in 'attendance' table:")
    for row in cursor.columns(table='attendance'):
        print(f"- {row.column_name}: {row.type_name}({row.column_size})")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_columns()
