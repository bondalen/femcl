#!/usr/bin/env python3
"""
FEMCL - Проверка доступных баз данных MS SQL Server
"""
import os
import sys
import pyodbc
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

load_dotenv()
console = Console()

def check_mssql_databases():
    """Проверка доступных баз данных на MS SQL Server"""
    try:
        server = os.getenv('MSSQL_SERVER', 'localhost')
        port = os.getenv('MSSQL_PORT', '1433')
        user = os.getenv('MSSQL_USER', 'sa')
        password = os.getenv('MSSQL_PASSWORD', 'kolob_OK1')
        
        # Подключение без указания базы данных
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server},{port};"
            f"UID={user};"
            f"PWD={password};"
            "TrustServerCertificate=yes;"
        )
        
        console.print(f"[blue]Подключение к MS SQL Server...[/blue]")
        console.print(f"Server: {server}:{port}")
        console.print(f"User: {user}")
        
        conn = pyodbc.connect(conn_str)
        console.print("[green]✅ Подключение успешно![/green]")
        
        with conn.cursor() as cur:
            # Получение списка баз данных
            cur.execute("SELECT name FROM sys.databases WHERE database_id > 4 ORDER BY name;")
            databases = cur.fetchall()
            
            table = Table(title="Доступные базы данных")
            table.add_column("База данных", style="cyan")
            
            for db in databases:
                table.add_row(db[0])
            
            console.print(table)
            
            # Проверка версии SQL Server
            cur.execute("SELECT @@VERSION;")
            version = cur.fetchone()[0]
            console.print(f"[blue]MS SQL Server версия:[/blue] {version}")
        
        conn.close()
        console.print("[green]✅ Проверка завершена успешно![/green]")
        
    except pyodbc.Error as e:
        console.print(f"[red]❌ Ошибка подключения к MS SQL Server:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Неожиданная ошибка:[/red] {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_mssql_databases()