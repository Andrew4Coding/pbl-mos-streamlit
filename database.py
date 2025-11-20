import psycopg2
from psycopg2.extras import RealDictCursor
import os
import json
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def get_db_connection():
    """Create and return a database connection"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'mos_evaluation'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            sslmode=os.getenv('DB_SSLMODE', 'prefer')
        )
        return conn
    except Exception as e:
        raise Exception(f"Database connection error: {str(e)}")

def init_database():
    """Initialize database tables"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Create participants table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS participants (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create evaluations table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS evaluations (
                id SERIAL PRIMARY KEY,
                participant_id INTEGER REFERENCES participants(id),
                evaluation_data JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("Database tables created successfully!")
        
    except Exception as e:
        conn.rollback()
        raise Exception(f"Error initializing database: {str(e)}")
    finally:
        cur.close()
        conn.close()

def save_participant(name, email):
    """Save participant and return participant ID"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO participants (name, email)
            VALUES (%s, %s)
            RETURNING id
        """, (name, email))
        
        participant_id = cur.fetchone()[0]
        conn.commit()
        return participant_id
        
    except Exception as e:
        conn.rollback()
        raise Exception(f"Error saving participant: {str(e)}")
    finally:
        cur.close()
        conn.close()

def save_evaluation(participant_id, evaluation_data):
    """Save evaluation data as JSON"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO evaluations 
            (participant_id, evaluation_data)
            VALUES (%s, %s)
        """, (participant_id, json.dumps(evaluation_data)))
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        raise Exception(f"Error saving evaluation: {str(e)}")
    finally:
        cur.close()
        conn.close()

def get_all_evaluations():
    """Retrieve all evaluations with participant information"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT 
                e.id,
                p.name as participant_name,
                p.email as participant_email,
                e.evaluation_data,
                e.created_at
            FROM evaluations e
            JOIN participants p ON e.participant_id = p.id
            ORDER BY e.created_at DESC
        """)
        
        return cur.fetchall()
        
    except Exception as e:
        raise Exception(f"Error retrieving evaluations: {str(e)}")
    finally:
        cur.close()
        conn.close()

def get_evaluation_statistics():
    """Get statistics about evaluations"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get average ratings by model from JSONB data
        cur.execute("""
            SELECT 
                rating->>'model_id' as model_id,
                rating->>'model_name' as model_name,
                COUNT(*) as total_ratings,
                ROUND(AVG((rating->>'rating')::numeric), 2) as average_rating,
                MIN((rating->>'rating')::integer) as min_rating,
                MAX((rating->>'rating')::integer) as max_rating
            FROM evaluations e,
                 jsonb_array_elements(e.evaluation_data->'ratings') as rating
            GROUP BY rating->>'model_id', rating->>'model_name'
            ORDER BY rating->>'model_id'
        """)
        
        model_stats = cur.fetchall()
        
        # Get total participants
        cur.execute("SELECT COUNT(*) as total_participants FROM participants")
        participant_count = cur.fetchone()['total_participants']
        
        # Get total evaluations
        cur.execute("SELECT COUNT(*) as total_evaluations FROM evaluations")
        evaluation_count = cur.fetchone()['total_evaluations']
        
        return {
            'model_statistics': model_stats,
            'total_participants': participant_count,
            'total_evaluations': evaluation_count
        }
        
    except Exception as e:
        raise Exception(f"Error retrieving statistics: {str(e)}")
    finally:
        cur.close()
        conn.close()

def check_participant_exists(email):
    """Check if participant with email already exists"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT id, name FROM participants WHERE email = %s
        """, (email,))
        
        result = cur.fetchone()
        return result
        
    except Exception as e:
        raise Exception(f"Error checking participant: {str(e)}")
    finally:
        cur.close()
        conn.close()

def get_all_participants():
    """Retrieve all participants with their submission count"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT 
                p.id,
                p.name,
                p.email,
                p.created_at,
                COUNT(e.id) as total_evaluations
            FROM participants p
            LEFT JOIN evaluations e ON p.id = e.participant_id
            GROUP BY p.id, p.name, p.email, p.created_at
            ORDER BY p.created_at DESC
        """)
        
        return cur.fetchall()
        
    except Exception as e:
        raise Exception(f"Error retrieving participants: {str(e)}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    # Initialize database when run directly
    try:
        init_database()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Error: {e}")
