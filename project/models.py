from project.views import db
from datetime import datetime


# user_role table
class UserRole(db.Model):
    __tablename__ = 'userrole'
    id = db.Column(db.Integer, primary_key=True)
    roleid = db.Column(db.Integer, unique=True)
    rolename = db.Column(db.String(50))

    def __init__(self, roleid, rolename):
        self.roleid = roleid
        self.rolename = rolename

    def __repr__(self):
        return '<User_Role %s>' % self.name


# users table
class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, index=True)
    firstname = db.Column(db.String(120), default='')
    lastname = db.Column(db.String(120), default='')
    email = db.Column(db.String(120), default='')
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.ForeignKey(UserRole.roleid), nullable=False)
    amino_editor = db.Column(db.Integer, default=-1)
    design_editor = db.Column(db.Integer, default=-1)
    recipe_editor = db.Column(db.Integer, default=-1)
    created_recipes = db.Column(db.Text, default='')
    last_login = db.Column(db.TIMESTAMP, default=datetime.utcnow())
    last_request = db.Column(db.TIMESTAMP, default=datetime.utcnow())
    computer_name = db.Column(db.String(255), default='')

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return '<User %s>' % self.username


# amino acids table
class AminoAcids(db.Model):
    __tablename__ = 'aminoacids'

    id = db.Column(db.Integer, primary_key=True)
    eid = db.Column(db.ForeignKey(Users.id))
    aminoacid = db.Column(db.String(120))
    short = db.Column(db.String(50))
    abbre = db.Column(db.String(120))
    formula = db.Column(db.String(120))
    mon_mass = db.Column(db.Float)
    avg_mass = db.Column(db.Float)
    protgrp = db.Column(db.Float)
    alphabet = db.Column(db.String(50))
    description = db.Column(db.Text)
    notes = db.Column(db.Text)
    active = db.Column(db.Integer, default=1)

    eid_t = db.Column(db.ForeignKey(Users.id))
    aminoacid_t = db.Column(db.String(120))
    short_t = db.Column(db.String(50))
    abbre_t = db.Column(db.String(120))
    formula_t = db.Column(db.String(120))
    mon_mass_t = db.Column(db.Float)
    avg_mass_t = db.Column(db.Float)
    protgrp_t = db.Column(db.Float)
    alphabet_t = db.Column(db.String(50))
    description_t = db.Column(db.Text)
    notes_t = db.Column(db.Text)
    active_t = db.Column(db.Integer, default=1)

    eid_mark_change = db.Column(db.Integer, default=0)
    aminoacid_mark_change = db.Column(db.Integer, default=0)
    short_mark_change = db.Column(db.Integer, default=0)
    abbre_mark_change = db.Column(db.Integer, default=0)
    formula_mark_change = db.Column(db.Integer, default=0)
    mon_mass_mark_change = db.Column(db.Integer, default=0)
    avg_mass_mark_change = db.Column(db.Integer, default=0)
    protgrp_mark_change = db.Column(db.Integer, default=0)
    alphabet_mark_change = db.Column(db.Integer, default=0)
    description_mark_change = db.Column(db.Integer, default=0)
    notes_mark_change = db.Column(db.Integer, default=0)
    active_mark_change = db.Column(db.Integer, default=0)

    def __repr__(self):
        return '<AminoAcid %s>' % self.aminoacid


# block types table
class BlockTypes(db.Model):
    __tablename__ = 'blocktypes'
    id = db.Column(db.Integer, primary_key=True, unique=True, default=0)
    name = db.Column(db.String(120))

    def __repr__(self):
        return '<BlockType %s>' % self.name


# designs table
class Designs(db.Model):
    __tablename__ = 'designs'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    protocol = db.Column(db.String(50), default='')
    supplier = db.Column(db.String(120), default='HealthTell, Inc.')
    block_type = db.Column(db.ForeignKey(BlockTypes.id))
    x_origin = db.Column(db.Integer, default=0)
    y_origin = db.Column(db.Integer, default=0)
    feature_diameter = db.Column(db.Float, default=0)
    x_features = db.Column(db.Integer, default=0)
    x_spacing = db.Column(db.Float, default=0)
    y_features = db.Column(db.Integer, default=0)
    y_spacing = db.Column(db.Float, default=0)
    active = db.Column(db.Integer, default=1)
    mask_num = db.Column(db.Integer, default=0)  # highest mask num
    feature_num = db.Column(db.Integer, default=0)  # highest row num
    date = db.Column(db.TIMESTAMP, default=datetime.utcnow())
    is_maldi = db.Column(db.Integer, default=0)


