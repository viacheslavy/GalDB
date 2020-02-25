#!/usr/bin/env python
from flask import render_template, request, json, session, Response, url_for
from project.models import *
from project.views import app, login_required, g
from project.classes import customfunc
from project.controllers.asynctask import new_task
from werkzeug.datastructures import Headers
from time import sleep

import mimetypes
import xlsxwriter
import io
import threading


# recipe template
@app.route("/recipe", methods=['GET'])
@login_required
def recipe():
    tmp_designs = db.session.query(Designs.id, Designs.protocol, Designs.active, Designs.is_maldi).order_by(Designs.protocol).all()

    labels = []
    tmp_labels = db.session.query(DesignDetailsLabels.id, DesignDetailsLabels.label, DesignDetailsLabels.label_num).all()
    for tmp in tmp_labels:
        json_obj = {
            'id': tmp.id,
            'label': tmp.label,
            'label_num': tmp.label_num
        }
        labels.append(json_obj)

    designs = []
    for tmp in tmp_designs:
        if tmp.is_maldi != 1:

            designdetailslabels = db.session.query(DesignDetails.label_id).group_by(DesignDetails.label_id).filter(DesignDetails.design_id == tmp.id).order_by(DesignDetails.label_id.asc()).all()
            label_ids = ''
            for designdetailslabel in designdetailslabels:
                if label_ids == '':
                    label_ids = str(designdetailslabel.label_id)
                else:
                    label_ids = label_ids + "," + str(designdetailslabel.label_id)

            json_obj = {
                'id': tmp.id,
                'protocol': tmp.protocol,
                'mask_num': 0,
                'label_ids': label_ids,
                'active': tmp.active
            }
            designs.append(json_obj)

    blocktypes = BlockTypes.query.all()
    aminos = AminoAcids.query.filter(AminoAcids.active == 1).order_by(AminoAcids.abbre.asc()).all()
    current_recipe_id = 0
    if 'current_recipe_id' in session:
        current_recipe_id = int(session['current_recipe_id'])

    users = Users.query.filter(Users.amino_editor == -1).order_by(Users.username).all()
    return render_template('recipe.html', menu="recipe", designs=designs, blocktypes=blocktypes, aminos=aminos, current_recipe_id=current_recipe_id, users=users, designdetailslabels=labels)


# recipe template
@app.route("/recipe_recipe_print", methods=['GET'])
@login_required
def recipe_recipe_print():
    recipe_id = request.args.get('recipe_id', '')
    recipe_header = RecipeHeaders.query.filter(RecipeHeaders.id == recipe_id).first()
    if recipe_header is None:
        return "Recipe does not exist."

    design = Designs.query.filter(Designs.id == recipe_header.design_id).first()
    if design is None:
        return "Design does not exist."

    design_details = DesignDetails.query.filter(DesignDetails.design_id == design.id).order_by(DesignDetails.col, DesignDetails.row, DesignDetails.feature).all()
    if design_details is None:
        return "Design Detail does not exist."

    first_mask_num = 0
    try:
        mask_list = recipe_header.mask_list
        mask_array = mask_list.split(":")
        first_mask_num = int(mask_array[0].split(",")[0])
    except Exception as e:
        return e

    return render_template('recipe_recipe_print.html', mask_array=mask_array, design_details=design_details, recipe_header=recipe_header, first_mask_num=first_mask_num)


# recipe template
@app.route("/recipe_gal_print", methods=['GET'])
@login_required
def recipe_gal_print():
    recipe_id = request.args.get('recipe_id', '')
    recipe_header = RecipeHeaders.query.filter(RecipeHeaders.id == recipe_id).first()
    if recipe_header is None:
        return "Recipe does not exist."

    recipe_details = RecipeDetails.query.filter(RecipeDetails.recipe_id == recipe_id).order_by(RecipeDetails.row, RecipeDetails.col, RecipeDetails.name).all()
    if recipe_details is None:
        return "Recipe Detail does not exist."

    return render_template('recipe_gal_print.html', recipe_header=recipe_header, recipe_details=recipe_details)


# get recipes
@app.route("/get_recipe", methods=['POST'])
@login_required
def get_recipe():
    result = {'result': 'ERROR', 'msg': 'Operation failed.', 'data': {}}
    recipe_id = request.form['recipe_id']
    recipe_header = RecipeHeaders.query.filter(RecipeHeaders.id == recipe_id).first()
    if recipe_header is not None:
        result['result'] = 'SUCCESS'
        result['msg'] = ''

        session['current_recipe_id'] = recipe_id

        result['data']['name'] = recipe_header.name
        result['data']['design_id'] = recipe_header.design_id
        result['data']['protocol'] = recipe_header.protocol
        result['data']['supplier'] = recipe_header.supplier
        result['data']['block_type'] = recipe_header.block_type
        result['data']['x_origin'] = recipe_header.x_origin
        result['data']['y_origin'] = recipe_header.y_origin
        result['data']['feature_diameter'] = recipe_header.feature_diameter
        result['data']['x_features'] = recipe_header.x_features
        result['data']['x_spacing'] = recipe_header.x_spacing
        result['data']['y_features'] = recipe_header.y_features
        result['data']['y_spacing'] = recipe_header.y_spacing
        result['data']['mask_list'] = recipe_header.mask_list
        result['data']['mask_num'] = 24
        design = Designs.query.filter(Designs.id == recipe_header.design_id).first()
        if design is not None:
            result['data']['mask_num'] = design.mask_num
    return json.dumps(result)


