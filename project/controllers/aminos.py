#!/usr/bin/env python
from flask import render_template, request, json
from project.views import app, login_required, g
from project.models import *
from sqlalchemy import exc, func, or_
from project.classes import customfunc


@app.route("/aminos", methods=['GET'])
@login_required
def aminos():
    do_update_aminoacids()
    users = Users.query.filter(Users.amino_editor == -1).order_by(Users.username).all()
    return render_template('aminos.html', menu="aminos", users=users)


# add amino acid
@app.route("/add_amino_acid", methods=['POST'])
@login_required
def add_amino_acid():
    result = {'result': 'ERROR', 'msg': '', 'id': ''}

    if g.user.amino_editor == 0:
        result['msg'] = 'Permission denied.'
        return json.dumps(result)

    amino = request.form['amino']
    short = request.form['short']
    abbre = request.form['abbre']
    formula = request.form['formula']
    mon_mass = request.form['mon_mass']
    avg_mass = request.form['avg_mass']
    protgrp = request.form['protgrp']
    notes = request.form['notes']
    editor = request.form['editor']

    aminoacid = AminoAcids.query.filter(func.lower(AminoAcids.aminoacid) == func.lower(amino)).first()
    if aminoacid is not None:
        result['msg'] = 'Duplicate: The Amino Acid already exist'
        return json.dumps(result)

    aminoacid = AminoAcids()
    aminoacid.aminoacid = amino
    aminoacid.aminoacid_t = amino

    aminoacid.short = short
    aminoacid.short_t = short

    aminoacid.abbre = abbre
    aminoacid.abbre_t = abbre

    aminoacid.formula = formula
    aminoacid.formula_t = formula

    aminoacid.mon_mass = mon_mass
    aminoacid.mon_mass_t = mon_mass

    aminoacid.avg_mass = avg_mass
    aminoacid.avg_mass_t = avg_mass

    aminoacid.protgrp = protgrp
    aminoacid.protgrp_t = protgrp

    aminoacid.notes = notes
    aminoacid.notes_t = notes

    aminoacid.eid = int(editor)
    aminoacid.eid_t = int(editor)

    try:
        db.session.add(aminoacid)
        db.session.commit()
        result['id'] = aminoacid.id
        result['result'] = 'SUCCESS'
        customfunc.add_activity(g.user.id, 'Added new amino acid("' + aminoacid.aminoacid + '")')
    except Exception as e:
        print("add new amino error:", e)
        result['msg'] = str(e)

    return json.dumps(result)


# delete amino acids
@app.route("/delete_amino_acids", methods=['POST'])
@login_required
def delete_amino_acids():
    result = {'result': 'ERROR', 'msg': ''}
    ids = request.form['ids']
    ids_array = ids.split(",")
    try:
        aminos = AminoAcids.query.filter(AminoAcids.id.in_(ids_array)).all()
        print(aminos)
        db.session.commit()
        result['result'] = 'SUCCESS'
    except exc.SQLAlchemyError as e:
        result['msg'] = 'Operation Failed.'
        print("Delete Amino error:", e)

    return json.dumps(result)


