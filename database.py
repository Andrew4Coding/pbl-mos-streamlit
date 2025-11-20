import psycopg2
from psycopg2.extras import RealDictCursor
import os
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
            password=os.getenv('DB_PASSWORD', '')
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
                sample_type VARCHAR(50) NOT NULL,
                sample_index INTEGER NOT NULL,
                model_id VARCHAR(10) NOT NULL,
                model_name VARCHAR(255) NOT NULL,
                rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                audio_path TEXT,
                original_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index for faster queries
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_evaluations_participant 
            ON evaluations(participant_id)
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_evaluations_model 
            ON evaluations(model_id)
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

def save_evaluation(participant_id, sample_type, sample_index, model_id, model_name, rating, audio_path, original_text):
    """Save evaluation rating"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO evaluations 
            (participant_id, sample_type, sample_index, model_id, model_name, rating, audio_path, original_text)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (participant_id, sample_type, sample_index, model_id, model_name, rating, audio_path, original_text))
        
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
                e.sample_type,
                e.sample_index,
                e.model_id,
                e.model_name,
                e.rating,
                e.audio_path,
                e.original_text,
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
        # Get average ratings by model
        cur.execute("""
            SELECT 
                model_id,
                model_name,
                COUNT(*) as total_ratings,
                ROUND(AVG(rating)::numeric, 2) as average_rating,
                MIN(rating) as min_rating,
                MAX(rating) as max_rating
            FROM evaluations
            GROUP BY model_id, model_name
            ORDER BY model_id
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

if __name__ == "__main__":
    # Initialize database when run directly
    try:
        init_database()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Error: {e}")