# get gal header
@app.route("/get_gal_header", methods=['POST'])
@login_required
def get_gal_header():
    result = {'result': 'ERROR', 'msg': 'Operation failed.', 'data': ''}
    recipe_name = request.form['recipe_name']
    designid = request.form['design_id']

    design = Designs.query.filter(Designs.id == designid).first()

    if design is not None:
        result['result'] = 'SUCCESS'
        tmp_result = 'ATF\t1.0\n'
        tmp_result += '8\t5\n'
        tmp_result += '"Type=GenePix ArrayList V1.0"\n'
        tmp_result += '"BlockCount=1"\n'
        tmp_result += '"BlockType=' + str(design.block_type) + '"\n'
        tmp_result += '"Protocol=' + design.protocol + '"\n'
        tmp_result += '"Version=' + recipe_name + '"\n'
        tmp_result += '"Supplier=' + design.supplier + '"\n'

        x_origin = design.x_origin
        if int(design.x_origin) == design.x_origin:
            x_origin = int(design.x_origin)

        y_origin = design.y_origin
        if int(design.y_origin) == design.y_origin:
            y_origin = int(design.y_origin)

        feature_diameter = design.feature_diameter
        if int(design.feature_diameter) == design.feature_diameter:
            feature_diameter = int(design.feature_diameter)

        x_features = design.x_features
        if int(design.x_features) == design.x_features:
            x_features = int(design.x_features)

        x_spacing = design.x_spacing
        if int(design.x_spacing) == design.x_spacing:
            x_spacing = int(design.x_spacing)

        y_features = design.y_features
        if int(design.y_features) == design.y_features:
            y_features = int(design.y_features)

        y_spacing = design.y_spacing
        if int(design.y_spacing) == design.y_spacing:
            y_spacing = int(design.y_spacing)

        tmp_result += '"Block1= ' + str(x_origin) + ', ' + str(y_origin) + ', ' + str(feature_diameter) + ', ' + str(x_features) + ', ' + str(x_spacing) + ', ' + str(y_features) + ', ' + str(y_spacing) + '"\n'

        result['data'] = tmp_result
    return json.dumps(result)


# delete recipe
@app.route("/delete_recipe", methods=['POST'])
@login_required
def delete_recipe():
    result = {'result': 'ERROR', 'msg': 'Operation failed.'}
    recipe_id = request.form['recipe_id']

    if g.user.role != 2:
        tmp = ''
        if g.user.created_recipes is not None:
            tmp = g.user.created_recipes
        tmp_array = tmp.split(",")

        if recipe_id not in tmp_array:
            result['msg'] = 'Permission denied'
            return json.dumps(result)

    try:
        recipe_name = ''
        recipe = RecipeHeaders.query.filter(RecipeHeaders.id == recipe_id).first()
        recipe_name = recipe.name

        RecipeDetails.query.filter(RecipeDetails.recipe_id == recipe_id).delete()
        RecipeHeaders.query.filter(RecipeHeaders.id == recipe_id).delete()
        db.session.commit()

        session.pop("current_recipe_id", None)
        result['result'] = 'SUCCESS'
        result['msg'] = ''
        customfunc.add_activity(g.user.id, 'Deleted Recipe(' + recipe_name + ')')
    except Exception as e:
        print("delete recipe error:", e)
    return json.dumps(result)


# get recipes
@app.route("/get_recipes", methods=['POST'])
@login_required
def get_recipes():
    result = {'result': 'ERROR', 'msg': 'Operation failed.', 'data': []}
    recipes = db.session.query(RecipeHeaders.id, RecipeHeaders.name, RecipeHeaders.notes, RecipeHeaders.design_id, RecipeHeaders.date, RecipeHeaders.userid, RecipeHeaders.mask_list, Designs.protocol, Designs.mask_num, RecipeHeaders.active).outerjoin(Designs, Designs.id == RecipeHeaders.design_id).order_by(RecipeHeaders.date.desc(),RecipeHeaders.name.asc(), ).all()
    if recipes is not None:
        result['result'] = 'SUCCESS'
        result['msg'] = ''
        for recipe in recipes:
            json_obj = {
                'id': recipe.id,
                'userid': recipe.userid,
                'name': recipe.name,
                'date': recipe.date,
                "design": recipe.design_id,
                "notes": recipe.notes,
                "design_text": recipe.protocol,
                "mask_list": recipe.mask_list,
                "mask_num": recipe.mask_num,
                "active": recipe.active
            }
            result['data'].append(json_obj)

    return json.dumps(result)