# edit amino acids table
@app.route("/aminos_edit", methods=['POST'])
@login_required
def aminos_edit():
    result = {'result': 'ERROR', 'data': [], 'field_name': ''}

    for key in request.form.keys():
        if key.startswith('data'):
            pos1 = [i for i, ltr in enumerate(key) if ltr == '[']
            pos2 = [i for i, ltr in enumerate(key) if ltr == ']']

            id = key[pos1[0]+1:pos2[0]]
            columnname = key[pos1[1] + 1:pos2[1]]
            columnvalue = request.form.getlist(key)

            amino = AminoAcids.query.filter_by(id=id).first()
            if amino is None:
                return json.dumps(result)

            if g.user.amino_editor == 0:
                tmp = {'name': columnname, 'status': 'Permission denied.'}
                result2 = {'fieldErrors': []}
                result2['fieldErrors'].append(tmp)
                return json.dumps(result2)

            if columnname == "aminoacid":
                amino.aminoacid = columnvalue[0]
                amino.aminoacid_mark_change = 1
                db.session.commit()

            if columnname == "short":
                amino.short = columnvalue[0]
                amino.short_mark_change = 1
                db.session.commit()

            if columnname == "abbre":
                amino.abbre = columnvalue[0]
                amino.abbre_mark_change = 1
                db.session.commit()

            if columnname == "formula":
                amino.formula = columnvalue[0]
                amino.formula_mark_change = 1
                db.session.commit()

            if columnname == "monmass":
                amino.mon_mass_mark_change = 1
                if len(columnvalue[0]) == 0:
                    amino.mon_mass = None
                else:
                    amino.mon_mass = columnvalue[0]
                db.session.commit()

            if columnname == "avgmass":
                amino.avg_mass_mark_change = 1
                if len(columnvalue[0]) == 0:
                    amino.avg_mass = None
                else:
                    amino.avg_mass = columnvalue[0]
                db.session.commit()

            if columnname == "protgrp":
                amino.protgrp_mark_change = 1
                if len(columnvalue[0]) == 0:
                    amino.protgrp = None
                else:
                    amino.protgrp = columnvalue[0]
                db.session.commit()

            if columnname == "active_text":
                amino.active_mark_change = 1
                amino.active = columnvalue[0]
                db.session.commit()

            if columnname == "eid_text":
                amino.eid_mark_change = 1
                if columnvalue[0] == '0':
                    amino.eid = None
                else:
                    amino.eid = columnvalue[0]
                db.session.commit()

            if columnname == "notes":
                amino.notes_mark_change = 1
                amino.notes = columnvalue[0]
                db.session.commit()

            active_text = "No"
            if amino.active == 1:
                active_text = "Yes"
            elif amino.active is None:
                amino.active = 0
                db.session.commit()

            amino = db.session.query(AminoAcids.id, AminoAcids.eid, Users.username, AminoAcids.active, AminoAcids.aminoacid, AminoAcids.short, AminoAcids.abbre, AminoAcids.formula, AminoAcids.mon_mass, AminoAcids.avg_mass, AminoAcids.protgrp, AminoAcids.notes).outerjoin(Users, Users.id == AminoAcids.eid).filter(AminoAcids.id == id).order_by(AminoAcids.aminoacid).first()
            if amino is not None:
                json_obj = {
                    "id": amino.id,
                    "eid": amino.eid,
                    "eid_text": amino.username,
                    "aminoacid": amino.aminoacid,
                    "short": amino.short,
                    "abbre": amino.abbre,
                    "formula": amino.formula,
                    "monmass": amino.mon_mass,
                    "avgmass": amino.avg_mass,
                    "protgrp": amino.protgrp,
                    "active": amino.active,
                    "active_text": active_text,
                    "notes": amino.notes

                }
                result['data'].append(json_obj)

    return json.dumps(result)


def do_update_aminoacids():
    aminos = AminoAcids.query.filter(
                                     or_(AminoAcids.aminoacid_mark_change == 1,
                                         AminoAcids.short_mark_change == 1,
                                         AminoAcids.abbre_mark_change == 1,
                                         AminoAcids.formula_mark_change == 1,
                                         AminoAcids.mon_mass_mark_change == 1,
                                         AminoAcids.avg_mass_mark_change == 1,
                                         AminoAcids.protgrp_mark_change == 1,
                                         AminoAcids.eid_mark_change == 1,
                                         AminoAcids.notes_mark_change == 1)).all()
    if aminos is not None:
        for amino in aminos:
            if amino.aminoacid_mark_change == 1:
                amino.aminoacid_t = amino.aminoacid
                amino.aminoacid_mark_change = 0

            if amino.short_mark_change == 1:
                amino.short_t = amino.short
                amino.short_mark_change = 0

            if amino.abbre_mark_change == 1:
                amino.abbre_t = amino.abbre
                amino.abbre_mark_change = 0
                customfunc.add_activity(g.user.id, 'Changed abbre of Amino("' + amino.aminoacid + '") to "' + amino.abbre + '"')

            if amino.formula_mark_change == 1:
                amino.formula_t = amino.formula
                amino.formula_mark_change = 0

            if amino.mon_mass_mark_change == 1:
                amino.mon_mass_t = amino.mon_mass
                amino.mon_mass_mark_change = 0
                customfunc.add_activity(g.user.id, 'Changed mon mass of Amino("' + amino.aminoacid + '") to "' + str(amino.mon_mass) + '"')

            if amino.avg_mass_mark_change == 1:
                amino.avg_mass_t = amino.avg_mass
                amino.avg_mass_mark_change = 0

            if amino.protgrp_mark_change == 1:
                amino.protgrp_t = amino.protgrp
                amino.protgrp_mark_change = 0
                customfunc.add_activity(g.user.id, 'Changed protect group of Amino("' + amino.aminoacid + '") to "' + str(amino.protgrp) + '"')

            if amino.active_mark_change == 1:
                amino.active_t = amino.active
                amino.active_mark_change = 0

            if amino.eid_mark_change == 1:
                amino.eid_t = amino.eid
                amino.eid_mark_change = 0
                username_tmp = 'None'
                user = Users.query.filter(Users.id == amino.eid).first()
                if user is not None:
                    username_tmp = '"' + user.username + '"'
                customfunc.add_activity(g.user.id, 'Changed Editor of Amino("' + amino.aminoacid + '") to ' + username_tmp)

            if amino.notes_mark_change == 1:
                amino.notes_t = amino.notes
                amino.notes_mark_change = 0
                notes_tmp = 'Empty'
                if amino.notes is not None and len(amino.notes) > 0:
                    if len(amino.notes) > 20:
                        notes_tmp = '"' + amino.notes[:20] + '..."'
                    else:
                        notes_tmp = '"' + amino.notes + '"'
                customfunc.add_activity(g.user.id, 'Changed Notes of Amino("' + amino.aminoacid + '") to ' + notes_tmp)

            db.session.commit()

    return True


