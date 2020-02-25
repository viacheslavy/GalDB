from project.models import UserRole, Users, BlockTypes, AminoAcids, Tasks
from project.views import db
from sqlalchemy import func
import hashlib
import threading
import time


# background thread
class Threading(object):
    def __init__(self, interval=1):
        self.interval = interval
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):
        print("thread started");
        while True:
            time.sleep(self.interval)
        print("thread ended");


def start_service():
    Threading(60)


# initialize database
def init_db():
    print("init_db started")

    Tasks.query.delete()
    db.session.commit()

    user_role = UserRole.query.filter_by(roleid=1, rolename='User').first()
    if user_role is None:
        user_role = UserRole(1, 'User')
        db.session.add(user_role)
        db.session.commit()

    user_role = UserRole.query.filter_by(roleid=2, rolename='Admin').first()
    if user_role is None:
        user_role = UserRole(2, 'Admin')
        db.session.add(user_role)
        db.session.commit()

    # This user is super admin
    user = Users.query.filter(func.lower(Users.username) == 'designdb').first()
    if user is None:
        username = "designdb"
        password = "hotinarizona0518"
        password = hashlib.md5(password.encode("utf8")).hexdigest()
        user = Users()
        user.username = username
        user.role = 2
        user.password = password
        user.email = "designdb@healthtell.io"
        db.session.add(user)
        db.session.commit()

    # Initialize BlockTypes table
    blocktype = BlockTypes.query.filter(BlockTypes.id == 0).first()
    if blocktype is None:
        blocktype = BlockTypes()
        blocktype.id = 0
        blocktype.name = 'Rectangular'
        db.session.add(blocktype)
        db.session.commit()

    blocktype = BlockTypes.query.filter(BlockTypes.id == 1).first()
    if blocktype is None:
        blocktype = BlockTypes()
        blocktype.id = 1
        blocktype.name = 'Hexagonal'
        db.session.add(blocktype)
        db.session.commit()

    # Make all admin users permission to be allowed.
    admin_users = Users.query.filter(Users.role == 2).all()
    if admin_users is not None:
        for admin_user in admin_users:
            admin_user.amino_editor = -1
            admin_user.design_editor = -1
            admin_user.recipe_editor = -1
        db.session.commit()

    print("init_db ended")


