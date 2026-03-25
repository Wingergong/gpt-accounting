# FastAPI Expense Tracker

A modern, secure expense tracking application built with FastAPI and SQLite. Track your daily expenses, categorize spending, and analyze monthly statistics with an intuitive web interface.

## Features

✨ **Core Functionality**
- Add, retrieve, and delete expenses
- Categorize expenses for better organization
- Monthly statistics and spending analysis
- Real-time expense tracking by date
- RESTful API endpoints

🔒 **Security**
- HTTPS support with SSL/TLS certificates
- CORS enabled for cross-origin requests
- Secure database operations using SQLAlchemy ORM

🎨 **User Interface**
- Responsive HTML frontend
- Bootstrap CSS framework integration
- Bootstrap Icons for visual appeal
- Clean, modern design

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Installation

1. **Clone the repository** (or download the project)
```bash
git clone https://github.com/YGONG6_ford/gpt_accounting.git
cd FastAPIProject
```

2. **Create a virtual environment** (recommended)
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

## Configuration

### SSL/TLS Certificates

The application supports HTTPS with SSL certificates. Place your certificate files in the `www-gongpingting-top/Nginx/` directory:

- **Certificate**: `www.gongpingting.top_cert_chain.pem`
- **Private Key**: `www.gongpingting.top_key.key`

If certificates are not found, the application falls back to HTTP.

### Database

The application uses SQLite by default:
```
expenses.db
```

To switch to MySQL (optional), modify the `DATABASE_URL` in `main.py`:
```python
DATABASE_URL = "mysql+pymysql://username:password@localhost:3306/expenses_db"
```

## Running the Application

### With HTTPS (Production)
```bash
python3 main.py
```

The server will automatically detect and use SSL certificates if available:
```
INFO:     Uvicorn running on https://0.0.0.0:8000
```

**Access**: `https://localhost:8000`

### Without HTTPS (Development)
If certificates are not found, the application runs in HTTP mode:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Access**: `http://localhost:8000`

### Custom Port
Edit `main.py` and change the `port` parameter:
```python
uvicorn.run(app, host="0.0.0.0", port=8080, ...)
```

## API Endpoints

### Expenses

**Create Expense**
```http
POST /expenses/
Content-Type: application/json

{
  "date": "2026-03-25",
  "amount": 25.50,
  "category": "Food"
}
```

**Get Expenses**
```http
GET /expenses?date=2026-03-25
```

Returns all expenses, optionally filtered by date.

**Delete Expense**
```http
DELETE /expenses/{expense_id}
```

### Monthly Data

**Get Monthly Statistics**
```http
GET /monthData?month=2026-03
```

Returns total spending and breakdown by category for the specified month.

## Database Schema

### Expenses Table
```sql
CREATE TABLE expenses (
    id INTEGER PRIMARY KEY,
    date DATE,
    amount FLOAT,
    category VARCHAR(50)
);
```

### Monthly Statistics Table
```sql
CREATE TABLE monthstatic (
    id INTEGER PRIMARY KEY,
    month VARCHAR(7),        -- Format: YYYY-MM
    category VARCHAR(50),
    amount FLOAT
);
```

## Project Structure

```
FastAPIProject/
├── main.py                          # Main FastAPI application
├── expenses.db                      # SQLite database
├── requirements.txt                 # Python dependencies
├── expenses.html                    # Web interface
├── static/                          # Static files
│   ├── bootstrap.min.css
│   ├── bootstrap.bundle.min.js
│   ├── bootstrap-icons.css
│   ├── main-Cyh-sEUN.css
│   └── favicon.ico
├── www-gongpingting-top/            # SSL certificates
│   └── Nginx/
│       ├── www.gongpingting.top_cert_chain.pem
│       └── www.gongpingting.top_key.key
└── README.md                        # This file
```

## Development

### Dependencies

See `requirements.txt` for all required packages:
- FastAPI
- Uvicorn
- SQLAlchemy
- Pydantic

### Adding New Features

1. Define data models in `main.py`
2. Create SQLAlchemy ORM models
3. Add corresponding API endpoints
4. Update the frontend (expenses.html) if needed

### Import Expenses from JSON

The application supports importing expenses from a JSON file:

```python
from pathlib import Path
with SessionLocal() as session:
    import_expenses_from_json("path/to/expenses.json", session)
    print("Expenses imported successfully.")
```

Expected JSON format:
```json
{
  "expenses": [
    {
      "id": 1,
      "date": "2026-03-25",
      "amount": 25.50,
      "category": "Food",
      "customCategory": "Optional custom category"
    }
  ]
}
```

## Security Considerations

🔐 **Production Deployment**
- Use trusted SSL certificates (not self-signed)
- Restrict CORS origins to your domain
- Validate and sanitize all inputs
- Use environment variables for sensitive data
- Run behind a reverse proxy (Nginx, Apache)

## Troubleshooting

### Port Already in Use
```bash
# On macOS/Linux, find and kill the process:
lsof -i :8000
kill -9 <PID>

# Then restart:
python3 main.py
```

### Certificate Not Found
Ensure certificate files exist in:
```
www-gongpingting-top/Nginx/
├── www.gongpingting.top_cert_chain.pem
└── www.gongpingting.top_key.key
```

The application will log warnings and fall back to HTTP if certificates are missing.

### Database Connection Error
- Verify `expenses.db` exists or is writable
- Check file permissions
- For MySQL, verify connection string and server status

## Browser Warning for HTTPS

When accessing `https://localhost:8000`, you may see a security warning because the certificate is self-signed. This is normal for development. To proceed:
- Click "Advanced" → "Proceed to localhost"
- Or import the certificate into your browser

## License

This project is provided as-is.

## Author

Wingergong (ygong6@ford.com)

## Contributing

Contributions and improvements are welcome!

---

**Last Updated**: March 2026

