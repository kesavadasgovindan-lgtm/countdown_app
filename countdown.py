import csv 
import datetime 
import sqlite3
from typing import Annotated, Optional 
import typer 
from rich.console import Console 
from rich.table import Table 

from rich import box 


DB_PATH = "countdown.db"
app=typer.Typer() 
console = Console()

def check_table_exists(table_name):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name,)
        )
        if cursor.fetchone() is None:
            console.print(f"[yellow]Table '{table_name}' does not exist. Creating it now...[/yellow]")
            cursor.execute(
                f"""CREATE TABLE {table_name} (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    date DATE NOT NULL,
                    priority BOOLEAN NOT NULL,
                    is_private BOOLEAN NOT NULL
                );"""
            )
            conn.commit()
        cursor.close()



    

@app.command("list")
def list_events(private: Annotated[bool, typer.Option("--private")] = False):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = "SELECT id, name, date, priority, is_private FROM events"
        
        if not private:
            query += " WHERE is_private = 0"

        cursor.execute(query)
        events = cursor.fetchall()
        cursor.close()
        table = Table(title="Events", box=box.ROUNDED)
        table.add_column("ID", justify="right", style="cyan", no_wrap=True)
        table.add_column("Name", style="magenta")
        table.add_column("Date", style="green")
        table.add_column("Priority", style="yellow")
        table.add_column("Private", style="red")
        table.add_column("Days Left", style="blue")

        for event in events:
            event_date = datetime.datetime.strptime(event["date"], "%Y-%m-%d").date()
            days_left = (event_date - datetime.date.today()).days
            if days_left < 0:
               msg = f"[red]{abs(days_left)} days ago[/red]"
            elif days_left == 0:
                msg = "[yellow]Today[/yellow]"
            else:
                msg = f"[green]{days_left} days left[/green]"
            table.add_row(
                str(event["id"]),
                event["name"],
                event["date"],
                "Yes" if event["priority"] else "No",
                "Yes" if event["is_private"] else "No",
                msg,)

        console.print(table)

       
@app.command("update")
def update_event(
    id: Annotated[int, typer.Argument()],
    name: Annotated[Optional[str], typer.Option("--name")] = None,
    date: Annotated[Optional[str], typer.Option("--date")] = None,
    priority: Annotated[Optional[int], typer.Option("--priority")] = None,
    is_private: Annotated[Optional[bool], typer.Option("--is-private")] = None,):

    values = []
    fields = []

    if name is not None:
        fields.append("name = ?")
        values.append(name)

    if date is not None:
        fields.append("date = ?")
        values.append(date)

    if priority is not None:
        fields.append("priority = ?")
        values.append(priority)

    if is_private is not None:
        fields.append("is_private = ?")
        values.append(is_private)   

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        if fields:
            values.append(id)
            query = f"UPDATE events SET {', '.join(fields)} WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()
            console.print(f"[green]Event with ID {id} updated successfully.[/green]")
        else:
            console.print(f"[yellow]No fields to update for event with ID {id}.[/yellow]")
        cursor.close()

@app.command("import")
def import_event(
    file_path: Annotated[str, typer.Argument()],
    skip_header: Annotated[bool, typer.Option("--skip-header")] = True,
):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        event_count = 0
        with open(file_path, "r") as csvfile:
            reader = csv.reader(csvfile)
            if skip_header:
                next(reader)  # Skip the header row
            for row in reader:
                
                cursor.execute(
                    """
                     INSERT INTO events (id,name, date, priority,is_private) 
                    VALUES (?, ?, ?, ?, ?) """,
                    (int(row[0]),row[1], row[2], bool(int(row[3])), int(row[4])),
                )
                event_count += 1

        conn.commit()
        cursor.close()
        console.print(f"[green]Successfully imported {event_count} events from {file_path}[/green]")


if __name__ == "__main__":
    check_table_exists("events")
    app()