# designdetaillabel table
class DesignDetailsLabels(db.Model):
    __tablename__ = 'designdetailslabels'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    label_num = db.Column(db.Integer, default=0)
    label = db.Column(db.Text, default='')


# design detail table
class DesignDetails(db.Model):
    __tablename__ = 'designdetails'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    design_id = db.Column(db.ForeignKey(Designs.id), nullable=False)
    label_id = db.Column(db.ForeignKey(DesignDetailsLabels.id), nullable=True)
    col = db.Column(db.Integer, default=0)
    row = db.Column(db.Integer, default=0)
    feature = db.Column(db.Integer, default=0)
    mask = db.Column(db.Text, default='')


# recipe header table
class RecipeHeaders(db.Model):
    __tablename__ = 'recipe_headers'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    design_id = db.Column(db.ForeignKey(Designs.id), nullable=False)
    userid = db.Column(db.ForeignKey(Users.id))
    name = db.Column(db.String(120), default='')
    date = db.Column(db.TIMESTAMP, default=datetime.utcnow())
    notes = db.Column(db.Text)
    mask_list = db.Column(db.Text)
    active = db.Column(db.Integer, default=1)


# recipe detail table
class RecipeDetails(db.Model):
    __tablename__ = 'recipe_details'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    recipe_id = db.Column(db.ForeignKey(RecipeHeaders.id), nullable=False)
    col = db.Column(db.Integer, default=0)
    row = db.Column(db.Integer, default=0)
    feature = db.Column(db.Integer, default=0)
    name = db.Column(db.Text, default='')


# maldi recipe header table
class MaldiRecipeHeaders(db.Model):
    __tablename__ = 'maldi_recipe_headers'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    design_id = db.Column(db.ForeignKey(Designs.id), nullable=False)
    userid = db.Column(db.ForeignKey(Users.id))
    name = db.Column(db.String(120), default='')

    protection = db.Column(db.Integer, default=0)
    spacer = db.Column(db.Integer, default=0)
    standard = db.Column(db.Integer, default=0)

    protocol = db.Column(db.String(50), default='')
    supplier = db.Column(db.String(120), default='HealthTell, Inc.')
    block_type = db.Column(db.ForeignKey(BlockTypes.id))
    x_origin = db.Column(db.Integer, default=0)
    y_origin = db.Column(db.Integer, default=0)
    feature_diameter = db.Column(db.Float, default=0)
    x_features = db.Column(db.Integer, default=0)
    x_spacing = db.Column(db.Float, default=0)
    y_features = db.Column(db.Integer, default=0)
    y_spacing = db.Column(db.Float, default=0)

    date = db.Column(db.TIMESTAMP, default=datetime.utcnow())
    notes = db.Column(db.Text)
    mask_list = db.Column(db.Text)
    active = db.Column(db.Integer, default=1)


# maldi recipe detail table
class MaldiRecipeDetails(db.Model):
    __tablename__ = 'maldi_recipe_details'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    recipe_id = db.Column(db.ForeignKey(MaldiRecipeHeaders.id), nullable=False)
    col = db.Column(db.Integer, default=0)
    row = db.Column(db.Integer, default=0)
    name = db.Column(db.Integer, default=0)
    iid = db.Column(db.Integer, default=0)
    var_x = db.Column(db.Float, default=0)
    var_y = db.Column(db.Float, default=0)
    var_z = db.Column(db.Float, default=0)
    var_multi_csv = db.Column(db.Text)
    var_x_key = db.Column(db.Text)
    var_y_key = db.Column(db.Text)
    var_z_key = db.Column(db.Text)
    var_multi_csv_keys = db.Column(db.Text)
    sequence = db.Column(db.Text)


# logs table
class Logs(db.Model):
    __tablename__ = 'activity_logs'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    eid = db.Column(db.ForeignKey(Users.id), nullable=False)
    computer_name = db.Column(db.String(120))
    activity = db.Column(db.Text)
    date = db.Column(db.TIMESTAMP, default=datetime.utcnow())


# tasks table
class Tasks(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    status = db.Column(db.String(120), default='')
    info = db.Column(db.Text, default='{}')
