from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import os
from collections import defaultdict
from enum import Enum
import calendar

app = Flask(__name__)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", "postgresql://postgres:GnHMImdTYLRpqHJPyruXZQgImNykmGHl@crossover.proxy.rlwy.net:46864/railway"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# Enums
class ExpenseCategory(Enum):
    FOOD = "Food"
    TRAVEL = "Travel"
    UTILITIES = "Utilities"
    ENTERTAINMENT = "Entertainment"
    OTHER = "Other"


class RecurrenceType(Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


# Models
class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
        }


class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    paid_by = db.Column(db.String(100), nullable=False)
    category = db.Column(db.Enum(ExpenseCategory), default=ExpenseCategory.OTHER)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    recurring_transaction_id = db.Column(
        db.Integer, db.ForeignKey("recurring_transaction.id"), nullable=True
    )

    # Relationship to expense splits
    splits = db.relationship(
        "ExpenseSplit", backref="expense", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "amount": float(self.amount),
            "description": self.description,
            "paid_by": self.paid_by,
            "category": (
                self.category.value if self.category else ExpenseCategory.OTHER.value
            ),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_recurring": self.recurring_transaction_id is not None,
            "splits": [split.to_dict() for split in self.splits] if self.splits else [],
        }


class ExpenseSplit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey("expense.id"), nullable=False)
    person_name = db.Column(db.String(100), nullable=False)
    split_type = db.Column(
        db.String(20), nullable=False
    )  # 'equal', 'percentage', 'exact'
    split_value = db.Column(
        db.Numeric(10, 2), nullable=True
    )  # percentage or exact amount
    calculated_amount = db.Column(
        db.Numeric(10, 2), nullable=False
    )  # final amount this person owes

    def to_dict(self):
        return {
            "id": self.id,
            "person_name": self.person_name,
            "split_type": self.split_type,
            "split_value": float(self.split_value) if self.split_value else None,
            "calculated_amount": float(self.calculated_amount),
        }


class RecurringTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    paid_by = db.Column(db.String(100), nullable=False)
    category = db.Column(db.Enum(ExpenseCategory), default=ExpenseCategory.OTHER)
    recurrence_type = db.Column(db.Enum(RecurrenceType), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=True)
    last_generated = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    expenses = db.relationship("Expense", backref="recurring_transaction", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "amount": float(self.amount),
            "description": self.description,
            "paid_by": self.paid_by,
            "category": (
                self.category.value if self.category else ExpenseCategory.OTHER.value
            ),
            "recurrence_type": self.recurrence_type.value,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "last_generated": (
                self.last_generated.isoformat() if self.last_generated else None
            ),
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "generated_expenses_count": len(self.expenses),
        }


# Utility functions
def validate_expense_data(data):
    """Validate expense data"""
    errors = []

    if not data.get("amount"):
        errors.append("Amount is required")
    else:
        try:
            amount = float(data["amount"])
            if amount <= 0:
                errors.append("Amount must be positive")
        except (ValueError, TypeError):
            errors.append("Amount must be a valid number")

    if not data.get("description") or not data["description"].strip():
        errors.append("Description is required")

    if not data.get("paid_by") or not data["paid_by"].strip():
        errors.append("Paid by is required")

    # Validate category if provided
    if "category" in data and data["category"]:
        valid_categories = [cat.value for cat in ExpenseCategory]
        if data["category"] not in valid_categories:
            errors.append(f"Category must be one of: {', '.join(valid_categories)}")

    # Validate splits if provided
    if "splits" in data and data["splits"]:
        errors.extend(validate_splits(data["splits"], float(data.get("amount", 0))))

    return errors


def validate_splits(splits, total_amount):
    """Validate expense splits"""
    errors = []

    if not isinstance(splits, list) or len(splits) == 0:
        errors.append("At least one split is required")
        return errors

    total_percentage = 0
    total_exact = 0
    equal_count = 0

    for i, split in enumerate(splits):
        if not isinstance(split, dict):
            errors.append(f"Split {i+1}: Invalid split format")
            continue

        person_name = split.get("person_name", "").strip()
        split_type = split.get("split_type", "").lower()
        split_value = split.get("split_value")

        if not person_name:
            errors.append(f"Split {i+1}: Person name is required")

        if split_type not in ["equal", "percentage", "exact"]:
            errors.append(
                f"Split {i+1}: Split type must be 'equal', 'percentage', or 'exact'"
            )
            continue

        if split_type == "percentage":
            if split_value is None:
                errors.append(f"Split {i+1}: Percentage value is required")
            else:
                try:
                    percentage = float(split_value)
                    if percentage <= 0 or percentage > 100:
                        errors.append(
                            f"Split {i+1}: Percentage must be between 0 and 100"
                        )
                    else:
                        total_percentage += percentage
                except (ValueError, TypeError):
                    errors.append(f"Split {i+1}: Invalid percentage value")

        elif split_type == "exact":
            if split_value is None:
                errors.append(f"Split {i+1}: Exact amount is required")
            else:
                try:
                    amount = float(split_value)
                    if amount <= 0:
                        errors.append(f"Split {i+1}: Exact amount must be positive")
                    elif amount > total_amount:
                        errors.append(
                            f"Split {i+1}: Exact amount cannot exceed total expense amount"
                        )
                    else:
                        total_exact += amount
                except (ValueError, TypeError):
                    errors.append(f"Split {i+1}: Invalid exact amount")

        elif split_type == "equal":
            equal_count += 1

    # Validate total percentages don't exceed 100%
    if total_percentage > 100:
        errors.append(f"Total percentage ({total_percentage}%) cannot exceed 100%")

    # Validate total exact amounts don't exceed total amount
    if total_exact > total_amount:
        errors.append(
            f"Total exact amounts (₹{total_exact}) cannot exceed total expense amount (₹{total_amount})"
        )

    # Check if combination of splits is valid
    remaining_amount = (
        total_amount - total_exact - (total_amount * total_percentage / 100)
    )
    if equal_count > 0 and remaining_amount < 0:
        errors.append(
            "Not enough amount remaining for equal splits after percentage and exact amounts"
        )
    elif (
        equal_count == 0 and abs(remaining_amount) > 0.01
    ):  # Allow small rounding differences
        errors.append("Splits must add up to 100% of the expense amount")

    return errors


