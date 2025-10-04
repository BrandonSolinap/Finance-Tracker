"""
Personal Finance Tracker & Analytics Tool
----------------------------------------

This application provides a simple way to record personal financial
transactions and view a summary of your income and expenses.

Features:
* Add transactions with a date (YYYY‑MM‑DD), description, category and amount.
* View all recorded transactions in a sortable table.
* Display a financial summary showing total income, total expenses and net
  balance.
* Show a basic bar chart that breaks down spending by category.

The application uses only the Python standard library (no external
dependencies). Data is persisted to a JSON file in the current directory.

How to run:
    python finance_tracker.py

This will open a GUI window. To add a transaction, fill in the fields
and click "Add Transaction". You can switch between the tabs to view
your transactions, summary, and analytics.

"""

import json
import os
from datetime import datetime
from collections import defaultdict

try:
    import tkinter as tk  # type: ignore
    from tkinter import ttk, messagebox  # type: ignore
except ImportError:
    # When tkinter is unavailable, set
    # these names to None. This allows importing FinanceTracker without
    # immediately failing. The GUI will not run until tkinter is installed.
    tk = None  # type: ignore
    ttk = None  # type: ignore
    messagebox = None  # type: ignore


class FinanceTracker:
    """Manages the storage and retrieval of financial transactions."""

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.transactions = []  # type: list[dict[str, object]]
        self.load()

    def load(self) -> None:
        """Load transactions from the JSON file, if it exists."""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # ensure list of dicts
                if isinstance(data, list):
                    self.transactions = data
                else:
                    self.transactions = []
            except (json.JSONDecodeError, OSError):
                # invalid file or cannot read; start fresh
                self.transactions = []
        else:
            self.transactions = []

    def save(self) -> None:
        """Persist current transactions to the JSON file."""
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.transactions, f, indent=4)
        except OSError:

            pass

    def add_transaction(
        self, date_str: str, description: str, category: str, amount: float
    ) -> None:
        """
        Add a transaction to the list and save it.

        :param date_str: Date of the transaction as a string (YYYY‑MM‑DD).
        :param description: Description of the transaction.
        :param category: Category (e.g., Food, Salary).
        :param amount: Positive for income, negative for expense.
        """
        transaction = {
            "date": date_str,
            "description": description,
            "category": category,
            "amount": amount,
        }
        self.transactions.append(transaction)
        self.save()

    def get_transactions(self) -> list[dict[str, object]]:
        """Return a copy of all recorded transactions."""
        return list(self.transactions)

    def compute_summary(self) -> tuple[float, float, float]:
        """
        Compute total income, total expenses, and net balance.

        :return: (total_income, total_expenses, net_balance)
        """
        total_income = 0.0
        total_expenses = 0.0
        for t in self.transactions:
            amt = float(t.get("amount", 0) or 0)
            if amt >= 0:
                total_income += amt
            else:
                total_expenses += -amt
        net = total_income - total_expenses
        return total_income, total_expenses, net

    def category_breakdown(self) -> dict[str, float]:
        """
        Return a breakdown of totals per category. Expenses are stored as positive
        values for the breakdown (i.e., absolute value).
        """
        breakdown: defaultdict[str, float] = defaultdict(float)
        for t in self.transactions:
            cat = str(t.get("category", "Uncategorized"))
            amt = float(t.get("amount", 0) or 0)
            # Represent expenses as positive values in the breakdown.
            value = -amt if amt < 0 else amt
            breakdown[cat] += value
        return dict(breakdown)


