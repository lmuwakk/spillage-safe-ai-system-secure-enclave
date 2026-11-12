#!/usr/bin/env python3
"""
Command-line expense tracker using Rich for display and JSON for storage.
"""

import argparse
import json
import os
import sys
from datetime import datetime, date

# Requirement: Use the 'rich' library for tables and formatting.
try:
    from rich.console import Console
    from rich.table import Table
    from rich.text import Text
    from rich.panel import Panel
except ImportError:
    print("Error: The 'rich' library is required. Please run: pip install rich")
    sys.exit(1)

DATA_FILE = "expenses.json"


def load_data():
    """Load expenses from the JSON file. Handles missing or corrupted files gracefully."""
    if not os.path.exists(DATA_FILE):
        return []
    
    try:
        with open(DATA_FILE, 'r') as f:
            content = f.read()
            if not content.strip():
                return []
            data = json.loads(content)
            # Basic validation to ensure it's a list
            if not isinstance(data, list):
                return []
            return data
    except (json.JSONDecodeError, IOError):
        print(f"Warning: Could not read {DATA_FILE} properly. Starting fresh.")
        return []


def save_data(data):
    """Save the expenses list to the JSON file."""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def get_next_id(data):
    """Calculate the next available ID."""
    if not data:
        return 1
    return max(item['id'] for item in data) + 1


def validate_date(date_string):
    """Validate and parse a YYYY-MM-DD date string."""
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def cmd_add(args):
    """Handle the 'add' subcommand."""
    # Validate amount
    if args.amount <= 0:
        print("Error: Amount must be greater than zero.")
        return

    # Determine date (default to today)
    current_date = date.today().isoformat()
    expense_date = args.date if args.date else current_date
    
    if not validate_date(expense_date):
        print(f"Error: Invalid date format '{expense_date}'. Please use YYYY-MM-DD.")
        return

    expenses = load_data()
    new_expense = {
        'id': get_next_id(expenses),
        'date': expense_date,
        'amount': args.amount,
        'category': args.category,
        'note': args.note if args.note else ""
    }
    
    expenses.append(new_expense)
    save_data(expenses)
    
    console = Console()
    print(f"Expense added successfully (ID: {new_expense['id']})")


def cmd_list(args):
    """Handle the 'list' subcommand."""
    expenses = load_data()
    
    # Filter by category if provided
    if args.category:
        expenses = [e for e in expenses if e['category'].lower() == args.category.lower()]

    if not expenses:
        console = Console()
        console.print(Panel("No expenses found.", style="yellow"))
        return

    # Sort by date descending (newest first)
    expenses.sort(key=lambda x: x['date'], reverse=True)

    table = Table(title="Expenses")
    table.add_column("ID", justify="right", style="cyan")
    table.add_column("Date", justify="right")
    table.add_column("Amount", justify="right")
    table.add_column("Category", style="green")
    table.add_column("Note")

    for exp in expenses:
        amount_str = f"${exp['amount']:.2f}"
        table.add_row(str(exp['id']), exp['date'], amount_str, exp['category'], exp['note'])

    console = Console()
    console.print(table)


def cmd_summary(args):
    """Handle the 'summary' subcommand."""
    expenses = load_data()
    
    # Filter by month if provided
    if args.month:
        if not validate_date(f"{args.month}-01"): # Basic check for YYYY-MM
             print(f"Error: Invalid month format '{args.month}'. Please use YYYY-MM.")
             return
        expenses = [e for e in expenses if e['date'].startswith(args.month)]

    if not expenses:
        console = Console()
        console.print(Panel("No data to summarize.", style="yellow"))
        return

    # Group by category
    summary = {}
    grand_total = 0
    
    for exp in expenses:
        cat = exp['category']
        amount = exp['amount']
        summary[cat] = summary.get(cat, 0) + amount
        grand_total += amount

    table = Table(title="Spending Summary")
    table.add_column("Category", style="cyan bold")
    table.add_column("Total Spent", justify="right")
    
    for cat, total in summary.items():
        table.add_row(cat, f"${total:.2f}")
    
    # Grand Total row
    table.add_row("[bold]Grand Total[/]", f"[bold green]${grand_total:.2f}[/]")

    console = Console()
    console.print(table)


def cmd_delete(args):
    """Handle the 'delete' subcommand."""
    expenses = load_data()
    
    # Find index of expense to delete
    target_idx = -1
    for i, exp in enumerate(expenses):
        if exp['id'] == args.id:
            target_idx = i
            break
            
    if target_idx == -1:
        print(f"Error: No expense found with ID {args.id}.")
        return

    removed_item = expenses.pop(target_idx)
    save_data(expenses)
    print(f"Expense ID {removed_item['id']} deleted successfully.")


def main():
    parser = argparse.ArgumentParser(description="Command-line Expense Tracker")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- ADD Command ---
    parser_add = subparsers.add_parser('add', help='Add a new expense')
    parser_add.add_argument('--amount', type=float, required=True, help='Cost of the item')
    parser_add.add_argument('--category', type=str, required=True, help='Category of the expense')
    parser_add.add_argument('--note', type=str, default="", help='Optional note')
    parser_add.add_argument('--date', type=str, default=None, help='Date (YYYY-MM-DD). Defaults to today.')

    # --- LIST Command ---
    parser_list = subparsers.add_parser('list', help='List expenses')
    parser_list.add_argument('--category', type=str, required=False, help='Filter by category')

    # --- SUMMARY Command ---
    parser_sum = subparsers.add_parser('summary', help='Show spending summary')
    parser_sum.add_argument('--month', type=str, default=None, help='Filter by month (YYYY-MM)')

    # --- DELETE Command ---
    parser_del = subparsers.add_parser('delete', help='Delete an expense')
    parser_del.add_argument('--id', type=int, required=True, help='ID of the expense to delete')

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == 'add':
        cmd_add(args)
    elif args.command == 'list':
        cmd_list(args)
    elif args.command == 'summary':
        cmd_summary(args)
    elif args.command == 'delete':
        cmd_delete(args)


if __name__ == "__main__":
    main()
