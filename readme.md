```json
{
  "success": true,
  "data": {
    "Shantanu": {
      "paid": 1600.0,
      "owes": 466.67,
      "balance": 1133.33,
      "status": "owed"
    },
    "Sanket": {
      "paid": 730.0,
      "owes": 633.33,
      "balance": 96.67,
      "status": "owed"
    },
    "Om": {
      "paid": 1100.0,
      "owes": 900.0,
      "balance": 200.0,
      "status": "owed" 
    },
    "Priya": {
      "paid": 0.0,
      "owes": 430.0,
      "balance": -430.0,
      "status": "owes"
    }
  },
  "message": "Balances calculated successfully"
}# Expense Splitter Backend

A Python Flask backend system that helps groups of people split expenses fairly and calculate who owes money to whom. Perfect for roommates splitting utility bills, friends sharing dinner costs, or travel buddies managing trip expenses.

## Features

### Core Features ✅
- **Expense Tracking**: Add, view, edit, and delete expenses
- **Automatic Person Management**: People are automatically added when mentioned in expenses
- **Settlement Calculations**: Calculate optimized settlements to minimize transactions
- **Balance Tracking**: Show how much each person has spent vs their fair share
- **Data Validation**: Comprehensive input validation and error handling
- **RESTful API**: Clean, consistent API endpoints

### 🌟 Optional Features (Extra Credit) ✅
- **Recurring Transactions**: Automatically track and split regular expenses like rent or subscriptions (monthly/weekly/yearly)
- **Expense Categories**: Assign categories to expenses (Food, Travel, Utilities, Entertainment, Other)
- **Enhanced Analytics**: Monthly spending summaries, individual vs group spending patterns, category breakdowns
- **Simple Web Interface**: Basic HTML dashboard to add expenses and view balances

### Key Capabilities
- **Flexible Expense Splitting**: Equal, percentage, or exact amount splits
- **Mixed Split Types**: Combine different split types in one expense
- **Automatic Equal Fallback**: Equal splitting when no custom splits provided
- **Optimized Settlement Algorithm**: Minimizes transaction complexity
- **Robust Error Handling**: Validates split totals and constraints
- **Sample Data Pre-loaded**: Ready for immediate testing
- **Automatic Recurring Processing**: No manual intervention needed
- **Multi-dimensional Analytics**: Category, time, and person-based insights

## API Endpoints

### Expense Management
- `GET /expenses` - List all expenses (with optional filtering)
- `POST /expenses` - Add new expense
- `PUT /expenses/:id` - Update expense
- `DELETE /expenses/:id` - Delete expense

### Settlement Calculations
- `GET /settlements` - Get optimized settlement transactions
- `GET /balances` - Show each person's balance (owes/owed)
- `GET /people` - List all people (derived from expenses)

### 🌟 Recurring Transactions
- `GET /recurring` - List all recurring transactions
- `POST /recurring` - Create new recurring transaction
- `PUT /recurring/:id` - Update recurring transaction (activate/deactivate)
- `POST /recurring/process` - Manually process recurring transactions

### 📊 Analytics & Categories
- `GET /categories` - Get all available categories
- `GET /analytics/categories` - Get spending breakdown by category
- `GET /analytics/monthly` - Get monthly spending summaries
- `GET /analytics/people` - Get individual vs group spending patterns

### 🌐 Web Interface
- `GET /` - Simple web dashboard
- `POST /web/expense` - Add expense via web form

## API Usage Examples

### Add an Expense with Custom Splits
```bash
POST /expenses
Content-Type: application/json

{
  "amount": 1000.00,
  "description": "Dinner at restaurant",
  "paid_by": "Shantanu",
  "category": "Food",
  "splits": [
    {
      "person_name": "Shantanu",
      "split_type": "percentage",
      "split_value": 50
    },
    {
      "person_name": "Sanket", 
      "split_type": "exact",
      "split_value": 300
    },
    {
      "person_name": "Om",
      "split_type": "equal"
    },
    {
      "person_name": "Priya",
      "split_type": "equal"
    }
  ]
}
```

**Split Types:**
- **`equal`**: Split remaining amount equally among equal participants
- **`percentage`**: Specify percentage of total (1-100)
- **`exact`**: Specify exact amount in currency

**How it works:**
1. **Exact amounts** are allocated first (Sanket pays ₹300)
2. **Percentage amounts** are calculated next (Shantanu pays 50% = ₹500)
3. **Equal splits** share the remaining amount (Om & Priya split ₹200 = ₹100 each)

### Add Simple Equal Split Expense
```bash
POST /expenses
Content-Type: application/json