# get design data
@app.route("/get_design_data", methods=['POST'])
@login_required
def get_design_data():
    result = {'result': 'ERROR', 'msg': 'Operation failed.', 'data': {}}
    designid = request.form['designid']
    design = Designs.query.filter(Designs.id == designid).first()
    if design is not None:
        result['msg'] = ''
        result['result'] = 'SUCCESS'
        result['data']['protocol'] = design.protocol
        result['data']['supplier'] = design.supplier
        result['data']['block_type'] = design.block_type
        result['data']['x_origin'] = design.x_origin
        result['data']['y_origin'] = design.y_origin
        result['data']['feature_diameter'] = design.feature_diameter
        result['data']['x_features'] = design.x_features
        result['data']['x_spacing'] = design.x_spacing
        result['data']['y_features'] = design.y_features
        result['data']['y_spacing'] = design.y_spacing
        result['data']['mask_num'] = design.mask_num
    return json.dumps(result)


# add recipe
class AsyncAddRecipe(object):
    def __init__(self, task_id, params, user_id, hostname):
        self.task_id = task_id
        self.params = params
        self.user_id = user_id
        self.hostname = hostname

        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):
        result = {'result': 'ERROR', 'msg': 'Operation failed.'}

        _request_form = self.params
        designid = _request_form['designid']
        name = _request_form['recipe_name']
        notes = _request_form['notes']
        mask_list = _request_form['mask_list']
        active = _request_form['active']

        task = Tasks.query.filter(Tasks.id == self.task_id).first()
        if task is None:
            return False

        recipeheader = RecipeHeaders.query.filter(RecipeHeaders.name == name).first()
        if recipeheader is not None:
            task.status = "Stopped"
            task.info = 'Duplicate: The Name already exist.'
            db.session.commit()
            return False

        design = Designs.query.filter(Designs.id == designid).first()
        if design is None:
            task.status = "Stopped"
            task.info = 'The Design does not exist.'
            db.session.commit()
            return False

        design_details = db.session.query(DesignDetails.col, DesignDetails.row, DesignDetails.mask, DesignDetails.label_id).filter(DesignDetails.design_id == designid).order_by(DesignDetails.col, DesignDetails.row, DesignDetails.label_id).all()

        if design_details is None:
            task.status = "Stopped"
            task.info = 'The Design Detail does not exist.'
            db.session.commit()
            return False

        mask_list_array = mask_list.split(":")
        for value in mask_list_array:
            arg1 = value.split(",")
            if len(arg1) != 2:
                task.status = "Stopped"
                task.info = "Masks are not correct."
                db.session.commit()
                return False

        try:
            recipeheader = RecipeHeaders()
            recipeheader.name = name
            recipeheader.design_id = designid
            recipeheader.userid = self.user_id
            recipeheader.notes = notes
            recipeheader.date = datetime.utcnow()
            recipeheader.mask_list = mask_list
            recipeheader.active = active

            db.session.add(recipeheader)
            db.session.commit()

            print("started adding rows in add_recipe")

            task.status = 'Processing'
            task.info = '0'
            db.session.commit()

            total_rows = len(design_details)
            processed_rows = 0

            col = 1
            row = 1
            tmp_design_details = []
            pre_design_col = 0
            pre_design_row = 0
            for design_detail in design_details:
                if processed_rows == 0:
                    pre_design_col = design_detail.col
                    pre_design_row = design_detail.row

                if design_detail.col != pre_design_col or design_detail.row != pre_design_row:
                    recipe_detail = RecipeDetails()
                    recipe_detail.recipe_id = recipeheader.id
                    recipe_detail.col = col
                    recipe_detail.row = row

                    name = ""
                    for mask_arg in mask_list_array:
                        tmp = mask_arg.split(",")
                        first_part = int(tmp[0])
                        label_id = int(first_part / 10000)
                        label_index = first_part % 10000
                        design_short = tmp[1]

                        for tmp_design_detail in tmp_design_details:
                            if tmp_design_detail.label_id == label_id:
                                design_mask_array = tmp_design_detail.mask.split(",")
                                tmp = ""
                                if len(design_mask_array) > label_index:
                                    tmp = design_mask_array[label_index]
                                if tmp == "1":
                                    name = name + design_short
                                break
                    recipe_detail.name = name
                    db.session.add(recipe_detail)

                    if row >= int(design.y_features):
                        col = col + 1
                        row = 1
                    else:
                        row = row + 1

                    tmp_design_details = []

                pre_design_col = design_detail.col
                pre_design_row = design_detail.row

                if processed_rows % 50000 == 0:
                    db.session.commit()

                if processed_rows % 100 == 0:
                    sleep(0.001)

                if processed_rows % 1000 == 0:
                    task.info = int(processed_rows * 100 / total_rows)
                    db.session.commit()

                processed_rows = processed_rows + 1
                tmp_design_details.append(design_detail)

            if len(tmp_design_details) > 0:
                recipe_detail = RecipeDetails()
                recipe_detail.recipe_id = recipeheader.id
                recipe_detail.col = col
                recipe_detail.row = row

                name = ""
                for mask_arg in mask_list_array:
                    tmp = mask_arg.split(",")
                    first_part = int(tmp[0])
                    label_id = int(first_part / 10000)
                    label_index = first_part % 10000
                    design_short = tmp[1]

                    for tmp_design_detail in tmp_design_details:
                        if tmp_design_detail.label_id == label_id:
                            design_mask_array = tmp_design_detail.mask.split(",")
                            tmp = ""
                            if len(design_mask_array) > label_index:
                                tmp = design_mask_array[label_index]
                            if tmp == "1":
                                name = name + design_short
                            break
                recipe_detail.name = name
                db.session.add(recipe_detail)

            task.status = 'Processing'
            task.info = '100'
            db.session.commit()

            print("ended adding rows in add_recipe")

            result['id'] = recipeheader.id
            result['date'] = recipeheader.date
            result['result'] = 'SUCCESS'
            result['msg'] = ''

            task.status = "Done"
            task.info = json.dumps(result)
            db.session.commit()

            current_user = Users.query.filter(Users.id == self.user_id).first()
            if current_user is not None:
                tmp = ''
                if current_user.created_recipes is not None:
                    tmp = current_user.created_recipes
                if tmp == '':
                    tmp = str(recipeheader.id)
                else:
                    tmp += ',' + str(recipeheader.id)
                current_user.created_recipes = tmp
                db.session.commit()

            customfunc.add_activity_hostname(self.user_id, 'Created Recipe(' + recipeheader.name + ')', self.hostname)
        except Exception as e:
            print("add recipe error:", e)
            task.status = "Stopped"
            task.info = str(e)
            db.session.commit()
        return False


