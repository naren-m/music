"""
Database Migration and Initialization Script
Carnatic Music Learning Platform
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.database import (
    DatabaseManager, DatabaseConfig,
    Base, User, Exercise, Progress, Recording,
    Raga, Tala, Composition, Achievement, Group,
    seed_initial_data, get_db_session
)
from config.validators import validate_db_name, SecurityValidationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_database_if_not_exists():
    """Create database if it doesn't exist - SQL injection safe"""
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    from psycopg2 import sql

    config = DatabaseConfig()

    try:
        # Validate database name to prevent SQL injection
        validated_db_name = validate_db_name(config.postgresql_db)

        # Connect to postgres database to create our database
        conn = psycopg2.connect(
            host=config.postgresql_host,
            port=config.postgresql_port,
            user=config.postgresql_user,
            password=config.postgresql_password,
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        cursor = conn.cursor()

        # Check if database exists (already safe with parameterized query)
        cursor.execute(
            "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
            (validated_db_name,)
        )

        if not cursor.fetchone():
            # Use psycopg2.sql for safe identifier composition
            cursor.execute(
                sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(validated_db_name)
                )
            )
            logger.info(f"Database '{validated_db_name}' created successfully")
        else:
            logger.info(f"Database '{validated_db_name}' already exists")

        cursor.close()
        conn.close()

    except SecurityValidationError as e:
        logger.error(f"Database name validation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        raise

def initialize_database():
    """Initialize database with tables and seed data"""
    try:
        # Create database if needed
        create_database_if_not_exists()

        # Initialize database manager
        db_manager = DatabaseManager()
        db_manager.initialize_postgresql()
        db_manager.initialize_redis()

        # Create all tables
        logger.info("Creating database tables...")
        db_manager.create_tables()

        # Seed initial data
        logger.info("Seeding initial data...")
        with get_db_session() as session:
            seed_initial_data(session)

        # Health check
        health = db_manager.health_check()
        logger.info(f"Database health check: {health}")

        if all(health.values()):
            logger.info("✅ Database initialization completed successfully!")
        else:
            logger.warning(f"⚠️  Database initialization completed with warnings: {health}")

        return True

    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False

def create_sample_data():
    """Create sample data for development and testing"""
    try:
        with get_db_session() as session:

            # Create sample exercises
            sample_exercises = [
                {
                    'type': 'swara',
                    'category': 'basic',
                    'difficulty_level': 1,
                    'title': 'Single Swara Practice - Sa',
                    'description': 'Practice singing Sa with proper intonation',
                    'content_data': {
                        'target_notes': ['Sa'],
                        'drone_notes': ['Sa', 'Pa'],
                        'tempo': 60,
                        'duration': 300  # 5 minutes
                    },
                    'estimated_duration': 5
                },
                {
                    'type': 'sarali',
                    'category': 'traditional',
                    'difficulty_level': 2,
                    'title': 'Sarali Varisai - Pattern 1',
                    'description': 'First sarali varisai pattern in ascending order',
                    'content_data': {
                        'pattern': ['Sa', 'Ri', 'Ga', 'Ma', 'Pa', 'Da', 'Ni', 'Sa'],
                        'repetitions': 3,
                        'tempo_progression': [60, 80, 100],
                        'evaluation_criteria': {
                            'pitch_accuracy': 0.8,
                            'rhythm_accuracy': 0.85,
                            'smoothness': 0.7
                        }
                    },
                    'estimated_duration': 8
                },
                {
                    'type': 'janta',
                    'category': 'traditional',
                    'difficulty_level': 3,
                    'title': 'Janta Varisai - Double Notes',
                    'description': 'Practice double note patterns with even emphasis',
                    'content_data': {
                        'pattern': ['Sa', 'Sa', 'Ri', 'Ri', 'Ga', 'Ga', 'Ma', 'Ma'],
                        'emphasis': 'equal',
                        'tempo_range': [70, 120],
                        'smoothness_target': 0.85
                    },
                    'estimated_duration': 10
                }
            ]

            for exercise_data in sample_exercises:
                existing = session.query(Exercise).filter_by(title=exercise_data['title']).first()
                if not existing:
                    exercise = Exercise(**exercise_data)
                    session.add(exercise)

            # Create sample compositions
            sample_compositions = [
                {
                    'title': 'Vathapi Ganapathim',
                    'composer': 'Muthuswami Dikshitar',
                    'type': 'kriti',
                    'difficulty': 6,
                    'lyrics': {
                        'sanskrit': 'Vathapi ganapathim bhajeham',
                        'transliteration': 'Vathapi ganapathim bhajeham',
                        'translation': 'I worship Lord Ganesha of Vathapi'
                    },
                    'sections': [
                        {'name': 'Pallavi', 'content': 'Vathapi ganapathim bhajeham'},
                        {'name': 'Anupallavi', 'content': 'Bhoothathi sevitham'},
                        {'name': 'Charanam', 'content': 'Ekadantham eka nethram'}
                    ],
                    'teaching_notes': 'Focus on clear pronunciation and steady tempo'
                }
            ]

            # Get Hamsadhwani raga for the composition (we'll add it if needed)
            hamsadhwani = session.query(Raga).filter_by(name='Hamsadhwani').first()
            if not hamsadhwani:
                hamsadhwani = Raga(
                    name='Hamsadhwani',
                    melakarta_number=None,  # Janya raga
                    arohanam='S R2 G3 P N3 S',
                    avarohanam='S N3 P G3 R2 S',
                    characteristics={'time': 'evening', 'emotion': 'devotional', 'popularity': 'high'}
                )
                session.add(hamsadhwani)
                session.flush()  # Get the ID

            # Get Adi tala
            adi_tala = session.query(Tala).filter_by(name='Adi').first()

            if hamsadhwani and adi_tala:
                for comp_data in sample_compositions:
                    existing = session.query(Composition).filter_by(title=comp_data['title']).first()
                    if not existing:
                        composition = Composition(
                            **comp_data,
                            raga_id=hamsadhwani.id,
                            tala_id=adi_tala.id
                        )
                        session.add(composition)

            session.commit()
            logger.info("✅ Sample data created successfully!")

    except Exception as e:
        logger.error(f"❌ Failed to create sample data: {e}")
        raise

def validate_database():
    """Validate database setup and connections"""
    try:
        db_manager = DatabaseManager()
        db_manager.initialize_postgresql()
        db_manager.initialize_redis()

        # Test PostgreSQL
        with get_db_session() as session:
            # Count records in each table
            user_count = session.query(User).count()
            exercise_count = session.query(Exercise).count()
            raga_count = session.query(Raga).count()
            tala_count = session.query(Tala).count()
            composition_count = session.query(Composition).count()

            logger.info(f"📊 Database validation:")
            logger.info(f"  - Users: {user_count}")
            logger.info(f"  - Exercises: {exercise_count}")
            logger.info(f"  - Ragas: {raga_count}")
            logger.info(f"  - Talas: {tala_count}")
            logger.info(f"  - Compositions: {composition_count}")

        # Test Redis
        redis_client = db_manager.get_redis()
        redis_client.set('test_key', 'test_value', ex=60)
        test_value = redis_client.get('test_key')

        if test_value == 'test_value':
            logger.info("✅ Redis connection validated")
        else:
            logger.error("❌ Redis validation failed")

        # Health check
        health = db_manager.health_check()
        logger.info(f"🏥 Health check results: {health}")

        return all(health.values())

    except Exception as e:
        logger.error(f"❌ Database validation failed: {e}")
        return False

def drop_all_tables():
    """Drop all tables (use with caution!)"""
    try:
        db_manager = DatabaseManager()
        db_manager.initialize_postgresql()

        logger.warning("⚠️  Dropping all database tables...")
        Base.metadata.drop_all(db_manager.engine)
        logger.info("✅ All tables dropped successfully")

    except Exception as e:
        logger.error(f"❌ Failed to drop tables: {e}")
        raise

def main():
    """Main function for database operations"""
    import argparse

    parser = argparse.ArgumentParser(description='Database management for Carnatic Music Learning Platform')
    parser.add_argument('action', choices=['init', 'seed', 'validate', 'drop', 'reset'],
                       help='Database action to perform')
    parser.add_argument('--force', action='store_true',
                       help='Force operation without confirmation')

    args = parser.parse_args()

    if args.action == 'init':
        logger.info("🚀 Initializing database...")
        if initialize_database():
            logger.info("✅ Database initialization completed!")
        else:
            logger.error("❌ Database initialization failed!")
            sys.exit(1)

    elif args.action == 'seed':
        logger.info("🌱 Creating sample data...")
        create_sample_data()

    elif args.action == 'validate':
        logger.info("🔍 Validating database...")
        if validate_database():
            logger.info("✅ Database validation passed!")
        else:
            logger.error("❌ Database validation failed!")
            sys.exit(1)

    elif args.action == 'drop':
        if not args.force:
            confirmation = input("⚠️  Are you sure you want to drop all tables? (yes/no): ")
            if confirmation.lower() != 'yes':
                logger.info("Operation cancelled")
                return
        drop_all_tables()

    elif args.action == 'reset':
        if not args.force:
            confirmation = input("⚠️  Are you sure you want to reset the database? (yes/no): ")
            if confirmation.lower() != 'yes':
                logger.info("Operation cancelled")
                return

        logger.info("🔄 Resetting database...")
        drop_all_tables()
        if initialize_database():
            create_sample_data()
            logger.info("✅ Database reset completed!")
        else:
            logger.error("❌ Database reset failed!")
            sys.exit(1)

if __name__ == "__main__":
    main()