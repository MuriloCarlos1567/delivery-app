from flask_migrate import upgrade
from .models import Role

def manage_database():
    try:
        if Role.query.filter_by(id=1).first():
            print('Alredy up')
    except:
        upgrade()
        Role.insert_roles()
        print('Updating')
