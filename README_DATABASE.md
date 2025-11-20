# MOS Evaluation App - PostgreSQL Setup

## Setup Instructions

### 1. Install PostgreSQL

#### On Ubuntu/Debian:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

#### On macOS:
```bash
brew install postgresql
brew services start postgresql
```

#### On Windows:
Download and install from: https://www.postgresql.org/download/windows/

### 2. Create Database

```bash
# Login to PostgreSQL
sudo -u postgres psql

# Create database
CREATE DATABASE mos_evaluation;

# Create user (optional, or use existing postgres user)
CREATE USER mos_user WITH PASSWORD 'your_secure_password';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE mos_evaluation TO mos_user;

# Exit
\q
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Edit `.env` with your database credentials:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mos_evaluation
DB_USER=postgres
DB_PASSWORD=your_password_here
```

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 5. Initialize Database Tables

```bash
python database.py
```

This will create the following tables:
- `participants`: Stores participant information (name, email)
- `evaluations`: Stores all evaluation ratings

### 6. Run the Application

```bash
streamlit run main.py
```

## Database Schema

### `participants` Table
- `id` (SERIAL PRIMARY KEY)
- `name` (VARCHAR(255))
- `email` (VARCHAR(255))
- `created_at` (TIMESTAMP)

### `evaluations` Table
- `id` (SERIAL PRIMARY KEY)
- `participant_id` (INTEGER, FOREIGN KEY)
- `sample_type` (VARCHAR(50)) - 'sunda' or 'indonesian'
- `sample_index` (INTEGER) - Index of the sample (0-9)
- `model_id` (VARCHAR(10)) - 'A', 'B', 'C', 'D', 'E', 'F'
- `model_name` (VARCHAR(255)) - Full model name
- `rating` (INTEGER) - Rating from 1-5
- `audio_path` (TEXT) - Path to the audio file
- `original_text` (TEXT) - Original transcription
- `created_at` (TIMESTAMP)

## Features

1. **Automatic Database Initialization**: Tables are created automatically on first run
2. **Duplicate Prevention**: Checks if email already exists before submission
3. **Backup to JSON**: All submissions are also saved as JSON files
4. **Statistics Dashboard**: View aggregated statistics by model
5. **Error Handling**: Graceful error handling with user-friendly messages

## Querying the Database

### View all evaluations:
```sql
SELECT * FROM evaluations ORDER BY created_at DESC;
```

### View statistics by model:
```sql
SELECT 
    model_id,
    model_name,
    COUNT(*) as total_ratings,
    ROUND(AVG(rating)::numeric, 2) as average_rating
FROM evaluations
GROUP BY model_id, model_name
ORDER BY model_id;
```

### View participant history:
```sql
SELECT 
    p.name,
    p.email,
    COUNT(e.id) as total_evaluations,
    AVG(e.rating) as average_rating
FROM participants p
LEFT JOIN evaluations e ON p.id = e.participant_id
GROUP BY p.id, p.name, p.email;
```

## Troubleshooting

### Connection Error:
- Verify PostgreSQL is running: `sudo systemctl status postgresql`
- Check credentials in `.env` file
- Ensure database exists: `psql -U postgres -l`

### Permission Error:
- Grant proper privileges to the user
- Check PostgreSQL authentication in `pg_hba.conf`

### Import Error:
- Reinstall psycopg2: `pip install --force-reinstall psycopg2-binary`