class FinanceApp:
    """Graphical user interface for the FinanceTracker."""

    def __init__(self, master) -> None:
        self.master = master
        self.master.title("Personal Finance Tracker")
        self.master.geometry("700x500")
        # Initialize tracker
        self.tracker = FinanceTracker("transactions.json")
        # Build user interface
        self._build_ui()
        # Populate initial data
        self.refresh_transactions()
        self.update_summary()

    def _build_ui(self) -> None:
        """Set up the notebook tabs and their content."""
        # Notebook with three tabs
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Frames for each tab
        self.tab_add = ttk.Frame(self.notebook)
        self.tab_view = ttk.Frame(self.notebook)
        self.tab_summary = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_add, text="Add Transaction")
        self.notebook.add(self.tab_view, text="View Transactions")
        self.notebook.add(self.tab_summary, text="Summary & Analytics")

        # Build each tab
        self._build_add_tab()
        self._build_view_tab()
        self._build_summary_tab()

    # --- Add Transaction tab ---
    def _build_add_tab(self) -> None:
        frame = self.tab_add
        padding_opts = {"padx": 10, "pady": 5}

        # Date
        ttk.Label(frame, text="Date (YYYY‑MM‑DD):").grid(row=0, column=0, sticky="e", **padding_opts)
        self.entry_date = ttk.Entry(frame)
        self.entry_date.grid(row=0, column=1, sticky="w", **padding_opts)
        # Default date to today
        self.entry_date.insert(0, datetime.today().strftime("%Y-%m-%d"))

        # Description
        ttk.Label(frame, text="Description:").grid(row=1, column=0, sticky="e", **padding_opts)
        self.entry_description = ttk.Entry(frame, width=40)
        self.entry_description.grid(row=1, column=1, sticky="w", **padding_opts)

        # Category
        ttk.Label(frame, text="Category:").grid(row=2, column=0, sticky="e", **padding_opts)
        self.combobox_category = ttk.Combobox(frame, values=self._get_unique_categories(), state="normal")
        self.combobox_category.grid(row=2, column=1, sticky="w", **padding_opts)

        # Amount
        ttk.Label(frame, text="Amount:").grid(row=3, column=0, sticky="e", **padding_opts)
        self.entry_amount = ttk.Entry(frame)
        self.entry_amount.grid(row=3, column=1, sticky="w", **padding_opts)

        # Add button
        self.button_add = ttk.Button(frame, text="Add Transaction", command=self.add_transaction)
        self.button_add.grid(row=4, column=0, columnspan=2, pady=10)

    def _get_unique_categories(self) -> list[str]:
        """Return a list of unique categories from existing transactions."""
        categories = {str(t.get("category", "")).strip() for t in self.tracker.get_transactions() if t.get("category")}
        return sorted(categories) or ["Food", "Salary", "Transport", "Utilities", "Entertainment"]

    def add_transaction(self) -> None:
        """
        Handle adding a new transaction. Validates input, updates data and UI.
        """
        date_str = self.entry_date.get().strip()
        description = self.entry_description.get().strip()
        category = self.combobox_category.get().strip() or "Uncategorized"
        amount_str = self.entry_amount.get().strip()

        # Input validation
        try:
            # Validate date format
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Invalid Date", "Please enter the date in YYYY‑MM‑DD format.")
            return
        try:
            amount = float(amount_str)
        except ValueError:
            messagebox.showerror("Invalid Amount", "Please enter a valid number for the amount.")
            return
        if not description:
            messagebox.showerror("Missing Description", "Please provide a description for the transaction.")
            return

        # Add transaction to tracker
        self.tracker.add_transaction(date_str, description, category, amount)

        # Clear inputs for next entry
        self.entry_description.delete(0, tk.END)
        self.entry_amount.delete(0, tk.END)
        # Add category to combobox values if it's new
        if category not in self.combobox_category.cget("values"):
            new_values = list(self.combobox_category.cget("values")) + [category]
            self.combobox_category.config(values=sorted(new_values))

        # Refresh views
        self.refresh_transactions()
        self.update_summary()

        messagebox.showinfo("Success", "Transaction added successfully!")

    # --- View Transactions tab ---
    def _build_view_tab(self) -> None:
        frame = self.tab_view
        # Treeview with scrollbars
        columns = ("date", "description", "category", "amount")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col.title())
            # Set column widths
            if col == "description":
                self.tree.column(col, width=250, anchor="w")
            else:
                self.tree.column(col, width=100, anchor="center")

        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscroll=vsb.set, xscroll=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

    def refresh_transactions(self) -> None:
        """Refresh the transactions displayed in the treeview."""
        # Clear existing rows
        for row in self.tree.get_children():
            self.tree.delete(row)
        # Insert updated rows
        for idx, t in enumerate(self.tracker.get_transactions()):
            values = (t["date"], t["description"], t["category"], f"{t['amount']:.2f}")
            self.tree.insert("", "end", iid=str(idx), values=values)

    # --- Summary & Analytics tab ---
    def _build_summary_tab(self) -> None:
        frame = self.tab_summary
        # Summary labels
        self.label_income = ttk.Label(frame, text="Total Income: $0.00", font=("Arial", 12))
        self.label_expenses = ttk.Label(frame, text="Total Expenses: $0.00", font=("Arial", 12))
        self.label_net = ttk.Label(frame, text="Net Balance: $0.00", font=("Arial", 12, "bold"))
        self.label_income.pack(pady=5)
        self.label_expenses.pack(pady=5)
        self.label_net.pack(pady=5)
        # Canvas for category chart
        self.canvas = tk.Canvas(frame, height=250)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def update_summary(self) -> None:
        """Update the summary labels and redraw the category chart."""
        income, expenses, net = self.tracker.compute_summary()
        self.label_income.config(text=f"Total Income: ${income:.2f}")
        self.label_expenses.config(text=f"Total Expenses: ${expenses:.2f}")
        self.label_net.config(
            text=f"Net Balance: ${net:.2f}",
            foreground="green" if net >= 0 else "red",
        )
        self.draw_category_chart()

    def draw_category_chart(self) -> None:
        """
        Draw a simple bar chart on the canvas representing the breakdown of
        spending per category. Both income and expenses are shown as
        absolute values.
        """
        self.canvas.delete("all")
        breakdown = self.tracker.category_breakdown()
        if not breakdown:
            self.canvas.create_text(
                10,
                10,
                anchor="nw",
                text="No data to display yet.",
                font=("Arial", 12),
            )
            return
        categories = list(breakdown.keys())
        values = list(breakdown.values())
        max_value = max(values)
        # Dimensions
        width = int(self.canvas.winfo_width() or 600)
        height = int(self.canvas.winfo_height() or 250)
        margin_x = 40
        margin_y = 40
        bar_gap = 10
        num_bars = len(categories)
        # Avoid division by zero
        if num_bars == 0 or max_value == 0:
            return
        bar_width = (width - 2 * margin_x - (num_bars - 1) * bar_gap) / num_bars
        # Draw bars
        for i, (cat, val) in enumerate(zip(categories, values)):
            x0 = margin_x + i * (bar_width + bar_gap)
            y0 = height - margin_y
            # Scale bar height proportionally to the max value
            bar_height = (val / max_value) * (height - 2 * margin_y)
            y1 = y0 - bar_height
            # Draw bar rectangle (blue color)
            self.canvas.create_rectangle(
                x0,
                y1,
                x0 + bar_width,
                y0,
                fill="#4A90E2",
                outline="black",
            )
            # Label above bar
            self.canvas.create_text(
                x0 + bar_width / 2,
                y1 - 5,
                text=f"${val:.2f}",
                anchor="s",
                font=("Arial", 8),
            )
            # Category label rotated if many bars
            self.canvas.create_text(
                x0 + bar_width / 2,
                y0 + 10,
                text=cat,
                anchor="n",
                font=("Arial", 8),
                angle=45 if len(categories) > 5 else 0,
            )


def main() -> None:
    # If tkinter is not available, notify the user and exit gracefully.
    if tk is None:
        print("tkinter is required to run this application. Please ensure it is installed.")
        return
    root = tk.Tk()
    app = FinanceApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()