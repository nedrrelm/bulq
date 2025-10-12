"""Reset database schema to match current models.

WARNING: This will DROP all existing tables and recreate them.
"""

from app.database import engine
from app.models import Base


def reset_database():
    print('WARNING: This will drop all existing tables!')
    response = input('Are you sure you want to continue? (yes/no): ')

    if response.lower() != 'yes':
        print('Aborted.')
        return

    print('Dropping all tables...')
    Base.metadata.drop_all(bind=engine)

    print('Creating all tables...')
    Base.metadata.create_all(bind=engine)

    print('✓ Database reset complete!')


if __name__ == '__main__':
    reset_database()