def calculate_split_amounts(total_amount, splits):
    """Calculate individual amounts for each split"""
    total_amount = Decimal(str(total_amount))
    calculated_splits = []

    # First pass: calculate exact and percentage amounts
    remaining_amount = total_amount
    equal_splits = []

    for split in splits:
        split_type = split["split_type"].lower()
        person_name = split["person_name"].strip()

        if split_type == "exact":
            amount = Decimal(str(split["split_value"]))
            calculated_splits.append(
                {
                    "person_name": person_name,
                    "split_type": split_type,
                    "split_value": split["split_value"],
                    "calculated_amount": amount,
                }
            )
            remaining_amount -= amount

        elif split_type == "percentage":
            percentage = Decimal(str(split["split_value"]))
            amount = total_amount * percentage / 100
            calculated_splits.append(
                {
                    "person_name": person_name,
                    "split_type": split_type,
                    "split_value": split["split_value"],
                    "calculated_amount": amount,
                }
            )
            remaining_amount -= amount

        elif split_type == "equal":
            equal_splits.append(
                {
                    "person_name": person_name,
                    "split_type": split_type,
                    "split_value": None,
                }
            )

    # Second pass: calculate equal splits from remaining amount
    if equal_splits:
        equal_amount = remaining_amount / len(equal_splits)
        for split in equal_splits:
            calculated_splits.append(
                {
                    "person_name": split["person_name"],
                    "split_type": split["split_type"],
                    "split_value": None,
                    "calculated_amount": equal_amount,
                }
            )

    return calculated_splits


def validate_recurring_data(data):
    """Validate recurring transaction data"""
    errors = validate_expense_data(data)

    if not data.get("recurrence_type"):
        errors.append("Recurrence type is required")
    else:
        valid_types = [rt.value for rt in RecurrenceType]
        if data["recurrence_type"] not in valid_types:
            errors.append(f"Recurrence type must be one of: {', '.join(valid_types)}")

    if not data.get("start_date"):
        errors.append("Start date is required")
    else:
        try:
            datetime.fromisoformat(data["start_date"].replace("Z", "+00:00"))
        except ValueError:
            errors.append("Start date must be in ISO format (YYYY-MM-DDTHH:MM:SS)")

    if data.get("end_date"):
        try:
            datetime.fromisoformat(data["end_date"].replace("Z", "+00:00"))
        except ValueError:
            errors.append("End date must be in ISO format (YYYY-MM-DDTHH:MM:SS)")

    return errors


def get_or_create_person(name):
    """Get existing person or create new one"""
    person = Person.query.filter_by(name=name).first()
    if not person:
        person = Person(name=name)
        db.session.add(person)
        db.session.commit()
    return person


def calculate_balances():
    """Calculate how much each person owes or is owed"""
    expenses = Expense.query.all()

    if not expenses:
        return {}

    # Calculate what each person paid and what they owe
    person_paid = defaultdict(Decimal)
    person_owes = defaultdict(Decimal)
    all_people = set()

    for expense in expenses:
        paid_by = expense.paid_by
        amount_paid = Decimal(str(expense.amount))
        person_paid[paid_by] += amount_paid
        all_people.add(paid_by)

        # Calculate what each person owes for this expense
        if expense.splits:
            # Use custom splits
            for split in expense.splits:
                person_name = split.person_name
                owed_amount = split.calculated_amount
                person_owes[person_name] += owed_amount
                all_people.add(person_name)
        else:
            # Fall back to equal split among all people (legacy expenses)
            # Get all people who have been involved in any expense
            all_involved_people = set()
            for exp in expenses:
                all_involved_people.add(exp.paid_by)
                if exp.splits:
                    for split in exp.splits:
                        all_involved_people.add(split.person_name)

            equal_share = amount_paid / len(all_involved_people)
            for person in all_involved_people:
                person_owes[person] += equal_share
                all_people.add(person)

    # Calculate balances (what they paid minus what they owe)
    balances = {}
    for person in all_people:
        paid = person_paid[person]
        owes = person_owes[person]
        balance = paid - owes  # positive = owed money, negative = owes money

        balances[person] = {
            "paid": float(paid),
            "owes": float(owes),
            "balance": float(balance),
            "status": "owed" if balance > 0 else "owes" if balance < 0 else "settled",
        }

    return balances


def calculate_settlements():
    """Calculate optimized settlements to minimize transactions"""
    balances = calculate_balances()

    if not balances:
        return []

    # Separate people who owe money from those who are owed money
    debtors = []  # People who owe money (negative balance)
    creditors = []  # People who are owed money (positive balance)

    for person, data in balances.items():
        balance = Decimal(str(data["balance"]))
        if balance < 0:
            debtors.append({"name": person, "amount": -balance})
        elif balance > 0:
            creditors.append({"name": person, "amount": balance})

    settlements = []

    # Match debtors with creditors to minimize transactions
    i, j = 0, 0
    while i < len(debtors) and j < len(creditors):
        debtor = debtors[i]
        creditor = creditors[j]

        # Calculate settlement amount
        settlement_amount = min(debtor["amount"], creditor["amount"])

        settlements.append(
            {
                "from": debtor["name"],
                "to": creditor["name"],
                "amount": float(settlement_amount),
            }
        )

        # Update remaining amounts
        debtor["amount"] -= settlement_amount
        creditor["amount"] -= settlement_amount

        # Move to next debtor/creditor if current one is settled
        if debtor["amount"] == 0:
            i += 1
        if creditor["amount"] == 0:
            j += 1

    return settlements