# add recipe
@app.route("/add_recipe", methods=['POST'])
@login_required
def add_recipe():
    result = {'result': 'ERROR', 'msg': 'Operation failed.'}

    if g.user.recipe_editor == 0:
        result['msg'] = 'Permission denied'
        return json.dumps(result)

    ipaddress = customfunc.get_ip_address()
    hostname = ''
    try:
        hostname = customfunc.get_host_name_by_ip(ipaddress)
    except Exception as e:
        hostname = customfunc.get_ip_address()

    task_id = new_task()
    task_status_url = url_for('task_status', task_id=task_id)
    AsyncAddRecipe(task_id=task_id, params=request.form, user_id=g.user.id, hostname=hostname)

    result['result'] = 'SUCCESS'
    result['msg'] = ''
    result['task_status_url'] = task_status_url
    return json.dumps(result)


# update recipe
class AsyncUpdateRecipe(object):
    def __init__(self, task_id, params, user_id, hostname):
        self.task_id = task_id
        self.params = params
        self.user_id = user_id
        self.hostname = hostname

        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):
        result = {'result': 'ERROR', 'msg': 'Operation failed.'}

        _request_form = self.params
        recipeid = int(_request_form['recipeid'])
        changed_mask_build = _request_form['changed_mask_build']
        designid = _request_form['designid']
        design_text = _request_form['design_text']
        recipe_name = _request_form['recipe_name']
        notes = _request_form['notes']
        mask_list = _request_form['mask_list']
        active = _request_form['active']
        active_text = 'No'
        if active == '1':
            active_text = 'Yes'

        task = Tasks.query.filter(Tasks.id == self.task_id).first()
        if task is None:
            return False

        recipeheader = RecipeHeaders.query.filter(RecipeHeaders.name == recipe_name).first()
        if recipeheader is not None and recipeheader.id != recipeid:
            task.status = "Stopped"
            task.info = 'Duplicate: The Name already exist.'
            db.session.commit()
            return False

        recipeheader = RecipeHeaders.query.filter(RecipeHeaders.id == recipeid).first()
        if recipeheader is None:
            task.status = "Stopped"
            task.info = 'The Recipe does not exist.'
            db.session.commit()
            return False

        design = Designs.query.filter(Designs.id == designid).first()
        if design is None:
            task.status = "Stopped"
            task.info = 'The Design does not exist.'
            db.session.commit()
            return False

        design_details = db.session.query(DesignDetails.col, DesignDetails.row, DesignDetails.mask, DesignDetails.label_id).filter(DesignDetails.design_id == designid).order_by(DesignDetails.col, DesignDetails.row, DesignDetails.label_id).all()
        if design_details is None:
            task.status = "Stopped"
            task.info = 'The Design Detail does not exist.'
            db.session.commit()
            return False

        mask_list_array = mask_list.split(":")
        for value in mask_list_array:
            arg1 = value.split(",")
            if len(arg1) != 2:
                task.status = "Stopped"
                task.info = "Masks are not correct."
                db.session.commit()
                return False

        try:
            log_str = ""
            if recipeheader.name != recipe_name:
                log_str = "Recipe Name from(" + recipeheader.name + ") to (" + recipe_name + ")"

            if recipeheader.design_id != int(designid):
                if log_str == "":
                    log_str = "Design from(" + design.protocol + ") to (" + design_text + ") on Recipe(" + recipe_name + ")"
                else:
                    log_str = log_str + ", " + "Design from(" + design.protocol + ") to (" + design_text + ") on Recipe(" + recipe_name + ")"

            if recipeheader.notes != notes:
                pre_notes = '""'
                if recipeheader.notes is not None and len(recipeheader.notes) > 20:
                    pre_notes = '"' + recipeheader.notes[:20] + '..."'
                else:
                    pre_notes = '"' + recipeheader.notes + '"'

                cur_notes = '""'
                if len(notes) > 20:
                    cur_notes = '"' + notes[:20] + '..."'
                else:
                    cur_notes = '"' + notes + '"'

                if log_str == "":
                    log_str = 'Notes from (' + pre_notes + ') to (' + cur_notes + ') on Recipe(' + recipe_name + ')'
                else:
                    log_str = log_str + ", " + 'Notes from (' + pre_notes + ') to (' + cur_notes + ') on Recipe(' + recipe_name + ')'

            if recipeheader.active != int(active):
                pre_active = 'False'
                if recipeheader.active == 1:
                    pre_active = 'True'

                cur_active = 'False'
                if int(active) == 1:
                    cur_active = 'True'

                if log_str == "":
                    log_str = 'Active from (' + pre_active + ') to (' + cur_active + ') on Recipe(' + recipe_name + ')'
                else:
                    log_str = log_str + ", " + 'Active from (' + pre_active + ') to (' + cur_active + ') on Recipe(' + recipe_name + ')'

            if log_str != "":
                customfunc.add_activity_hostname(self.user_id, "Changed " + log_str, self.hostname)

            if recipeheader.mask_list != mask_list:
                pre_mask_array = []
                if recipeheader.mask_list is not None:
                    pre_mask_array = recipeheader.mask_list.split(":")
                cur_mask_array = mask_list.split(":")
                start = 0
                end = 0
                if len(pre_mask_array) > len(cur_mask_array):
                    start = 0
                    end = len(cur_mask_array)
                    for i in range(len(cur_mask_array) + 1, len(pre_mask_array) + 1):
                        customfunc.add_activity_hostname(self.user_id, 'Deleted ' + str(i) + 'nd Mask on Recipe(' + recipe_name + ')', self.hostname)
                elif len(cur_mask_array) > len(pre_mask_array):
                    for i in range(len(pre_mask_array) + 1, len(cur_mask_array) + 1):
                        customfunc.add_activity_hostname(self.user_id, 'Added ' + str(i) + 'nd Mask on Recipe(' + recipe_name + ')', self.hostname)
                    start = 0
                    end = len(pre_mask_array)
                else:
                    start = 0
                    end = len(cur_mask_array)

                for i in range(start, end):
                    pre_mask_arg_array = pre_mask_array[i].split(",")
                    cur_mask_arg_array = cur_mask_array[i].split(",")
                    if pre_mask_array[i] != cur_mask_array[i]:
                        if pre_mask_arg_array[0] != cur_mask_arg_array[0]:
                            customfunc.add_activity_hostname(self.user_id, 'Changed ' + str(i + 1) + 'nd Mask from (' + pre_mask_arg_array[0] + ') to (' + cur_mask_arg_array[0] + ') on Recipe(' + recipe_name + ')', self.hostname)
                        if pre_mask_arg_array[1] != cur_mask_arg_array[1]:
                            pre_tmp = pre_mask_arg_array[1]
                            cur_tmp = cur_mask_arg_array[1]
                            tmp = db.session.query(AminoAcids.abbre).filter(AminoAcids.short == pre_tmp).first()
                            if tmp is not None:
                                pre_tmp = tmp.abbre

                            tmp = db.session.query(AminoAcids.abbre).filter(AminoAcids.short == cur_tmp).first()
                            if tmp is not None:
                                cur_tmp = tmp.abbre

                            customfunc.add_activity_hostname(self.user_id, 'Changed ' + str(i + 1) + 'nd Mask from (' + pre_tmp + ') to (' + cur_tmp + ') on Recipe(' + recipe_name + ')', self.hostname)

            recipeheader.name = recipe_name
            recipeheader.design_id = designid
            recipeheader.userid = self.user_id
            recipeheader.date = datetime.utcnow()
            recipeheader.notes = notes
            recipeheader.mask_list = mask_list
            recipeheader.active = active
            db.session.commit()

            if changed_mask_build == "1":
                RecipeDetails.query.filter(RecipeDetails.recipe_id == recipeid).delete()
                db.session.commit()

                print("started adding rows in update_recipe")

                task.status = 'Processing'
                task.info = '0'
                db.session.commit()

                col = 1
                row = 1
                tmp_design_details = []

                total_rows = len(design_details)
                processed_rows = 0

                pre_design_col = 0
                pre_design_row = 0
                for design_detail in design_details:
                    if processed_rows == 0:
                        pre_design_col = design_detail.col
                        pre_design_row = design_detail.row

                    if design_detail.col != pre_design_col or design_detail.row != pre_design_row:
                        recipe_detail = RecipeDetails()
                        recipe_detail.recipe_id = recipeheader.id
                        recipe_detail.col = col
                        recipe_detail.row = row

                        name = ""
                        for mask_arg in mask_list_array:
                            tmp = mask_arg.split(",")
                            first_part = int(tmp[0])
                            label_id = int(first_part / 10000)
                            label_index = first_part % 10000
                            design_short = tmp[1]

                            for tmp_design_detail in tmp_design_details:
                                if tmp_design_detail.label_id == label_id:
                                    design_mask_array = tmp_design_detail.mask.split(",")
                                    tmp = ""
                                    if len(design_mask_array) > label_index:
                                        tmp = design_mask_array[label_index]
                                    if tmp == "1":
                                        name = name + design_short
                                    break
                        recipe_detail.name = name
                        db.session.add(recipe_detail)

                        if row >= int(design.y_features):
                            col = col + 1
                            row = 1
                        else:
                            row = row + 1

                        tmp_design_details = []

                    pre_design_col = design_detail.col
                    pre_design_row = design_detail.row

                    if processed_rows % 50000 == 0:
                        db.session.commit()

                    if processed_rows % 100 == 0:
                        sleep(0.001)

                    if processed_rows % 1000 == 0:
                        task.info = int(processed_rows * 100 / total_rows)
                        db.session.commit()

                    processed_rows = processed_rows + 1
                    tmp_design_details.append(design_detail)

                if len(tmp_design_details) > 0:
                    recipe_detail = RecipeDetails()
                    recipe_detail.recipe_id = recipeheader.id
                    recipe_detail.col = col
                    recipe_detail.row = row

                    name = ""
                    for mask_arg in mask_list_array:
                        tmp = mask_arg.split(",")
                        first_part = int(tmp[0])
                        label_id = int(first_part / 10000)
                        label_index = first_part % 10000
                        design_short = tmp[1]

                        for tmp_design_detail in tmp_design_details:
                            if tmp_design_detail.label_id == label_id:
                                design_mask_array = tmp_design_detail.mask.split(",")
                                tmp = ""
                                if len(design_mask_array) > label_index:
                                    tmp = design_mask_array[label_index]
                                if tmp == "1":
                                    name = name + design_short
                                break
                    recipe_detail.name = name
                    db.session.add(recipe_detail)

                task.status = 'Processing'
                task.info = '100'
                db.session.commit()

                '''
                total_rows = len(mask_list_array) * len(design_details)
                processed_rows = 1

                for mask_arg in mask_list_array:
                    tmp = mask_arg.split(",")
                    first_part = int(tmp[0])
                    label_id = int(first_part / 10000)
                    label_index = first_part % 10000
                    design_short = tmp[1]

                    col = 1
                    row = 1
                    for design_detail in design_details:
                        if design_detail.label_id == label_id:
                            recipe_detail = RecipeDetails.query.filter(RecipeDetails.recipe_id == recipeheader.id, RecipeDetails.col == col, RecipeDetails.row == row).first()
                            name = ""
                            if recipe_detail is None:
                                recipe_detail = RecipeDetails()
                                recipe_detail.recipe_id = recipeheader.id
                                recipe_detail.col = col
                                recipe_detail.row = row
                                db.session.add(recipe_detail)
                            else:
                                name = recipe_detail.name

                            design_mask_array = design_detail.mask.split(",")
                            tmp = ""
                            if len(design_mask_array) > label_index:
                                tmp = design_mask_array[label_index]
                            if tmp == "1":
                                name = name + design_short

                            recipe_detail.name = name

                            if row >= int(design.y_features):
                                col = col + 1
                                row = 1
                            else:
                                row = row + 1

                            if processed_rows % 50000 == 0:
                                db.session.commit()

                            if processed_rows % 200 == 0:
                                sleep(0.001)

                        if processed_rows % 1000 == 0:
                            task.info = int(processed_rows * 100 / total_rows)
                            db.session.commit()

                        processed_rows = processed_rows + 1
                    db.session.commit()
                '''
                print("ended adding rows in update_recipe")

            result['id'] = recipeheader.id
            result['result'] = 'SUCCESS'
            result['msg'] = ''
            task.status = "Done"
            task.info = json.dumps(result)
            db.session.commit()
        except Exception as e:
            print("update recipe error:", e)
            task.status = "Stopped"
            task.info = str(e)
            db.session.commit()
        return False


