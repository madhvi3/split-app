#!/usr/bin/env python3
"""
Setup script for Expense Splitter Backend
Handles database initialization and sample data loading
"""

import os
import sys
from decimal import Decimal
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_database():
    """Initialize database with tables and sample data"""
    try:
        from app import app, db, Person, Expense, ExpenseSplit, RecurringTransaction
        from app import ExpenseCategory, RecurrenceType, get_or_create_person
        
        print("🔄 Setting up database...")
        
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✅ Database tables created")
            
            # Check if data already exists
            if Person.query.count() > 0:
                print("ℹ️  Database already contains data")
                choice = input("Do you want to reset with fresh sample data? (y/N): ")
                if choice.lower() != 'y':
                    print("✅ Setup complete - using existing data")
                    return
                
                # Clear existing data
                print("🧹 Clearing existing data...")
                ExpenseSplit.query.delete()
                Expense.query.delete()
                RecurringTransaction.query.delete()
                Person.query.delete()
                db.session.commit()
            
            # Create sample data
            print("📊 Creating sample data...")
            
            # Sample expenses with different split scenarios
            sample_expenses = [
                {
                    'amount': 600, 
                    'description': 'Dinner at restaurant', 
                    'paid_by': 'Shantanu', 
                    'category': 'Food',
                    'splits': [
                        {'person': 'Shantanu', 'type': 'equal'},
                        {'person': 'Sanket', 'type': 'equal'},
                        {'person': 'Om', 'type': 'equal'}
                    ]
                },
                {
                    'amount': 1000, 
                    'description': 'Team lunch with custom splits', 
                    'paid_by': 'Sanket', 
                    'category': 'Food',
                    'splits': [
                        {'person': 'Shantanu', 'type': 'percentage', 'value': 40},
                        {'person': 'Sanket', 'type': 'exact', 'value': 300},
                        {'person': 'Om', 'type': 'equal'},
                        {'person': 'Priya', 'type': 'equal'}
                    ]
                },
                {
                    'amount': 450, 
                    'description': 'Groceries', 
                    'paid_by': 'Sanket', 
                    'category': 'Food',
                    'splits': [
                        {'person': 'Shantanu', 'type': 'equal'},
                        {'person': 'Sanket', 'type': 'equal'},
                        {'person': 'Om', 'type': 'equal'}
                    ]
                },
                {
                    'amount': 300, 
                    'description': 'Petrol', 
                    'paid_by': 'Om', 
                    'category': 'Travel',
                    'splits': [
                        {'person': 'Shantanu', 'type': 'equal'},
                        {'person': 'Sanket', 'type': 'equal'},
                        {'person': 'Om', 'type': 'equal'}
                    ]
                },
                {
                    'amount': 800, 
                    'description': 'Electric Bill', 
                    'paid_by': 'Om', 
                    'category': 'Utilities',
                    'splits': [
                        {'person': 'Shantanu', 'type': 'percentage', 'value': 50},
                        {'person': 'Sanket', 'type': 'percentage', 'value': 30},
                        {'person': 'Om', 'type': 'percentage', 'value': 20}
                    ]
                }
            ]
            
            # Create expenses with splits
            for expense_data in sample_expenses:
                # Create people
                for split in expense_data['splits']:
                    get_or_create_person(split['person'])
                get_or_create_person(expense_data['paid_by'])
                
                # Create expense
                expense = Expense(
                    amount=Decimal(str(expense_data['amount'])),
                    description=expense_data['description'],
                    paid_by=expense_data['paid_by'],
                    category=ExpenseCategory(expense_data['category'])
                )
                db.session.add(expense)
                db.session.flush()
                
                # Calculate and create splits
                total_amount = Decimal(str(expense_data['amount']))
                remaining_amount = total_amount
                equal_splits = []
                
                # First pass: handle exact and percentage splits
                for split in expense_data['splits']:
                    if split['type'] == 'exact':
                        amount = Decimal(str(split['value']))
                        split_record = ExpenseSplit(
                            expense_id=expense.id,
                            person_name=split['person'],
                            split_type='exact',
                            split_value=split['value'],
                            calculated_amount=amount
                        )
                        db.session.add(split_record)
                        remaining_amount -= amount
                        
                    elif split['type'] == 'percentage':
                        percentage = Decimal(str(split['value']))
                        amount = total_amount * percentage / 100
                        split_record = ExpenseSplit(
                            expense_id=expense.id,
                            person_name=split['person'],
                            split_type='percentage',
                            split_value=split['value'],
                            calculated_amount=amount
                        )
                        db.session.add(split_record)
                        remaining_amount -= amount
                        
                    elif split['type'] == 'equal':
                        equal_splits.append(split['person'])
                
                # Second pass: handle equal splits
                if equal_splits:
                    equal_amount = remaining_amount / len(equal_splits)
                    for person in equal_splits:
                        split_record = ExpenseSplit(
                            expense_id=expense.id,
                            person_name=person,
                            split_type='equal',
                            split_value=None,
                            calculated_amount=equal_amount
                        )
                        db.session.add(split_record)
            
            # Create sample recurring transaction
            recurring = RecurringTransaction(
                amount=Decimal('15000'),
                description='Monthly Rent',
                paid_by='Shantanu',
                category=ExpenseCategory.UTILITIES,
                recurrence_type=RecurrenceType.MONTHLY,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2025, 12, 31)
            )
            db.session.add(recurring)
            
            db.session.commit()
            
            print("✅ Sample data created successfully!")
            print(f"📊 Created {Person.query.count()} people")
            print(f"💰 Created {Expense.query.count()} expenses")
            print(f"🔄 Created {RecurringTransaction.query.count()} recurring transactions")
            print(f"📈 Created {ExpenseSplit.query.count()} expense splits")
            
    except ImportError as e:
        print(f"❌ Error importing app modules: {e}")
        print("Make sure you're running this from the project directory")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        sys.exit(1)

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import flask
        import flask_sqlalchemy
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def main():
    """Main setup function"""
    print("🚀 Expense Splitter Backend Setup")
    print("=" * 40)
    
    if not check_dependencies():
        sys.exit(1)
    
    setup_database()
    
    print("\n🎉 Setup complete!")
    print("To start the application:")
    print("  python app.py")
    print("\nWeb dashboard will be available at:")
    print("  http://localhost:5000")

if __name__ == "__main__":
    main()