{
  "amount": 60.00,
  "description": "Coffee",
  "paid_by": "Shantanu",
  "category": "Food"
}
```
*If no splits provided, automatically creates equal split among all existing people*

### Create Recurring Transaction
```bash
POST /recurring
Content-Type: application/json

{
  "amount": 15000.00,
  "description": "Monthly Rent",
  "paid_by": "Shantanu",
  "category": "Utilities",
  "recurrence_type": "monthly",
  "start_date": "2024-01-01T00:00:00",
  "end_date": "2025-12-31T23:59:59"
}
```

### Get Category Analytics
```bash
GET /analytics/categories?start_date=2024-01-01&end_date=2024-12-31
```

```json
{
  "success": true,
  "data": {
    "categories": [
      {
        "category": "Food",
        "amount": 1330.0,
        "percentage": 31.25,
        "count": 3
      },
      {
        "category": "Utilities", 
        "amount": 2000.0,
        "percentage": 46.99,
        "count": 2
      }
    ],
    "total_amount": 4260.0,
    "total_expenses": 7
  }
}
```

### Response Format
```json
{
  "success": true,
  "data": {
    "id": 1,
    "amount": 1000.0,
    "description": "Dinner at restaurant",
    "paid_by": "Shantanu",
    "category": "Food",
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:30:00",
    "is_recurring": false,
    "splits": [
      {
        "id": 1,
        "person_name": "Shantanu",
        "split_type": "percentage",
        "split_value": 50.0,
        "calculated_amount": 500.0
      },
      {
        "id": 2,
        "person_name": "Sanket",
        "split_type": "exact", 
        "split_value": 300.0,
        "calculated_amount": 300.0
      },
      {
        "id": 3,
        "person_name": "Om",
        "split_type": "equal",
        "split_value": null,
        "calculated_amount": 100.0
      },
      {
        "id": 4,
        "person_name": "Priya",
        "split_type": "equal",
        "split_value": null,
        "calculated_amount": 100.0
      }
    ]
  },
  "message": "Expense added successfully"
}
```

### Get Settlement Summary
```bash
GET /settlements
```

```json
{
  "success": true,
  "data": [
    {
      "from": "Om",
      "to": "Shantanu",
      "amount": 266.67
    },
    {
      "from": "Sanket",
      "to": "Shantanu",
      "amount": 123.33
    }
  ],
  "message": "Found 2 settlement transactions"
}
```

## Local Development Setup

### Prerequisites
- Python 3.7+
- pip

### Installation
1. Clone the repository:
```bash
git clone <repository-url>
cd expense-splitter
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

The API will be available at `http://localhost:5000`

### Sample Data
The application comes pre-loaded with sample data:
- **People**: Shantanu, Sanket, Om
- **Expenses**: 
  - Dinner (₹600, paid by Shantanu) - Food
  - Groceries (₹450, paid by Sanket) - Food
  - Petrol (₹300, paid by Om) - Travel
  - Movie Tickets (₹500, paid by Shantanu) - Entertainment
  - Pizza (₹280, paid by Sanket) - Food
  - Electric Bill (₹800, paid by Om) - Utilities
  - Internet Bill (₹1200, paid by Shantanu) - Utilities
- **Recurring Transaction**: Monthly Rent (₹15000, paid by Shantanu) - Utilities

### 🌐 Web Dashboard
Visit `http://localhost:5000` to access the simple web dashboard that allows you to:
- Add new expenses through a user-friendly form
- View current balances and settlement recommendations
- See spending breakdown by category
- Browse recent expenses
- Access API documentation

## Deployment

### Environment Variables
- `DATABASE_URL`: Database connection string (defaults to SQLite for local development)

### Recommended Deployment Platforms
- **Railway.app** (Recommended)
- **Render.com**
- **Heroku**

### Deployment Steps for Railway
1. Connect your GitHub repository to Railway
2. Set environment variables if needed
3. Railway will automatically detect the Python app and deploy

### For Production Database
Replace SQLite with PostgreSQL by setting the `DATABASE_URL` environment variable:
```
DATABASE_URL=postgresql://username:password@host:port/database
```