# edit recipe
@app.route("/edit_recipe", methods=['POST'])
@login_required
def edit_recipe():
    result = {'result': 'ERROR', 'msg': 'Operation failed.'}

    recipeid = int(request.form['recipeid'])
    if g.user.role != 2:
        tmp = ''
        if g.user.created_recipes is not None:
            tmp = g.user.created_recipes
        tmp_array = tmp.split(",")

        if str(recipeid) not in tmp_array:
            result['msg'] = 'Permission denied'
            return json.dumps(result)

    ipaddress = customfunc.get_ip_address()
    hostname = ''
    try:
        hostname = customfunc.get_host_name_by_ip(ipaddress)
    except Exception as e:
        hostname = customfunc.get_ip_address()

    task_id = new_task()
    task_status_url = url_for('task_status', task_id=task_id)
    AsyncUpdateRecipe(task_id=task_id, params=request.form, user_id=g.user.id, hostname=hostname)

    result['result'] = 'SUCCESS'
    result['msg'] = ''
    result['task_status_url'] = task_status_url
    return json.dumps(result)


# build mask
@app.route("/bulid_mask", methods=['POST'])
@login_required
def bulid_mask():
    result = {'result': 'ERROR', 'msg': 'Operation failed.', 'data': [], 'gal_data': []}
    designid = request.form['designid']
    x_features = request.form['x_features']
    y_features = request.form['y_features']
    mask_arg = request.form['mask_arg']
    mask_arg_array = mask_arg.split(":")

    design = Designs.query.filter(Designs.id == designid).first()
    design_details = DesignDetails.query.filter(DesignDetails.design_id == designid).order_by(DesignDetails.col, DesignDetails.row, DesignDetails.feature).all()

    if design is not None and design_details is not None:
        result['result'] = 'SUCCESS'

        for design_detail in design_details:
            name = ""
            design_mask_array = design_detail.mask.split(",")
            for mask_arg in mask_arg_array:
                arg1 = mask_arg.split(",")
                if len(arg1) != 2:
                    continue

                mask_set_num = int(arg1[0])
                design_short = arg1[1]

                tmp = ""
                if len(design_mask_array) > mask_set_num - 1:
                    tmp = design_mask_array[mask_set_num - 1]
                if tmp == "1":
                    name = name + design_short

            json_obj = {
                'col': design_detail.col,
                'row': design_detail.row,
                'name': name
            }
            result['gal_data'].append(json_obj)

        for mask_arg in mask_arg_array:
            arg1 = mask_arg.split(",")
            if len(arg1) != 2:
                continue

            mask_set_num = int(arg1[0])
            design_short = arg1[1]

            if design.mask_num < mask_set_num:
                continue

            json_obj = {
                "mask_col": "Mask " + str(mask_set_num),
                "mask_data": []
            }
            for design_detail in design_details:
                tmp = ""
                design_mask_array = design_detail.mask.split(",")
                if len(design_mask_array) > mask_set_num-1:
                    tmp = design_mask_array[mask_set_num-1]
                value = ""
                if tmp == "1":
                    value = design_short
                json_obj2 = {
                    # 'col': design_detail.col,
                    # 'row': design_detail.row,
                    'val': value
                }
                json_obj['mask_data'].append(json_obj2)

            result['data'].append(json_obj)
    return json.dumps(result)