def get_next_occurrence_date(last_date, recurrence_type):
    """Calculate next occurrence date based on recurrence type"""
    if recurrence_type == RecurrenceType.WEEKLY:
        return last_date + timedelta(weeks=1)
    elif recurrence_type == RecurrenceType.MONTHLY:
        # Add one month
        if last_date.month == 12:
            return last_date.replace(year=last_date.year + 1, month=1)
        else:
            return last_date.replace(month=last_date.month + 1)
    elif recurrence_type == RecurrenceType.YEARLY:
        return last_date.replace(year=last_date.year + 1)


def process_recurring_transactions():
    """Generate expenses from active recurring transactions"""
    now = datetime.utcnow()
    recurring_transactions = RecurringTransaction.query.filter_by(is_active=True).all()

    generated_count = 0

    for rt in recurring_transactions:
        # Skip if end date has passed
        if rt.end_date and now > rt.end_date:
            rt.is_active = False
            continue

        # Determine the last generation date
        last_generated = rt.last_generated or rt.start_date

        # Generate expenses for all missed occurrences
        next_date = get_next_occurrence_date(last_generated, rt.recurrence_type)

        while next_date <= now and (not rt.end_date or next_date <= rt.end_date):
            # Create expense
            expense = Expense(
                amount=rt.amount,
                description=f"{rt.description} (Auto-generated)",
                paid_by=rt.paid_by,
                category=rt.category,
                created_at=next_date,
                recurring_transaction_id=rt.id,
            )
            db.session.add(expense)

            rt.last_generated = next_date
            generated_count += 1

            # Get next occurrence
            next_date = get_next_occurrence_date(next_date, rt.recurrence_type)

    db.session.commit()
    return generated_count


# API Routes
@app.route("/expenses", methods=["GET"])
def get_expenses():
    """Get all expenses with optional filtering"""
    try:
        # Process recurring transactions first
        process_recurring_transactions()

        # Get query parameters
        category = request.args.get("category")
        paid_by = request.args.get("paid_by")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        # Build query
        query = Expense.query

        if category:
            query = query.filter(Expense.category == ExpenseCategory(category))

        if paid_by:
            query = query.filter(Expense.paid_by == paid_by)

        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            query = query.filter(Expense.created_at >= start_dt)

        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            query = query.filter(Expense.created_at <= end_dt)

        expenses = query.order_by(Expense.created_at.desc()).all()

        return jsonify(
            {
                "success": True,
                "data": [expense.to_dict() for expense in expenses],
                "message": f"Retrieved {len(expenses)} expenses",
            }
        )
    except Exception as e:
        return (
            jsonify(
                {"success": False, "message": f"Error retrieving expenses: {str(e)}"}
            ),
            500,
        )


@app.route("/expenses", methods=["POST"])
def add_expense():
    """Add new expense"""
    try:
        data = request.get_json()

        # Validate input
        errors = validate_expense_data(data)
        if errors:
            return (
                jsonify(
                    {"success": False, "message": "Validation failed", "errors": errors}
                ),
                400,
            )

        # Create expense
        expense = Expense(
            amount=Decimal(str(data["amount"])),
            description=data["description"].strip(),
            paid_by=data["paid_by"].strip(),
            category=ExpenseCategory(data.get("category", ExpenseCategory.OTHER.value)),
        )

        # Create person if doesn't exist
        get_or_create_person(data["paid_by"].strip())

        db.session.add(expense)
        db.session.flush()  # Get the expense ID

        # Handle splits
        if "splits" in data and data["splits"]:
            # Custom splits provided
            calculated_splits = calculate_split_amounts(data["amount"], data["splits"])

            for split_data in calculated_splits:
                # Create person if doesn't exist
                get_or_create_person(split_data["person_name"])

                split = ExpenseSplit(
                    expense_id=expense.id,
                    person_name=split_data["person_name"],
                    split_type=split_data["split_type"],
                    split_value=split_data["split_value"],
                    calculated_amount=split_data["calculated_amount"],
                )
                db.session.add(split)
        else:
            # No splits provided - create equal split among all existing people
            all_people = [person.name for person in Person.query.all()]
            if expense.paid_by not in all_people:
                all_people.append(expense.paid_by)

            equal_amount = Decimal(str(data["amount"])) / len(all_people)

            for person_name in all_people:
                split = ExpenseSplit(
                    expense_id=expense.id,
                    person_name=person_name,
                    split_type="equal",
                    split_value=None,
                    calculated_amount=equal_amount,
                )
                db.session.add(split)

        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "data": expense.to_dict(),
                    "message": "Expense added successfully",
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return (
            jsonify({"success": False, "message": f"Error adding expense: {str(e)}"}),
            500,
        )


@app.route("/expenses/<int:expense_id>", methods=["PUT"])
def update_expense(expense_id):
    """Update existing expense"""
    try:
        expense = Expense.query.get(expense_id)
        if not expense:
            return jsonify({"success": False, "message": "Expense not found"}), 404

        data = request.get_json()

        # Validate input
        errors = validate_expense_data(data)
        if errors:
            return (
                jsonify(
                    {"success": False, "message": "Validation failed", "errors": errors}
                ),
                400,
            )

        # Update expense
        expense.amount = Decimal(str(data["amount"]))
        expense.description = data["description"].strip()
        expense.paid_by = data["paid_by"].strip()
        expense.category = ExpenseCategory(data.get("category", expense.category.value))
        expense.updated_at = datetime.utcnow()

        # Create person if doesn't exist
        get_or_create_person(data["paid_by"].strip())

        # Delete existing splits
        ExpenseSplit.query.filter_by(expense_id=expense.id).delete()

        # Handle splits
        if "splits" in data and data["splits"]:
            # Custom splits provided
            calculated_splits = calculate_split_amounts(data["amount"], data["splits"])

            for split_data in calculated_splits:
                # Create person if doesn't exist
                get_or_create_person(split_data["person_name"])

                split = ExpenseSplit(
                    expense_id=expense.id,
                    person_name=split_data["person_name"],
                    split_type=split_data["split_type"],
                    split_value=split_data["split_value"],
                    calculated_amount=split_data["calculated_amount"],
                )
                db.session.add(split)
        else:
            # No splits provided - create equal split among all existing people
            all_people = [person.name for person in Person.query.all()]
            if expense.paid_by not in all_people:
                all_people.append(expense.paid_by)

            equal_amount = Decimal(str(data["amount"])) / len(all_people)

            for person_name in all_people:
                split = ExpenseSplit(
                    expense_id=expense.id,
                    person_name=person_name,
                    split_type="equal",
                    split_value=None,
                    calculated_amount=equal_amount,
                )
                db.session.add(split)

        db.session.commit()

        return jsonify(
            {
                "success": True,
                "data": expense.to_dict(),
                "message": "Expense updated successfully",
            }
        )

    except Exception as e:
        db.session.rollback()
        return (
            jsonify({"success": False, "message": f"Error updating expense: {str(e)}"}),
            500,
        )