## 🧮 Settlement Calculation Logic

The expense splitter uses an intelligent algorithm to minimize the number of transactions needed to settle all debts.

### How Settlement Calculation Works

#### Step 1: Calculate Individual Balances
For each person, the system calculates:
- **Amount Paid**: Total of all expenses they paid for
- **Amount Owed**: Sum of their calculated shares from all expense splits
- **Net Balance**: `Amount Paid - Amount Owed`
  - **Positive balance**: Person is owed money
  - **Negative balance**: Person owes money
  - **Zero balance**: Person is settled

#### Step 2: Split Types and Calculation Priority
When processing expense splits, the system handles different split types in this order:

1. **Exact Amounts** (`"split_type": "exact"`): Fixed currency amounts allocated first
2. **Percentage Splits** (`"split_type": "percentage"`): Calculated as percentage of total expense
3. **Equal Splits** (`"split_type": "equal"`): Remaining amount divided equally among equal participants

**Example Calculation:**
```
Expense: ₹1000 "Team Dinner"
Splits:
- Shantanu: 40% = ₹400
- Sanket: Exact ₹300 = ₹300  
- Om: Equal = ₹150 (₹300 remaining ÷ 2)
- Priya: Equal = ₹150 (₹300 remaining ÷ 2)
Total: ₹400 + ₹300 + ₹150 + ₹150 = ₹1000 ✓
```

#### Step 3: Settlement Optimization Algorithm
The system uses a greedy algorithm to minimize transactions:

1. **Separate Debtors and Creditors**: 
   - Debtors: People with negative balances (owe money)
   - Creditors: People with positive balances (are owed money)

2. **Match Optimal Pairs**: 
   - For each debtor, find the creditor who can receive the most money
   - Calculate settlement amount as `min(debtor_owes, creditor_owed)`
   - Create settlement transaction

3. **Update Remaining Balances**: Continue until all balances are zero

**Example Settlement:**
```
Before Settlement:
- Shantanu: +₹500 (owed)
- Sanket: -₹200 (owes) 
- Om: -₹300 (owes)

Optimized Settlements:
1. Om pays Shantanu ₹300
2. Sanket pays Shantanu ₹200

Result: Everyone settled with just 2 transactions
(Instead of potentially 3+ transactions in a naive approach)
```

### Mathematical Properties

- **Conservation**: Total amount paid always equals total amount owed
- **Minimality**: Algorithm produces the minimum number of settlement transactions
- **Accuracy**: Uses Decimal arithmetic to avoid floating-point precision errors
- **Completeness**: Guarantees all debts are settled when algorithm completes

### Edge Cases Handled

1. **Empty Database**: Returns empty balances and settlements
2. **Single Person**: No settlements needed
3. **Already Settled**: Returns empty settlement list
4. **Rounding**: Small differences (< ₹0.01) are handled gracefully
5. **Mixed Split Types**: Properly validates and calculates complex scenarios

## 📚 Complete API Documentation

### Base URL
```
Production: https://your-app-name.railway.app
Local: http://localhost:5000
```

### Response Format
All API responses follow this consistent format:
```json
{
  "success": boolean,
  "data": object|array,
  "message": string,
  "errors": array (optional, only on validation failures)
}
```

### HTTP Status Codes
- `200 OK`: Successful GET/PUT requests
- `201 Created`: Successful POST requests  
- `400 Bad Request`: Validation errors
- `404 Not Found`: Resource not found
- `405 Method Not Allowed`: Invalid HTTP method
- `500 Internal Server Error`: Server errors

---

## 📋 Complete API Endpoints Reference

### 💰 Expense Management

#### `GET /expenses`
List all expenses with optional filtering.

**Query Parameters:**
- `category` (optional): Filter by category (Food, Travel, Utilities, Entertainment, Other)
- `paid_by` (optional): Filter by person who paid
- `start_date` (optional): Start date filter (ISO format: YYYY-MM-DD)
- `end_date` (optional): End date filter (ISO format: YYYY-MM-DD)

**Response:** Array of expense objects with splits

#### `POST /expenses`
Add new expense with optional custom splits.

**Request Body:**
```json
{
  "amount": number (required, > 0),
  "description": string (required, non-empty),
  "paid_by": string (required, person name),
  "category": string (optional, default: "Other"),
  "splits": array (optional, see split object below)
}
```