# download recipe
@app.route("/download_recipe", methods=['GET'])
@login_required
def download_recipe():
    recipe_id = request.args.get('recipe_id', '')
    timeoffset = int(request.args.get('timeoffset', 0))

    recipe_header = RecipeHeaders.query.filter(RecipeHeaders.id == recipe_id).first()
    if recipe_header is None:
        return "Recipe does not exist."

    design = Designs.query.filter(Designs.id == recipe_header.design_id).first()
    if design is None:
        return "Design does not exist."

    design_details = DesignDetails.query.filter(DesignDetails.design_id == design.id).order_by(DesignDetails.col, DesignDetails.row, DesignDetails.feature).all()
    if design_details is None:
        return "Design Detail does not exist."

    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()

    worksheet.write(0, 0, "ATF 1.0")
    worksheet.write(1, 0, "8    5")
    worksheet.write(2, 0, '"Type=GenePix ArrayList V1.0"')
    worksheet.write(3, 0, '"Version=' + recipe_header.name + '"')
    worksheet.write(4, 0, '"BlockCount=1"')
    worksheet.write(5, 0, '"BlockType=0"')
    worksheet.write(6, 0, '"Protocol=' + recipe_header.protocol + '"')
    worksheet.write(7, 0, '"Supplier=' + recipe_header.supplier + '"')
    worksheet.write(8, 0, '"Block1= ' + str(recipe_header.x_origin) + ', ' + str(recipe_header.y_origin) + ', ' + str(recipe_header.feature_diameter) + ', ' + str(recipe_header.x_features) + ', ' + str(recipe_header.x_spacing) + ', ' + str(recipe_header.y_features) + ', ' + str(recipe_header.y_spacing) + '"')

    row = 9
    mask_arg_array = recipe_header.mask_list.split(":")
    for mask_arg in mask_arg_array:
        arg1 = mask_arg.split(",")
        if len(arg1) != 2:
            continue

        mask_set_num = int(arg1[0])
        design_short = arg1[1]
        if row > 0:
            row = row + 2
        worksheet.write(row, 0, "Mask " + str(mask_set_num))
        row = row + 1
        for i in range(1, int(recipe_header.x_features) + 1):
            worksheet.write(row, i, i)

        row = row + 1
        col = 1
        row2 = 1
        for design_detail in design_details:
            tmp = ""
            design_mask_array = design_detail.mask.split(",")
            if len(design_mask_array) > mask_set_num - 1:
                tmp = design_mask_array[mask_set_num - 1]
            value = ""
            if tmp == "1":
                value = design_short

            if col == 1:
                worksheet.write(row, 0, row2)
                worksheet.write(row, col, value)
            else:
                worksheet.write(row, col, value)

            if col >= recipe_header.x_features:
                col = 1
                row = row + 1
                row2 = row2 + 1
            else:
                col = col + 1

    workbook.close()
    output.seek(0)

    response = Response()
    response.status_code = 200
    response.data = output.read()

    # Set filname and mimetype
    file_name = recipe_header.name + " Recipe File.xlsx"
    mimetype_tuple = mimetypes.guess_type(file_name)
    # HTTP headers for forcing file download
    response_headers = Headers({
        'Pragma': "public",  # required,
        'Expires': '0',
        'Cache-Control': 'must-revalidate, post-check=0, pre-check=0',
        'Cache-Control': 'private',  # required for certain browsers,
        'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'Content-Disposition': 'attachment; filename=\"%s\";' % file_name,
        'Content-Transfer-Encoding': 'binary',
        'Content-Length': len(response.data)
    })
    if not mimetype_tuple[1] is None:
        response.update({
            'Content-Encoding': mimetype_tuple[1]
        })
    # Add headers
    response.headers = response_headers
    # jquery.fileDownload.js requirements
    response.set_cookie('fileDownload', 'true', path='/')

    output.close()
    return response