@app.route("/expenses/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id):
    """Delete expense"""
    try:
        expense = Expense.query.get(expense_id)
        if not expense:
            return jsonify({"success": False, "message": "Expense not found"}), 404

        db.session.delete(expense)
        db.session.commit()

        return jsonify({"success": True, "message": "Expense deleted successfully"})

    except Exception as e:
        db.session.rollback()
        return (
            jsonify({"success": False, "message": f"Error deleting expense: {str(e)}"}),
            500,
        )


@app.route("/people", methods=["GET"])
def get_people():
    """Get all people"""
    try:
        people = Person.query.order_by(Person.name).all()
        return jsonify(
            {
                "success": True,
                "data": [person.to_dict() for person in people],
                "message": f"Retrieved {len(people)} people",
            }
        )
    except Exception as e:
        return (
            jsonify(
                {"success": False, "message": f"Error retrieving people: {str(e)}"}
            ),
            500,
        )


@app.route("/balances", methods=["GET"])
def get_balances():
    """Get current balances for each person"""
    try:
        process_recurring_transactions()
        balances = calculate_balances()
        return jsonify(
            {
                "success": True,
                "data": balances,
                "message": "Balances calculated successfully",
            }
        )
    except Exception as e:
        return (
            jsonify(
                {"success": False, "message": f"Error calculating balances: {str(e)}"}
            ),
            500,
        )


@app.route("/settlements", methods=["GET"])
def get_settlements():
    """Get optimized settlement transactions"""
    try:
        process_recurring_transactions()
        settlements = calculate_settlements()
        return jsonify(
            {
                "success": True,
                "data": settlements,
                "message": f"Found {len(settlements)} settlement transactions",
            }
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"Error calculating settlements: {str(e)}",
                }
            ),
            500,
        )


# Recurring Transactions
@app.route("/recurring", methods=["GET"])
def get_recurring_transactions():
    """Get all recurring transactions"""
    try:
        recurring = RecurringTransaction.query.order_by(
            RecurringTransaction.created_at.desc()
        ).all()
        return jsonify(
            {
                "success": True,
                "data": [rt.to_dict() for rt in recurring],
                "message": f"Retrieved {len(recurring)} recurring transactions",
            }
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"Error retrieving recurring transactions: {str(e)}",
                }
            ),
            500,
        )


@app.route("/recurring", methods=["POST"])
def create_recurring_transaction():
    """Create new recurring transaction"""
    try:
        data = request.get_json()

        # Validate input
        errors = validate_recurring_data(data)
        if errors:
            return (
                jsonify(
                    {"success": False, "message": "Validation failed", "errors": errors}
                ),
                400,
            )

        # Parse dates
        start_date = datetime.fromisoformat(data["start_date"].replace("Z", "+00:00"))
        end_date = None
        if data.get("end_date"):
            end_date = datetime.fromisoformat(data["end_date"].replace("Z", "+00:00"))

        # Create recurring transaction
        recurring = RecurringTransaction(
            amount=Decimal(str(data["amount"])),
            description=data["description"].strip(),
            paid_by=data["paid_by"].strip(),
            category=ExpenseCategory(data.get("category", ExpenseCategory.OTHER.value)),
            recurrence_type=RecurrenceType(data["recurrence_type"]),
            start_date=start_date,
            end_date=end_date,
        )

        # Create person if doesn't exist
        get_or_create_person(data["paid_by"].strip())

        db.session.add(recurring)
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "data": recurring.to_dict(),
                    "message": "Recurring transaction created successfully",
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"Error creating recurring transaction: {str(e)}",
                }
            ),
            500,
        )


@app.route("/recurring/<int:recurring_id>", methods=["PUT"])
def update_recurring_transaction(recurring_id):
    """Update recurring transaction"""
    try:
        recurring = RecurringTransaction.query.get(recurring_id)
        if not recurring:
            return (
                jsonify(
                    {"success": False, "message": "Recurring transaction not found"}
                ),
                404,
            )

        data = request.get_json()

        # Update fields if provided
        if "is_active" in data:
            recurring.is_active = bool(data["is_active"])

        if "end_date" in data and data["end_date"]:
            recurring.end_date = datetime.fromisoformat(
                data["end_date"].replace("Z", "+00:00")
            )

        db.session.commit()

        return jsonify(
            {
                "success": True,
                "data": recurring.to_dict(),
                "message": "Recurring transaction updated successfully",
            }
        )

    except Exception as e:
        db.session.rollback()
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"Error updating recurring transaction: {str(e)}",
                }
            ),
            500,
        )