# Update amino acids
@app.route("/update_aminoacids", methods=['POST'])
@login_required
def update_aminoacids():
    result = {'result': 'SUCCESS'}
    if g.user.amino_editor == -1:
        do_update_aminoacids()
    return json.dumps(result)


# Cancel amino acids
@app.route("/cancel_aminoacids", methods=['POST'])
@login_required
def cancel_aminoacids():
    result = {'result': 'SUCCESS'}
    if g.user.amino_editor == 0:
        return json.dumps(result)

    aminos = AminoAcids.query.filter(
                                     or_(AminoAcids.aminoacid_mark_change == 1,
                                         AminoAcids.short_mark_change == 1,
                                         AminoAcids.abbre_mark_change == 1,
                                         AminoAcids.formula_mark_change == 1,
                                         AminoAcids.mon_mass_mark_change == 1,
                                         AminoAcids.avg_mass_mark_change == 1,
                                         AminoAcids.protgrp_mark_change == 1,
                                         AminoAcids.active_mark_change == 1,
                                         AminoAcids.eid_mark_change == 1,
                                         AminoAcids.notes_mark_change == 1)).all()
    if aminos is not None:
        for amino in aminos:
            if amino.aminoacid_mark_change == 1:
                amino.aminoacid = amino.aminoacid_t
                amino.aminoacid_mark_change = 0

            if amino.short_mark_change == 1:
                amino.short_t = amino.short
                amino.short_mark_change = 0

            if amino.abbre_mark_change == 1:
                amino.abbre = amino.abbre_t
                amino.abbre_mark_change = 0

            if amino.formula_mark_change == 1:
                amino.formula = amino.formula_t
                amino.formula_mark_change = 0

            if amino.mon_mass_mark_change == 1:
                amino.mon_mass = amino.mon_mass_t
                amino.mon_mass_mark_change = 0

            if amino.avg_mass_mark_change == 1:
                amino.avg_mass = amino.avg_mass_t
                amino.avg_mass_mark_change = 0

            if amino.protgrp_mark_change == 1:
                amino.protgrp = amino.protgrp_t
                amino.protgrp_mark_change = 0

            if amino.active_mark_change == 1:
                amino.active = amino.active_t
                amino.active_mark_change = 0

            if amino.eid_mark_change == 1:
                amino.eid = amino.eid_t
                amino.eid_mark_change = 0

            if amino.notes_mark_change == 1:
                amino.notes = amino.notes_t
                amino.notes_mark_change = 0

            db.session.commit()
    return json.dumps(result)


# get amino acid list
@app.route("/get_amino_acids", methods=['POST'])
@login_required
def get_amino_acids():
    result = {'result': 'ERROR', 'msg': '', 'data': []}

    aminos = db.session.query(AminoAcids.id, AminoAcids.eid, Users.username, AminoAcids.active, AminoAcids.aminoacid, AminoAcids.short, AminoAcids.abbre, AminoAcids.formula, AminoAcids.mon_mass, AminoAcids.avg_mass, AminoAcids.protgrp, AminoAcids.notes).outerjoin(Users, Users.id == AminoAcids.eid).order_by(AminoAcids.aminoacid).all()

    if aminos is not None:
        result['result'] = 'SUCCESS'
        for amino in aminos:
            active = amino.active
            if active is None:
                active = 0

            active_text = "No"
            if active == 1:
                active_text = "Yes"

            json_obj = {
                "id": amino.id,
                "eid": amino.eid,
                "eid_text": amino.username,
                "aminoacid": amino.aminoacid,
                "short": amino.short,
                "abbre": amino.abbre,
                "formula": amino.formula,
                "monmass": amino.mon_mass,
                "avgmass": amino.avg_mass,
                "protgrp": amino.protgrp,
                "active": active,
                "active_text": active_text,
                "notes": amino.notes

            }
            result['data'].append(json_obj)

    return json.dumps(result)
