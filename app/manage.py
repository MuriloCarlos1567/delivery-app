from flask_migrate import upgrade
from .models import Role

def manage_database():
    if Role.query.filter_by(id=1).first():
        upgrade()
        Role.insert_roles()
    else:
        print('Alredy up')