# Categories and Analytics
@app.route("/categories", methods=["GET"])
def get_categories():
    """Get all available categories"""
    try:
        categories = [
            {"value": cat.value, "name": cat.value} for cat in ExpenseCategory
        ]
        return jsonify(
            {"success": True, "data": categories, "message": "Retrieved all categories"}
        )
    except Exception as e:
        return (
            jsonify(
                {"success": False, "message": f"Error retrieving categories: {str(e)}"}
            ),
            500,
        )


@app.route("/analytics/categories", methods=["GET"])
def get_category_analytics():
    """Get spending breakdown by category"""
    try:
        process_recurring_transactions()

        # Get time range parameters
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        query = Expense.query

        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            query = query.filter(Expense.created_at >= start_dt)

        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            query = query.filter(Expense.created_at <= end_dt)

        expenses = query.all()

        # Calculate category totals
        category_totals = defaultdict(Decimal)
        total_spent = Decimal("0")

        for expense in expenses:
            category = (
                expense.category.value
                if expense.category
                else ExpenseCategory.OTHER.value
            )
            amount = Decimal(str(expense.amount))
            category_totals[category] += amount
            total_spent += amount

        # Convert to list with percentages
        category_breakdown = []
        for category, amount in category_totals.items():
            percentage = (amount / total_spent * 100) if total_spent > 0 else 0
            category_breakdown.append(
                {
                    "category": category,
                    "amount": float(amount),
                    "percentage": float(percentage),
                    "count": len(
                        [
                            e
                            for e in expenses
                            if (
                                e.category.value
                                if e.category
                                else ExpenseCategory.OTHER.value
                            )
                            == category
                        ]
                    ),
                }
            )

        # Sort by amount descending
        category_breakdown.sort(key=lambda x: x["amount"], reverse=True)

        return jsonify(
            {
                "success": True,
                "data": {
                    "categories": category_breakdown,
                    "total_amount": float(total_spent),
                    "total_expenses": len(expenses),
                },
                "message": "Category analytics retrieved successfully",
            }
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"Error retrieving category analytics: {str(e)}",
                }
            ),
            500,
        )


@app.route("/analytics/monthly", methods=["GET"])
def get_monthly_analytics():
    """Get monthly spending summaries"""
    try:
        process_recurring_transactions()

        # Get year parameter (default to current year)
        year = int(request.args.get("year", datetime.now().year))

        # Get expenses for the year
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31, 23, 59, 59)

        expenses = Expense.query.filter(
            Expense.created_at >= start_date, Expense.created_at <= end_date
        ).all()

        # Group by month
        monthly_totals = defaultdict(Decimal)
        monthly_counts = defaultdict(int)

        for expense in expenses:
            month_key = expense.created_at.strftime("%Y-%m")
            amount = Decimal(str(expense.amount))
            monthly_totals[month_key] += amount
            monthly_counts[month_key] += 1

        # Create monthly breakdown
        monthly_breakdown = []
        for month in range(1, 13):
            month_key = f"{year}-{month:02d}"
            month_name = calendar.month_name[month]

            monthly_breakdown.append(
                {
                    "month": month_key,
                    "month_name": f"{month_name} {year}",
                    "amount": float(monthly_totals.get(month_key, 0)),
                    "count": monthly_counts.get(month_key, 0),
                }
            )

        total_year = sum(monthly_totals.values())

        return jsonify(
            {
                "success": True,
                "data": {
                    "year": year,
                    "months": monthly_breakdown,
                    "total_amount": float(total_year),
                    "total_expenses": sum(monthly_counts.values()),
                },
                "message": f"Monthly analytics for {year} retrieved successfully",
            }
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"Error retrieving monthly analytics: {str(e)}",
                }
            ),
            500,
        )


@app.route("/analytics/people", methods=["GET"])
def get_people_analytics():
    """Get individual vs group spending patterns"""
    try:
        process_recurring_transactions()

        expenses = Expense.query.all()

        # Calculate person-wise statistics
        person_stats = defaultdict(
            lambda: {
                "total_spent": Decimal("0"),
                "expense_count": 0,
                "categories": defaultdict(Decimal),
                "avg_expense": Decimal("0"),
            }
        )

        total_amount = Decimal("0")

        for expense in expenses:
            person = expense.paid_by
            amount = Decimal(str(expense.amount))
            category = (
                expense.category.value
                if expense.category
                else ExpenseCategory.OTHER.value
            )

            person_stats[person]["total_spent"] += amount
            person_stats[person]["expense_count"] += 1
            person_stats[person]["categories"][category] += amount
            total_amount += amount

        # Calculate averages and convert to response format
        people_breakdown = []
        for person, stats in person_stats.items():
            avg_expense = (
                stats["total_spent"] / stats["expense_count"]
                if stats["expense_count"] > 0
                else Decimal("0")
            )
            percentage_of_total = (
                (stats["total_spent"] / total_amount * 100) if total_amount > 0 else 0
            )

            # Convert categories
            top_categories = sorted(
                [
                    {"category": cat, "amount": float(amt)}
                    for cat, amt in stats["categories"].items()
                ],
                key=lambda x: x["amount"],
                reverse=True,
            )[
                :3
            ]  # Top 3 categories

            people_breakdown.append(
                {
                    "person": person,
                    "total_spent": float(stats["total_spent"]),
                    "expense_count": stats["expense_count"],
                    "avg_expense": float(avg_expense),
                    "percentage_of_total": float(percentage_of_total),
                    "top_categories": top_categories,
                }
            )

        # Sort by total spent
        people_breakdown.sort(key=lambda x: x["total_spent"], reverse=True)

        return jsonify(
            {
                "success": True,
                "data": {
                    "people": people_breakdown,
                    "total_amount": float(total_amount),
                    "total_expenses": len(expenses),
                    "avg_expense_overall": (
                        float(total_amount / len(expenses)) if expenses else 0
                    ),
                },
                "message": "People analytics retrieved successfully",
            }
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"Error retrieving people analytics: {str(e)}",
                }
            ),
            500,
        )


