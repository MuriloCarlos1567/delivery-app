from flask_migrate import upgrade
from models import Role

def manage_database():
    upgrade()
    Role.insert_roles()