**Split Object:**
```json
{
  "person_name": string (required),
  "split_type": "equal|percentage|exact" (required),
  "split_value": number (required for percentage/exact, 1-100 for percentage)
}
```

**Validation Rules:**
- Amount must be positive
- Description cannot be empty
- Split percentages cannot exceed 100%
- Exact amounts cannot exceed total expense
- At least one split required if splits provided

#### `PUT /expenses/{id}`
Update existing expense. Same request body as POST.

#### `DELETE /expenses/{id}`
Delete expense and all associated splits.

---

### 🏛️ People & Settlements

#### `GET /people`
List all people (automatically created from expenses).

#### `GET /balances`
Get current balance for each person.

**Response:**
```json
{
  "success": true,
  "data": {
    "PersonName": {
      "paid": number,
      "owes": number, 
      "balance": number,
      "status": "owed|owes|settled"
    }
  }
}
```

#### `GET /settlements`
Get optimized settlement transactions.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "from": "DebtorName",
      "to": "CreditorName", 
      "amount": number
    }
  ]
}
```

---

### 🔄 Recurring Transactions

#### `GET /recurring`
List all recurring transaction templates.

#### `POST /recurring`
Create new recurring transaction template.

**Request Body:**
```json
{
  "amount": number (required),
  "description": string (required),
  "paid_by": string (required),
  "category": string (optional),
  "recurrence_type": "weekly|monthly|yearly" (required),
  "start_date": string (required, ISO format),
  "end_date": string (optional, ISO format)
}
```

#### `PUT /recurring/{id}`
Update recurring transaction (typically to activate/deactivate).

**Request Body:**
```json
{
  "is_active": boolean,
  "end_date": string (optional)
}
```

#### `POST /recurring/process`
Manually trigger processing of recurring transactions.

---

### 📊 Analytics

#### `GET /categories`
Get all available expense categories.

#### `GET /analytics/categories`
Get spending breakdown by category.

**Query Parameters:**
- `start_date` (optional): Filter start date
- `end_date` (optional): Filter end date

#### `GET /analytics/monthly`
Get monthly spending summaries.

**Query Parameters:**
- `year` (optional): Year to analyze (default: current year)

#### `GET /analytics/people`
Get individual spending patterns and statistics.

---

### 🔧 Admin Endpoints

#### `POST /admin/clean-db`
⚠️ **WARNING**: Permanently delete all data from database.

#### `POST /admin/reset-sample-data`
Clean database and reload fresh sample data.

---

### 🌐 Web Interface

#### `GET /`
Access interactive web dashboard (open in browser).

---

## 🚀 Known Limitations and Assumptions

### Current Limitations

1. **Single Currency**: Only supports one currency (₹ INR in examples)
2. **No User Authentication**: No login system or user access control
3. **Basic Web Interface**: Simple dashboard without advanced UI features
4. **No File Uploads**: Cannot attach receipts or images to expenses
5. **Timezone Handling**: All dates stored in UTC, no timezone conversion
6. **No Audit Trail**: Changes to expenses don't maintain history
7. **Memory-based Processing**: Recurring transactions processed on-demand

### Assumptions Made

1. **Trust-based System**: Assumes honest reporting of expenses
2. **Equal Default**: When no splits specified, assumes equal division among all people
3. **Name-based Identity**: People identified by name only (case-sensitive)
4. **Positive Amounts**: All expenses and splits must be positive values
5. **Immediate Settlement**: Assumes settlements happen immediately when calculated
6. **Decimal Precision**: Uses 2 decimal places for currency calculations
7. **Linear Recurrence**: Recurring transactions follow simple time patterns

### Future Enhancement Opportunities

1. **Multi-currency Support**: Currency conversion and international splitting
2. **User Authentication**: Secure login and user management
3. **Advanced Web UI**: Rich interface with charts, graphs, and better UX
4. **Mobile App**: Native mobile applications for iOS/Android
5. **Receipt Management**: Photo upload and OCR for automatic expense entry
6. **Export Features**: PDF reports, Excel exports, accounting software integration
7. **Notification System**: Email/SMS alerts for settlements and reminders
8. **Group Management**: Multiple expense groups with different participants
9. **Payment Integration**: Direct integration with payment apps (UPI, PayPal, etc.)
10. **Advanced Analytics**: Trends, predictions, budget tracking, and insights

### Technical Debt

1. **Error Handling**: Could be more granular with specific error codes
2. **Performance**: No caching or query optimization for large datasets
3. **Testing**: Lacks comprehensive unit and integration tests
4. **Documentation**: API documentation could be auto-generated (OpenAPI/Swagger)
5. **Logging**: Basic logging, could be enhanced for production monitoring
6. **Security**: No rate limiting, input sanitization, or SQL injection protection

### Example
If three people have these balances:
- Shantanu: +₹390 (owed money)
- Sanket: -₹123.33 (owes money)  
- Om: -₹266.67 (owes money)

The algorithm generates:
- Om pays Shantanu ₹266.67
- Sanket pays Shantanu ₹123.33

This settles all debts with just 2 transactions instead of potentially more complex arrangements.

## Error Handling

The API includes comprehensive error handling:

- **400 Bad Request**: Invalid input data
- **404 Not Found**: Resource not found
- **405 Method Not Allowed**: Invalid HTTP method
- **500 Internal Server Error**: Server errors

All errors return consistent JSON format:
```json
{
  "success": false,
  "message": "Error description",
  "errors": ["Detailed error messages"]
}
```

## Data Validation

- **Amount**: Must be positive number
- **Description**: Required, non-empty string
- **Paid By**: Required, non-empty string
- **Person Names**: Automatically trimmed and validated

## Testing

### Manual Testing
Use the provided sample data and web dashboard to test:

#### Core Features:
1. View all expenses: `GET /expenses`
2. Check balances: `GET /balances`
3. Get settlements: `GET /settlements`
4. Add new expense: `POST /expenses`
5. Update expense: `PUT /expenses/1`
6. Delete expense: `DELETE /expenses/1`

#### 🌟 Optional Features:
7. **Recurring Transactions**:
   - List recurring: `GET /recurring`
   - Create recurring: `POST /recurring`
   - Process recurring: `POST /recurring/process`

8. **Analytics**:
   - Category breakdown: `GET /analytics/categories`
   - Monthly summaries: `GET /analytics/monthly?year=2024`
   - People analytics: `GET /analytics/people`

9. **Web Interface**:
   - Visit dashboard: `GET /`
   - Add expense via form: Use web interface

### Postman Collection
Create a Postman collection with the following requests for comprehensive testing:

**Expense Management Folder:**
- Add Expense - Dinner (₹600, Shantanu, Food)
- Add Expense - Groceries (₹450, Sanket, Food)
- Add Expense - Petrol (₹300, Om, Travel)
- List All Expenses
- Filter Expenses by Category (Food)
- Update Expense - Change Petrol to ₹350
- Delete Expense

**🔄 Recurring Transactions Folder:**
- Create Monthly Rent (₹15000, Shantanu, Utilities)
- Create Weekly Groceries (₹500, Sanket, Food)
- List All Recurring Transactions
- Process Recurring Transactions
- Deactivate Recurring Transaction

**📊 Analytics Folder:**
- Get All Categories
- Category Analytics (Current Year)
- Monthly Analytics (2024)
- People Spending Patterns

**Settlements & People Folder:**
- Get All People
- Get Current Balances
- Get Settlement Summary

**🌐 Web Interface:**
- Test web dashboard manually at `/`

**Validation & Error Handling Folder:**
- Add Invalid Expense (negative amount)
- Add Invalid Expense (empty description)
- Add Invalid Expense (missing paid_by)
- Update Non-existent Expense
- Delete Non-existent Expense

## Known Limitations

1. **Equal Split Only**: Currently assumes equal splitting among all participants
2. **Single Currency**: No multi-currency support
3. **No User Authentication**: No login/user management system
4. **Basic Web Interface**: Simple dashboard without advanced UI features
5. **Timezone Handling**: All dates stored in UTC

## Future Enhancements

- Custom split ratios (percentage, exact amounts)
- Multi-currency support
- User authentication and group management
- Advanced web interface with charts and graphs
- Export functionality (PDF, Excel)
- Receipt uploads and image processing
- Mobile app integration
- Email notifications for settlements
- Integration with payment apps

## Tech Stack

- **Backend**: Python 3.7+ with Flask
- **Database**: SQLite (development) / PostgreSQL (production)
- **ORM**: SQLAlchemy
- **Deployment**: Railway/Render recommended

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

## License

MIT License - feel free to use this code for your projects!