"""
Migration script to update database schema from individual evaluation rows to JSON format.
Run this script if you have existing data that needs to be migrated.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
from database import get_db_connection

def migrate_to_json_format():
    """Migrate old evaluation format to new JSON format"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Check if old schema exists
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'evaluations' 
            AND column_name = 'sample_type'
        """)
        
        if not cur.fetchone():
            print("Database already using new JSON format or no migration needed.")
            return
        
        print("Old schema detected. Starting migration...")
        
        # Get all old evaluations grouped by participant
        cur.execute("""
            SELECT 
                participant_id,
                sample_type,
                sample_index,
                model_id,
                model_name,
                rating,
                audio_path,
                original_text
            FROM evaluations
            ORDER BY participant_id, created_at
        """)
        
        old_evaluations = cur.fetchall()
        
        if not old_evaluations:
            print("No data to migrate.")
            return
        
        # Group by participant
        participant_data = {}
        for eval_row in old_evaluations:
            pid = eval_row['participant_id']
            if pid not in participant_data:
                participant_data[pid] = {'ratings': []}
            
            participant_data[pid]['ratings'].append({
                'sample_type': eval_row['sample_type'],
                'sample_index': eval_row['sample_index'],
                'model_id': eval_row['model_id'],
                'model_name': eval_row['model_name'],
                'rating': eval_row['rating'],
                'audio_path': eval_row['audio_path'],
                'original_text': eval_row['original_text']
            })
        
        # Create backup table
        print("Creating backup table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS evaluations_backup AS 
            SELECT * FROM evaluations
        """)
        
        # Drop old table
        print("Dropping old evaluations table...")
        cur.execute("DROP TABLE evaluations")
        
        # Create new table with JSONB
        print("Creating new evaluations table with JSON format...")
        cur.execute("""
            CREATE TABLE evaluations (
                id SERIAL PRIMARY KEY,
                participant_id INTEGER REFERENCES participants(id),
                evaluation_data JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert migrated data
        print(f"Migrating data for {len(participant_data)} participants...")
        for participant_id, eval_data in participant_data.items():
            cur.execute("""
                INSERT INTO evaluations (participant_id, evaluation_data)
                VALUES (%s, %s)
            """, (participant_id, json.dumps(eval_data)))
        
        # Create indexes
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_evaluations_participant 
            ON evaluations(participant_id)
        """)
        
        conn.commit()
        print("✅ Migration completed successfully!")
        print(f"✅ Migrated data for {len(participant_data)} participants")
        print("ℹ️ Old data backed up in 'evaluations_backup' table")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {str(e)}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    print("=== Database Migration Script ===")
    print("This will migrate evaluation data from old format to new JSON format.")
    response = input("Do you want to proceed? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        migrate_to_json_format()
    else:
        print("Migration cancelled.")