# Simple Web Interface
@app.route("/")
def dashboard():
    """Simple web dashboard"""
    try:
        process_recurring_transactions()

        # Get summary data
        expenses = Expense.query.order_by(Expense.created_at.desc()).limit(10).all()
        balances = calculate_balances()
        settlements = calculate_settlements()
        people = Person.query.all()

        # Get category breakdown
        category_totals = defaultdict(float)
        for expense in Expense.query.all():
            category = (
                expense.category.value
                if expense.category
                else ExpenseCategory.OTHER.value
            )
            category_totals[category] += float(expense.amount)

        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Expense Splitter Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .card { background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; }
        .form-group { margin: 15px 0; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, select, textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        button { background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }
        button:hover { background-color: #0056b3; }
        button.danger { background-color: #dc3545; }
        button.danger:hover { background-color: #c82333; }
        button.success { background-color: #28a745; }
        button.success:hover { background-color: #218838; }
        .balance-positive { color: green; font-weight: bold; }
        .balance-negative { color: red; font-weight: bold; }
        .balance-zero { color: gray; }
        .category-badge { padding: 4px 8px; border-radius: 12px; font-size: 12px; background-color: #e9ecef; }
        .settlement { background-color: #fff3cd; padding: 10px; margin: 5px 0; border-radius: 4px; }
        .split-row { border: 1px solid #ddd; padding: 10px; margin: 5px 0; border-radius: 4px; background-color: #f8f9fa; }
        .split-controls { display: flex; gap: 10px; align-items: center; }
        .split-controls > * { margin: 0; }
        .admin-section { border: 2px solid #dc3545; padding: 15px; margin: 20px 0; border-radius: 8px; background-color: #f8d7da; }
        #splits-container { margin-top: 10px; }
        .hidden { display: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>💰 Expense Splitter Dashboard</h1>
        
        <div class="grid">
            <!-- Add Expense Form -->
            <div class="card">
                <h2>Add New Expense</h2>
                <form id="expense-form">
                    <div class="form-group">
                        <label>Amount (₹):</label>
                        <input type="number" name="amount" step="0.01" required>
                    </div>
                    <div class="form-group">
                        <label>Description:</label>
                        <input type="text" name="description" required>
                    </div>
                    <div class="form-group">
                        <label>Paid By:</label>
                        <select name="paid_by" required>
                            <option value="">Select Person</option>
                            {% for person in people %}
                            <option value="{{ person.name }}">{{ person.name }}</option>
                            {% endfor %}
                        </select>
                        <input type="text" name="new_paid_by" placeholder="Or enter new person name" style="margin-top: 5px;">
                    </div>
                    <div class="form-group">
                        <label>Category:</label>
                        <select name="category">
                            <option value="Food">Food</option>
                            <option value="Travel">Travel</option>
                            <option value="Utilities">Utilities</option>
                            <option value="Entertainment">Entertainment</option>
                            <option value="Other">Other</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="custom-splits" onchange="toggleCustomSplits()">
                            Use Custom Splits (otherwise equal split among all people)
                        </label>
                    </div>
                    
                    <div id="splits-section" class="hidden">
                        <h4>Custom Splits</h4>
                        <div id="splits-container">
                            <!-- Splits will be added here -->
                        </div>
                        <button type="button" onclick="addSplit()" class="success">Add Person</button>
                    </div>
                    
                    <button type="submit">Add Expense</button>
                </form>
            </div>

            <!-- Admin Controls -->
            <div class="card admin-section">
                <h2>🔧 Admin Controls</h2>
                <p><strong>Warning:</strong> These actions will permanently delete data!</p>
                <button onclick="cleanDatabase()" class="danger">Clean Database</button>
                <button onclick="resetSampleData()" class="success">Reset Sample Data</button>
            </div>

            <!-- Balances Summary -->
            <div class="card">
                <h2>Current Balances</h2>
                {% if balances %}
                <table>
                    <tr>
                        <th>Person</th>
                        <th>Paid</th>
                        <th>Owes</th>
                        <th>Balance</th>
                    </tr>
                    {% for person, data in balances.items() %}
                    <tr>
                        <td>{{ person }}</td>
                        <td>₹{{ "%.2f"|format(data.paid) }}</td>
                        <td>₹{{ "%.2f"|format(data.owes) }}</td>
                        <td class="{% if data.balance > 0 %}balance-positive{% elif data.balance < 0 %}balance-negative{% else %}balance-zero{% endif %}">
                            ₹{{ "%.2f"|format(data.balance) }}
                            {% if data.balance > 0 %}(owed){% elif data.balance < 0 %}(owes){% else %}(settled){% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </table>
                {% else %}
                <p>No expenses recorded yet.</p>
                {% endif %}
            </div>
        </div>

        <!-- Settlements -->
        {% if settlements %}
        <div class="card">
            <h2>💸 Settlement Recommendations</h2>
            {% for settlement in settlements %}
            <div class="settlement">
                <strong>{{ settlement.from }}</strong> should pay <strong>₹{{ "%.2f"|format(settlement.amount) }}</strong> to <strong>{{ settlement.to }}</strong>
            </div>
            {% endfor %}
        </div>
        {% endif %}

        <!-- Category Breakdown -->
        <div class="card">
            <h2>📊 Spending by Category</h2>
            {% if category_totals %}
            <table>
                <tr>
                    <th>Category</th>
                    <th>Total Amount</th>
                </tr>
                {% for category, amount in category_totals.items() %}
                <tr>
                    <td><span class="category-badge">{{ category }}</span></td>
                    <td>₹{{ "%.2f"|format(amount) }}</td>
                </tr>
                {% endfor %}
            </table>
            {% endif %}
        </div>

        <!-- Recent Expenses -->
        <div class="card">
            <h2>Recent Expenses</h2>
            {% if expenses %}
            <table>
                <tr>
                    <th>Description</th>
                    <th>Amount</th>
                    <th>Paid By</th>
                    <th>Category</th>
                    <th>Date</th>
                </tr>
                {% for expense in expenses %}
                <tr>
                    <td>{{ expense.description }}</td>
                    <td>₹{{ "%.2f"|format(expense.amount) }}</td>
                    <td>{{ expense.paid_by }}</td>
                    <td><span class="category-badge">{{ expense.category.value if expense.category else 'Other' }}</span></td>
                    <td>{{ expense.created_at.strftime('%Y-%m-%d %H:%M') }}</td>
                </tr>
                {% endfor %}
            </table>
            {% else %}
            <p>No expenses recorded yet.</p>
            {% endif %}
        </div>

        <!-- API Information -->
        <div class="card">
            <h2>🔗 API Endpoints</h2>
            <p>This dashboard is powered by RESTful APIs. Here are some key endpoints:</p>
            <ul>
                <li><code>GET /expenses</code> - List all expenses</li>
                <li><code>POST /expenses</code> - Add new expense (with custom splits)</li>
                <li><code>GET /balances</code> - Get current balances</li>
                <li><code>GET /settlements</code> - Get settlement recommendations</li>
                <li><code>GET /analytics/categories</code> - Category breakdown</li>
                <li><code>GET /analytics/monthly</code> - Monthly summaries</li>
                <li><code>GET /recurring</code> - Recurring transactions</li>
                <li><code>POST /admin/clean-db</code> - Clean database</li>
                <li><code>POST /admin/reset-sample-data</code> - Reset sample data</li>
            </ul>
        </div>
    </div>

    <script>
        let splitCount = 0;

        function toggleCustomSplits() {
            const checkbox = document.getElementById('custom-splits');
            const splitsSection = document.getElementById('splits-section');
            if (checkbox.checked) {
                splitsSection.classList.remove('hidden');
                if (splitCount === 0) {
                    addSplit(); // Add first split automatically
                }
            } else {
                splitsSection.classList.add('hidden');
            }
        }

        function addSplit() {
            splitCount++;
            const container = document.getElementById('splits-container');
            const splitDiv = document.createElement('div');
            splitDiv.className = 'split-row';
            splitDiv.id = `split-${splitCount}`;
            splitDiv.innerHTML = `
                <div class="split-controls">
                    <select name="person_${splitCount}" style="width: 25%;" required>
                        <option value="">Select Person</option>
                        {% for person in people %}
                        <option value="{{ person.name }}">{{ person.name }}</option>
                        {% endfor %}
                    </select>
                    <input type="text" name="new_person_${splitCount}" placeholder="Or new person" style="width: 20%;">
                    <select name="split_type_${splitCount}" style="width: 20%;" onchange="toggleSplitValue(${splitCount})" required>
                        <option value="equal">Equal Split</option>
                        <option value="percentage">Percentage</option>
                        <option value="exact">Exact Amount</option>
                    </select>
                    <input type="number" name="split_value_${splitCount}" id="split_value_${splitCount}" style="width: 20%;" step="0.01" disabled placeholder="Auto">
                    <button type="button" onclick="removeSplit(${splitCount})" class="danger" style="width: 10%;">Remove</button>
                </div>
            `;
            
            container.appendChild(splitDiv);
        }

        function removeSplit(id) {
            const splitDiv = document.getElementById(`split-${id}`);
            if (splitDiv) {
                splitDiv.remove();
            }
        }

        function toggleSplitValue(id) {
            const splitType = document.querySelector(`select[name="split_type_${id}"]`);
            const splitValue = document.getElementById(`split_value_${id}`);
            
            if (splitType.value === 'equal') {
                splitValue.disabled = true;
                splitValue.placeholder = 'Auto';
                splitValue.required = false;
            } else {
                splitValue.disabled = false;
                splitValue.required = true;
                if (splitType.value === 'percentage') {
                    splitValue.placeholder = 'Percentage (1-100)';
                } else {
                    splitValue.placeholder = 'Exact amount (₹)';
                }
            }
        }

        document.getElementById('expense-form').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const customSplits = document.getElementById('custom-splits').checked;
            
            // Build expense data
            const expenseData = {
                amount: parseFloat(formData.get('amount')),
                description: formData.get('description'),
                paid_by: formData.get('paid_by') || formData.get('new_paid_by'),
                category: formData.get('category')
            };

            // Add splits if custom splits are enabled
            if (customSplits) {
                const splits = [];
                
                for (let i = 1; i <= splitCount; i++) {
                    const splitDiv = document.getElementById(`split-${i}`);
                    if (!splitDiv) continue;
                    
                    const person = formData.get(`person_${i}`) || formData.get(`new_person_${i}`);
                    const splitType = formData.get(`split_type_${i}`);
                    const splitValue = formData.get(`split_value_${i}`);
                    
                    if (person && splitType) {
                        const split = {
                            person_name: person,
                            split_type: splitType
                        };
                        
                        if (splitType !== 'equal' && splitValue) {
                            split.split_value = parseFloat(splitValue);
                        }
                        
                        splits.push(split);
                    }
                }
                
                if (splits.length > 0) {
                    expenseData.splits = splits;
                }
            }

            try {
                const response = await fetch('/expenses', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(expenseData)
                });

                const result = await response.json();
                
                if (result.success) {
                    alert('Expense added successfully!');
                    location.reload();
                } else {
                    alert('Error: ' + result.message + (result.errors ? '\\n' + result.errors.join('\\n') : ''));
                }
            } catch (error) {
                alert('Error adding expense: ' + error.message);
            }
        });

        async function cleanDatabase() {
            if (!confirm('Are you sure you want to clean the entire database? This will delete ALL data!')) {
                return;
            }
            
            try {
                const response = await fetch('/admin/clean-db', { method: 'POST' });
                const result = await response.json();
                
                if (result.success) {
                    alert('Database cleaned successfully!');
                    location.reload();
                } else {
                    alert('Error: ' + result.message);
                }
            } catch (error) {
                alert('Error cleaning database: ' + error.message);
            }
        }

        async function resetSampleData() {
            if (!confirm('Reset database with fresh sample data?')) {
                return;
            }
            
            try {
                const response = await fetch('/admin/reset-sample-data', { method: 'POST' });
                const result = await response.json();
                
                if (result.success) {
                    alert('Sample data reset successfully!');
                    location.reload();
                } else {
                    alert('Error: ' + result.message);
                }
            } catch (error) {
                alert('Error resetting sample data: ' + error.message);
            }
        }
    </script>
</body>
</html>
        """

        return render_template_string(
            html_template,
            expenses=expenses,
            balances=balances,
            settlements=settlements,
            people=people,
            category_totals=dict(category_totals),
        )

    except Exception as e:
        return f"Error loading dashboard: {str(e)}", 500


@app.route("/web/expense", methods=["POST"])
def web_add_expense():
    """Add expense via web form"""
    try:
        # Get form data
        amount = request.form.get("amount")
        description = request.form.get("description")
        paid_by = request.form.get("paid_by")
        category = request.form.get("category", "Other")

        # Handle new person
        if paid_by == "new":
            paid_by = request.form.get("new_person_name", "").strip()
            if not paid_by:
                return "Please provide a name for the new person", 400

        # Validate data
        data = {
            "amount": amount,
            "description": description,
            "paid_by": paid_by,
            "category": category,
        }

        errors = validate_expense_data(data)
        if errors:
            return f"Validation errors: {', '.join(errors)}", 400

        # Create expense
        expense = Expense(
            amount=Decimal(str(amount)),
            description=description.strip(),
            paid_by=paid_by.strip(),
            category=ExpenseCategory(category),
        )

        # Create person if doesn't exist
        get_or_create_person(paid_by.strip())

        db.session.add(expense)
        db.session.commit()

        # Redirect back to dashboard
        return """
        <script>
            alert("Expense added successfully!");
            window.location.href = "/";
        </script>
        """

    except Exception as e:
        return f"Error adding expense: {str(e)}", 500


# Clean database endpoint
@app.route("/admin/clean-db", methods=["POST"])
def clean_database():
    """Clean all data from database (for testing)"""
    try:
        # Delete all data
        ExpenseSplit.query.delete()
        Expense.query.delete()
        RecurringTransaction.query.delete()
        Person.query.delete()

        db.session.commit()

        return jsonify({"success": True, "message": "Database cleaned successfully"})
    except Exception as e:
        db.session.rollback()
        return (
            jsonify(
                {"success": False, "message": f"Error cleaning database: {str(e)}"}
            ),
            500,
        )


@app.route("/admin/reset-sample-data", methods=["POST"])
def reset_sample_data():
    """Reset database with fresh sample data"""
    try:
        # Clean existing data
        ExpenseSplit.query.delete()
        Expense.query.delete()
        RecurringTransaction.query.delete()
        Person.query.delete()
        db.session.commit()

        # Create fresh sample data
        create_sample_data()

        return jsonify({"success": True, "message": "Sample data reset successfully"})
    except Exception as e:
        db.session.rollback()
        return (
            jsonify(
                {"success": False, "message": f"Error resetting sample data: {str(e)}"}
            ),
            500,
        )


def create_sample_data():
    """Create sample data for testing"""
    # Create sample people and expenses
    sample_expenses = [
        {
            "amount": 600,
            "description": "Dinner at restaurant",
            "paid_by": "Shantanu",
            "category": "Food",
        },
        {
            "amount": 450,
            "description": "Groceries",
            "paid_by": "Sanket",
            "category": "Food",
        },
        {"amount": 300, "description": "Petrol", "paid_by": "Om", "category": "Travel"},
        {
            "amount": 500,
            "description": "Movie Tickets",
            "paid_by": "Shantanu",
            "category": "Entertainment",
        },
        {
            "amount": 280,
            "description": "Pizza",
            "paid_by": "Sanket",
            "category": "Food",
        },
        {
            "amount": 800,
            "description": "Electric Bill",
            "paid_by": "Om",
            "category": "Utilities",
        },
        {
            "amount": 1200,
            "description": "Internet Bill",
            "paid_by": "Shantanu",
            "category": "Utilities",
        },
    ]

    for expense_data in sample_expenses:
        # Create person
        get_or_create_person(expense_data["paid_by"])

        # Create expense
        expense = Expense(
            amount=Decimal(str(expense_data["amount"])),
            description=expense_data["description"],
            paid_by=expense_data["paid_by"],
            category=ExpenseCategory(expense_data["category"]),
        )
        db.session.add(expense)
        db.session.flush()  # Get the expense ID

        # Create equal splits for sample data
        all_people_names = ["Shantanu", "Sanket", "Om"]
        equal_amount = Decimal(str(expense_data["amount"])) / len(all_people_names)

        for person_name in all_people_names:
            split = ExpenseSplit(
                expense_id=expense.id,
                person_name=person_name,
                split_type="equal",
                split_value=None,
                calculated_amount=equal_amount,
            )
            db.session.add(split)

    # Create sample recurring transaction
    get_or_create_person("Shantanu")
    rent_recurring = RecurringTransaction(
        amount=Decimal("15000"),
        description="Monthly Rent",
        paid_by="Shantanu",
        category=ExpenseCategory.UTILITIES,
        recurrence_type=RecurrenceType.MONTHLY,
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2025, 12, 31),
    )
    db.session.add(rent_recurring)

    db.session.commit()


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "message": "Endpoint not found"}), 404


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"success": False, "message": "Method not allowed"}), 405


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"success": False, "message": "Internal server error"}), 500


# Initialize database
def create_tables():
    with app.app_context():
        db.create_all()

        # Add sample data if database is empty
        if Person.query.count() == 0:
            create_sample_data()


if __name__ == "__main__":
    # Initialize database when app starts
    create_tables()
    app.run(debug=True, host="0.0.0.0", port=5000)