# download gal
@app.route("/download_gal", methods=['GET'])
@login_required
def download_gal():
    recipe_id = request.args.get('recipe_id', '')
    timeoffset = int(request.args.get('timeoffset', 0))

    recipe_header = RecipeHeaders.query.filter(RecipeHeaders.id == recipe_id).first()
    recipe_details = db.session.query(RecipeDetails.row, RecipeDetails.col, RecipeDetails.name).filter(RecipeDetails.recipe_id == recipe_id).order_by(RecipeDetails.row, RecipeDetails.col).first()

    if recipe_header is None or recipe_details is None:
        return "Recipe does not exist."

    design = Designs.query.filter(Designs.id == recipe_header.design_id).first()
    if design is None:
        return "Design does not exist."

    output = io.StringIO()
    output.write('ATF\t1.0\r\n')
    output.write('8\t5\r\n')
    output.write('"Type=GenePix ArrayList V1.0"\r\n')
    output.write('"BlockCount=1"\r\n')
    output.write('"BlockType=0"\r\n')
    output.write('"Protocol=' + design.protocol + '"\r\n')
    output.write('"Version=' + recipe_header.name + '"\r\n')
    output.write('"Supplier=' + design.supplier + '"\r\n')
    output.write('"Block1= ' + str(design.x_origin) + ', ' + str(design.y_origin) + ', ' + str(design.feature_diameter) + ', ' + str(design.x_features) + ', ' + str(design.x_spacing) + ', ' + str(design.y_features) + ', ' + str(design.y_spacing) + '"\r\n')
    output.write('"Block"\t"Row"\t"Column"\t"Name"\t"ID"\r\n')

    index = 1
    while True:
        recipe_details = db.session.query(RecipeDetails.row, RecipeDetails.col, RecipeDetails.name).filter(RecipeDetails.recipe_id == recipe_id).order_by(RecipeDetails.row, RecipeDetails.col).offset(index-1).limit(50000).all()
        if len(recipe_details) == 0:
            break

        for recipe_detail in recipe_details:
            output.write('1\t' + str(recipe_detail.row) + '\t' + str(recipe_detail.col) + '\t' + recipe_detail.name + '\t' + str(index) + '\r\n')
            if index % 1000 == 0:
                sleep(0.001)
            index = index + 1
    output.seek(0)

    response = Response()
    response.status_code = 200
    response.data = output.read()

    # Set filname and mimetype
    file_name = recipe_header.name + " Gal.gal"
    mimetype_tuple = mimetypes.guess_type(file_name)
    # HTTP headers for forcing file download
    response_headers = Headers({
        'Pragma': "public",  # required,
        'Expires': '0',
        'Cache-Control': 'private',  # required for certain browsers,
        'Content-Type': 'GAL File',
        'Content-Disposition': 'attachment; filename=\"%s\";' % file_name,
        'Content-Transfer-Encoding': 'binary',
        'Content-Length': len(response.data)
    })
    if not mimetype_tuple[1] is None:
        response.update({
            'Content-Encoding': mimetype_tuple[1]
        })
    # Add headers
    response.headers = response_headers
    # jquery.fileDownload.js requirements
    response.set_cookie('fileDownload', 'true', path='/')

    output.close()
    customfunc.add_activity(g.user.id, 'Downloaded GAL file for Recipe(' + recipe_header.name + ')')
    return response

