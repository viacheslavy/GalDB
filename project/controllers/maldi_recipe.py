from flask import render_template, request, json, session, Response, url_for
from project.models import *
from project.views import app, login_required, g
from project.classes import customfunc
from project.controllers.asynctask import new_task


from time import sleep
from werkzeug.datastructures import Headers
import mimetypes
import xlsxwriter
import io
import threading


# recipe template
@app.route("/maldi_recipe", methods=['GET'])
@login_required
def maldi_recipe():
    tmp_designs = Designs.query.order_by(Designs.protocol).all()

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
        if tmp.is_maldi == 1:
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
    aminos = AminoAcids.query.filter(AminoAcids.active == 1).order_by(AminoAcids.aminoacid.asc()).all()

    users = Users.query.filter(Users.amino_editor == -1).order_by(Users.username).all()
    return render_template('maldi_recipe.html', menu="maldi_recipe", designs=designs, blocktypes=blocktypes, aminos=aminos, users=users, designdetailslabels=labels)


# get maldi recipes
@app.route("/get_maldi_recipes", methods=['POST'])
@login_required
def get_maldi_recipes():
    result = {'result': 'ERROR', 'msg': 'Operation failed.', 'data': []}
    recipes = db.session.query(MaldiRecipeHeaders.id, MaldiRecipeHeaders.name, MaldiRecipeHeaders.notes, MaldiRecipeHeaders.design_id, MaldiRecipeHeaders.date, MaldiRecipeHeaders.userid, MaldiRecipeHeaders.mask_list,  MaldiRecipeHeaders.supplier, MaldiRecipeHeaders.block_type, MaldiRecipeHeaders.x_origin, MaldiRecipeHeaders.y_origin, MaldiRecipeHeaders.feature_diameter, MaldiRecipeHeaders.x_features, MaldiRecipeHeaders.x_spacing, MaldiRecipeHeaders.y_features, MaldiRecipeHeaders.y_spacing, MaldiRecipeHeaders.spacer, MaldiRecipeHeaders.protection, MaldiRecipeHeaders.standard, Designs.mask_num, Designs.protocol, MaldiRecipeHeaders.active).outerjoin(Designs, Designs.id == MaldiRecipeHeaders.design_id).order_by(MaldiRecipeHeaders.date.desc(), MaldiRecipeHeaders.name.asc()).all()
    if recipes is not None:
        result['result'] = 'SUCCESS'
        result['msg'] = ''
        for recipe in recipes:
            protection = 0
            if recipe.protection == 1:
                protection = 1
            json_obj = {
                'id': recipe.id,
                'userid': recipe.userid,
                'name': recipe.name,
                'date': recipe.date,
                "design": recipe.design_id,
                "supplier": recipe.supplier,
                "block_type": recipe.block_type,
                "x_origin": recipe.x_origin,
                "y_origin": recipe.y_origin,
                "feature_diameter": recipe.feature_diameter,
                "x_features": recipe.x_features,
                "x_spacing": recipe.x_spacing,
                "y_features": recipe.y_features,
                "y_spacing": recipe.y_spacing,
                "protection": protection,
                "spacer": recipe.spacer,
                "standard": recipe.standard,
                "notes": recipe.notes,
                "design_text": recipe.protocol,
                "mask_list": recipe.mask_list,
                "mask_num": recipe.mask_num,
                "active": recipe.active
            }
            result['data'].append(json_obj)

    return json.dumps(result)


# get mask set param
@app.route("/get_mask_set_param", methods=['POST'])
@login_required
def get_mask_set_param():
    result = {'result': 'ERROR', 'msg': 'Operation failed.', 'data': {}}
    id = request.form['mask_set_id']

    design = Designs.query.filter(Designs.id == id).first()
    if design is not None:
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

    return json.dumps(result)


# genearte maldi gal header
@app.route("/generate_maldi_gal_header", methods=['POST'])
@login_required
def generate_maldi_gal_header():
    result = {'result': 'ERROR', 'msg': 'Operation failed.', 'data': ''}

    protocol = request.form['protocol']
    supplier = request.form['supplier']
    block_type = request.form['block_type']
    x_origin = request.form['x_origin']
    y_origin = request.form['y_origin']
    feature_diameter = request.form['feature_diameter']
    x_features = request.form['x_features']
    x_spacing = request.form['x_spacing']
    y_features = request.form['y_features']
    y_spacing = request.form['y_spacing']

    tmp_result = 'ATF\t1.0\n'
    tmp_result += '8\t9\n'
    tmp_result += 'Type=GenePix ArrayList V1.0\n'
    tmp_result += 'BlockCount=1\n'
    tmp_result += 'BlockType=' + block_type + '\n'
    tmp_result += '"Supplier=' + supplier + '"\n'
    tmp_result += 'ArrayName=' + protocol + '"\n'
    tmp_result += 'ArrayerSoftwareVersion=1.1' + '\n'
    tmp_result += 'SlideBarcode=SSA' + '\n'

    tmp_result += '"Block1= ' + x_origin + ', ' + y_origin + ', ' + feature_diameter + ', ' + x_features + ', ' + x_spacing + ', ' + y_features + ', ' + y_spacing + '"\n'

    result['result'] = 'SUCCESS'
    result['data'] = tmp_result

    return json.dumps(result)


# add maldi_recipe in thread
class AsyncAddMaldiRecipe(object):
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

        name = _request_form['recipe_name']
        designid = _request_form['designid']
        protocol = _request_form['design_text']
        supplier = _request_form['supplier']
        block_type = _request_form['block_type']
        x_origin = _request_form['x_origin']
        y_origin = _request_form['y_origin']
        feature_diameter = _request_form['feature_diameter']
        x_features = _request_form['x_features']
        x_spacing = _request_form['x_spacing']
        y_features = _request_form['y_features']
        y_spacing = _request_form['y_spacing']
        protection = _request_form['protection']
        spacer = _request_form['spacer']
        standard = _request_form['standard']
        notes = _request_form['notes']
        mask_list = _request_form['mask_list']
        active = _request_form['active']

        task = Tasks.query.filter(Tasks.id == self.task_id).first()
        if task is None:
            return False

        recipeheader = MaldiRecipeHeaders.query.filter(MaldiRecipeHeaders.name == name).first()
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

        design_details = db.session.query(DesignDetails.col, DesignDetails.row, DesignDetails.feature, DesignDetails.mask, DesignDetails.label_id).filter(DesignDetails.design_id == designid).order_by(DesignDetails.col, DesignDetails.row, DesignDetails.label_id).all()
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
            recipeheader = MaldiRecipeHeaders()
            recipeheader.name = name
            recipeheader.design_id = designid
            recipeheader.protocol = protocol
            recipeheader.supplier = supplier
            recipeheader.block_type = block_type
            recipeheader.x_origin = x_origin
            recipeheader.y_origin = y_origin
            recipeheader.feature_diameter = feature_diameter
            recipeheader.x_features = x_features
            recipeheader.x_spacing = x_spacing
            recipeheader.y_features = y_features
            recipeheader.y_spacing = y_spacing
            recipeheader.protection = protection
            recipeheader.spacer = spacer
            recipeheader.standard = standard
            recipeheader.userid = self.user_id
            recipeheader.notes = notes
            recipeheader.mask_list = mask_list
            recipeheader.active = active
            recipeheader.date = datetime.utcnow()

            db.session.add(recipeheader)
            db.session.commit()

            aminos = AminoAcids.query.all()

            print("started adding rows in add maldi recipe")

            task.status = 'Processing'
            task.info = '0'
            db.session.commit()

            tmp_design_details = []

            total_rows = len(design_details)
            processed_rows = 0

            pre_design_col = 0
            pre_design_row = 0
            pre_design_feature = 0
            for design_detail in design_details:
                if processed_rows == 0:
                    pre_design_col = design_detail.col
                    pre_design_row = design_detail.row
                    pre_design_feature = design_detail.feature

                if design_detail.col != pre_design_col or design_detail.row != pre_design_row:
                    recipe_detail = MaldiRecipeDetails()
                    recipe_detail.recipe_id = recipeheader.id
                    recipe_detail.col = pre_design_col
                    recipe_detail.row = pre_design_row
                    recipe_detail.name = pre_design_feature
                    iid = int(pre_design_row) - 1 + (int(pre_design_col) - 1) * 15
                    recipe_detail.iid = iid
                    if spacer == '0':
                        recipe_detail.var_x = 982.43
                    else:
                        recipe_detail.var_x = 798.34

                    if standard == '0':
                        recipe_detail.var_z = 560.36
                    elif standard == '1':
                        recipe_detail.var_z = 1616.99
                    else:
                        recipe_detail.var_z = 2145.31
                    recipe_detail.var_x_key = 'Spacer'
                    recipe_detail.var_y_key = 'Desired'
                    recipe_detail.var_z_key = 'Standard'

                    if len(design_details) == 229:
                        recipe_detail.var_multi_csv = 'AD'
                        recipe_detail.var_multi_csv_keys = 'AD'
                    else:
                        recipe_detail.var_multi_csv = 'BC'
                        recipe_detail.var_multi_csv_keys = 'BC'

                    sequence = ""
                    var_y = 0
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
                                    sequence = sequence + design_short
                                    for amino in aminos:
                                        if amino.short == design_short:
                                            if protection == "1":
                                                var_y = var_y + amino.mon_mass + amino.protgrp
                                            else:
                                                var_y = var_y + amino.mon_mass
                                            break
                                break

                    recipe_detail.sequence = sequence
                    recipe_detail.var_y = var_y
                    db.session.add(recipe_detail)
                    tmp_design_details = []

                pre_design_col = design_detail.col
                pre_design_row = design_detail.row
                pre_design_feature = design_detail.feature

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
                recipe_detail = MaldiRecipeDetails()
                recipe_detail.recipe_id = recipeheader.id
                recipe_detail.col = pre_design_col
                recipe_detail.row = pre_design_row
                recipe_detail.name = pre_design_feature
                iid = int(pre_design_row) - 1 + (int(pre_design_col) - 1) * 15
                recipe_detail.iid = iid
                if spacer == '0':
                    recipe_detail.var_x = 982.43
                else:
                    recipe_detail.var_x = 798.34

                if standard == '0':
                    recipe_detail.var_z = 560.36
                elif standard == '1':
                    recipe_detail.var_z = 1616.99
                else:
                    recipe_detail.var_z = 2145.31
                recipe_detail.var_x_key = 'Spacer'
                recipe_detail.var_y_key = 'Desired'
                recipe_detail.var_z_key = 'Standard'

                if len(design_details) == 229:
                    recipe_detail.var_multi_csv = 'AD'
                    recipe_detail.var_multi_csv_keys = 'AD'
                else:
                    recipe_detail.var_multi_csv = 'BC'
                    recipe_detail.var_multi_csv_keys = 'BC'

                sequence = ""
                var_y = 0
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
                                sequence = sequence + design_short
                                for amino in aminos:
                                    if amino.short == design_short:
                                        if protection == "1":
                                            var_y = var_y + amino.mon_mass + amino.protgrp
                                        else:
                                            var_y = var_y + amino.mon_mass
                                        break
                            break

                recipe_detail.sequence = sequence
                recipe_detail.var_y = var_y
                db.session.add(recipe_detail)

            task.status = 'Processing'
            task.info = '100'
            db.session.commit()

            print("ended adding rows in add maldi recipe")

            result['id'] = recipeheader.id
            result['date'] = recipeheader.date
            result['result'] = 'SUCCESS'
            result['msg'] = ''

            task.status = 'Done'
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

            customfunc.add_activity_hostname(self.user_id, 'Created Maldi Recipe(' + recipeheader.name + ')', self.hostname)
        except Exception as e:
            task.status = 'Stopped'
            task.info = str(e)
            db.session.commit()
            print("add maldi recipe error:", e)

        return json.dumps(result)


# add recipe
@app.route("/add_maldi_recipe", methods=['POST'])
@login_required
def add_maldi_recipe():
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
    AsyncAddMaldiRecipe(task_id=task_id, params=request.form, user_id=g.user.id, hostname=hostname)

    result['result'] = 'SUCCESS'
    result['msg'] = ''
    result['task_status_url'] = task_status_url
    return json.dumps(result)


# do actual update of maldi_recipe
class AsyncUpdateMaldiRecipe(object):
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
        designid = _request_form['designid']
        design_text = _request_form['design_text']
        recipe_name = _request_form['recipe_name']
        supplier = _request_form['supplier']
        block_type = _request_form['block_type']
        x_origin = _request_form['x_origin']
        y_origin = _request_form['y_origin']
        feature_diameter = _request_form['feature_diameter']
        x_features = _request_form['x_features']
        x_spacing = _request_form['x_spacing']
        y_features = _request_form['y_features']
        y_spacing = _request_form['y_spacing']
        protection = _request_form['protection']
        spacer = _request_form['spacer']
        standard = _request_form['standard']
        notes = _request_form['notes']
        mask_list = _request_form['mask_list']
        active = _request_form['active']

        active_text = 'No'
        if active == '1':
            active_text = 'Yes'

        task = Tasks.query.filter(Tasks.id == self.task_id).first()
        if task is None:
            return False

        recipeheader = MaldiRecipeHeaders.query.filter(MaldiRecipeHeaders.name == recipe_name).first()
        if recipeheader is not None and recipeheader.id != recipeid:
            task.status = 'Stopped'
            task.info = 'Duplicate: The Name already exist.'
            db.session.commit()
            return False

        recipeheader = MaldiRecipeHeaders.query.filter(MaldiRecipeHeaders.id == recipeid).first()
        if recipeheader is None:
            task.status = 'Stopped'
            task.info = 'The Recipe does not exist.'
            db.session.commit()
            return False

        design = Designs.query.filter(Designs.id == designid).first()
        if design is None:
            task.status = 'Stopped'
            task.info = 'The Design does not exist.'
            db.session.commit()
            return False

        design_details = db.session.query(DesignDetails.col, DesignDetails.row, DesignDetails.feature, DesignDetails.mask, DesignDetails.label_id).filter(DesignDetails.design_id == designid).order_by(DesignDetails.col, DesignDetails.row, DesignDetails.label_id).all()

        if design_details is None:
            task.status = 'Stopped'
            task.info = 'The Design Detail does not exist.'
            db.session.commit()
            return False

        mask_list_array = mask_list.split(":")
        for value in mask_list_array:
            arg1 = value.split(",")
            if len(arg1) != 2:
                task.status = 'Stopped'
                task.info = "Masks are not correct."
                db.session.commit()
                return False

        try:
            # Add changed log start #########
            log_str = ""
            need_build = False
            if recipeheader.name != recipe_name:
                log_str = 'Recipe Name from (' + recipeheader.name + ') to (' + recipe_name + ')'

            if recipeheader.design_id != int(designid):
                need_build = True
                if log_str == "":
                    log_str = 'Design from (' + design.protocol + ') to (' + design_text + ') on Maldi Recipe(' + recipe_name + ')'
                else:
                    log_str = log_str + ", " + 'Design from (' + design.protocol + ') to (' + design_text + ') on Maldi Recipe(' + recipe_name + ')'

            if recipeheader.supplier != supplier:
                need_build = True
                if log_str == "":
                    log_str = 'Supplier from (' + recipeheader.supplier + ') to (' + supplier + ') on Maldi Recipe(' + recipe_name + ')'
                else:
                    log_str = log_str + ", " + 'Supplier from (' + recipeheader.supplier + ') to (' + supplier + ') on Maldi Recipe(' + recipe_name + ')'

            if recipeheader.block_type != int(block_type):
                need_build = True
                pre_block = ''
                tmp_block = db.session.query(BlockTypes.name).filter(BlockTypes.id == recipeheader.block_type).first()
                if tmp_block is not None:
                    pre_block = tmp_block.name

                cur_block = ''
                tmp_block = db.session.query(BlockTypes.name).filter(BlockTypes.id == int(block_type)).first()
                if tmp_block is not None:
                    cur_block = tmp_block.name

                if log_str == "":
                    log_str = 'Block Type from (' + pre_block + ') to (' + cur_block + ') on Maldi Recipe(' + recipe_name + ')'
                else:
                    log_str = log_str + ", " + 'Block Type from (' + pre_block + ') to (' + cur_block + ') on Maldi Recipe(' + recipe_name + ')'

            if str(recipeheader.x_origin) != x_origin:
                need_build = True
                if log_str == "":
                    log_str = 'X Origin from (' + str(recipeheader.x_origin) + ') to (' + x_origin + ') on Maldi Recipe(' + recipe_name + ')'
                else:
                    log_str = log_str + ", " + 'X Origin from (' + str(recipeheader.x_origin) + ') to (' + x_origin + ') on Maldi Recipe(' + recipe_name + ')'

            if str(recipeheader.y_origin) != y_origin:
                need_build = True
                if log_str == "":
                    log_str = 'Y Origin from (' + str(recipeheader.y_origin) + ') to (' + y_origin + ') on Maldi Recipe(' + recipe_name + ')'
                else:
                    log_str = log_str + ", " + 'Y Origin from (' + str(recipeheader.y_origin) + ') to (' + y_origin + ') on Maldi Recipe(' + recipe_name + ')'

            if float(recipeheader.feature_diameter) != float(feature_diameter):
                need_build = True
                if log_str == "":
                    log_str = 'Feature Diameter from (' + str(recipeheader.feature_diameter) + ') to (' + feature_diameter + ') on Maldi Recipe(' + recipe_name + ')'
                else:
                    log_str = log_str + ", " + 'Feature Diameter from (' + str(recipeheader.feature_diameter) + ') to (' + feature_diameter + ') on Maldi Recipe(' + recipe_name + ')'

            if str(recipeheader.x_features) != x_features:
                need_build = True
                if log_str == "":
                    log_str = 'X Features from (' + str(recipeheader.x_features) + ') to (' + x_features + ') on Maldi Recipe(' + recipe_name + ')'
                else:
                    log_str = log_str + ", " + 'X Features from (' + str(recipeheader.x_features) + ') to (' + x_features + ') on Maldi Recipe(' + recipe_name + ')'

            if float(recipeheader.x_spacing) != float(x_spacing):
                need_build = True
                if log_str == "":
                    log_str = 'X Spacing from (' + str(recipeheader.x_spacing) + ') to (' + x_spacing + ') on Maldi Recipe(' + recipe_name + ')'
                else:
                    log_str = log_str + ", " + 'X Spacing from (' + str(recipeheader.x_spacing) + ') to (' + x_spacing + ') on Maldi Recipe(' + recipe_name + ')'

            if str(recipeheader.y_features) != y_features:
                need_build = True
                if log_str == "":
                    log_str = 'Y Features from (' + str(recipeheader.y_features) + ') to (' + y_features + ') on Maldi Recipe(' + recipe_name + ')'
                else:
                    log_str = log_str + ", " + 'Y Features from (' + str(recipeheader.y_features) + ') to (' + y_features + ') on Maldi Recipe(' + recipe_name + ')'

            if float(recipeheader.y_spacing) != float(y_spacing):
                need_build = True
                if log_str == "":
                    log_str = 'Y Spacing from (' + str(recipeheader.y_spacing) + ') to (' + y_spacing + ') on Maldi Recipe(' + recipe_name + ')'
                else:
                    log_str = log_str + ", " + 'Y Spacing from (' + str(recipeheader.y_spacing) + ') to (' + y_spacing + ') on Maldi Recipe(' + recipe_name + ')'

            if recipeheader.protection != int(protection):
                need_build = True
                pre_protection = 'False'
                if recipeheader.protection == 1:
                    pre_protection = 'True'

                cur_protection = 'False'
                if int(protection) == 1:
                    cur_protection = 'True'

                if log_str == "":
                    log_str = 'Protection from (' + pre_protection + ') to (' + cur_protection + ') on Maldi Recipe(' + recipe_name + ')'
                else:
                    log_str = log_str + ", " + 'Protection from (' + pre_protection + ') to (' + cur_protection + ') on Maldi Recipe(' + recipe_name + ')'

            if recipeheader.spacer != int(spacer):
                need_build = True
                pre_spacer = 'SCL Linker'
                if recipeheader.spacer == 1:
                    pre_spacer = 'DKP Linker'

                cur_spacer = 'SCL Linker'
                if int(spacer) == 1:
                    cur_spacer = 'DKP Linker'

                if log_str == "":
                    log_str = 'Spacer from (' + pre_spacer + ') to (' + cur_spacer + ') on Maldi Recipe(' + recipe_name + ')'
                else:
                    log_str = log_str + ", " + 'Spacer from (' + pre_spacer + ') to (' + cur_spacer + ') on Maldi Recipe(' + recipe_name + ')'

            if recipeheader.standard != int(standard):
                need_build = True
                pre_standard = 'PEG12'
                if recipeheader.standard == 1:
                    pre_standard = 'PEG36'
                elif recipeheader.standard == 2:
                    pre_standard = 'PEG48'

                cur_standard = 'PEG12'
                if int(standard) == 1:
                    cur_standard = 'PEG36'
                elif int(standard) == 2:
                    cur_standard = 'PEG48'

                if log_str == "":
                    log_str = 'Standard from (' + pre_standard + ') to (' + cur_standard + ') on Maldi Recipe(' + recipe_name + ')'
                else:
                    log_str = log_str + ", " + 'Standard from (' + pre_standard + ') to (' + cur_standard + ') on Maldi Recipe(' + recipe_name + ')'

            if recipeheader.notes != notes:
                need_build = True
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
                    log_str = 'Notes from (' + pre_notes + ') to (' + cur_notes + ') on Maldi Recipe(' + recipe_name + ')'
                else:
                    log_str = log_str + ", " + 'Notes from (' + pre_notes + ') to (' + cur_notes + ') on Maldi Recipe(' + recipe_name + ')'

            if recipeheader.active != int(active):
                need_build = True
                pre_active = 'False'
                if recipeheader.active == 1:
                    pre_active = 'True'

                cur_active = 'False'
                if int(active) == 1:
                    cur_active = 'True'

                if log_str == "":
                    log_str = 'Active from (' + pre_active + ') to (' + cur_active + ') on Maldi Recipe(' + recipe_name + ')'
                else:
                    log_str = log_str + ", " + 'Active from (' + pre_active + ') to (' + cur_active + ') on Maldi Recipe(' + recipe_name + ')'

            if log_str != "":
                customfunc.add_activity_hostname(self.user_id, log_str, self.hostname)

            if recipeheader.mask_list != mask_list:
                need_build = True
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
                        customfunc.add_activity_hostname(self.user_id, 'Deleted ' + str(i) + 'nd Mask on Maldi Recipe(' + recipe_name + ')', self.hostname)
                elif len(cur_mask_array) > len(pre_mask_array):
                    for i in range(len(pre_mask_array) + 1, len(cur_mask_array) + 1):
                        customfunc.add_activity_hostname(self.user_id, 'Added ' + str(i) + 'nd Mask on Maldi Recipe(' + recipe_name + ')', self.hostname)
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
                            customfunc.add_activity_hostname(self.user_id, 'Changed ' + str(i + 1) + 'nd Mask from (' + pre_mask_arg_array[0] + ') to (' + cur_mask_arg_array[0] + ') on Maldi Recipe(' + recipe_name + ')', self.hostname)
                        if pre_mask_arg_array[1] != cur_mask_arg_array[1]:
                            pre_tmp = pre_mask_arg_array[1]
                            cur_tmp = cur_mask_arg_array[1]
                            tmp = db.session.query(AminoAcids.abbre).filter(AminoAcids.short == pre_tmp).first()
                            if tmp is not None:
                                pre_tmp = tmp.abbre

                            tmp = db.session.query(AminoAcids.abbre).filter(AminoAcids.short == cur_tmp).first()
                            if tmp is not None:
                                cur_tmp = tmp.abbre

                            customfunc.add_activity_hostname(self.user_id, 'Changed ' + str(i + 1) + 'nd Mask from (' + pre_tmp + ') to (' + cur_tmp + ') on Maldi Recipe(' + recipe_name + ')', self.hostname)

            # Add changed log end #########
            recipeheader.name = recipe_name
            recipeheader.userid = self.user_id
            recipeheader.design_id = designid
            recipeheader.protocol = design_text
            recipeheader.supplier = supplier
            recipeheader.block_type = block_type
            recipeheader.x_origin = int(float(x_origin))
            recipeheader.y_origin = int(float(y_origin))
            recipeheader.feature_diameter = feature_diameter
            recipeheader.x_features = int(float(x_features))
            recipeheader.x_spacing = float(x_spacing)
            recipeheader.y_features = int(float(y_features))
            recipeheader.y_spacing = float(y_spacing)
            recipeheader.protection = protection
            recipeheader.spacer = spacer
            recipeheader.standard = standard
            recipeheader.notes = notes
            recipeheader.mask_list = mask_list
            recipeheader.active = active

            db.session.commit()

            aminos = AminoAcids.query.all()

            if need_build is True:
                MaldiRecipeDetails.query.filter(MaldiRecipeDetails.recipe_id == recipeid).delete()
                db.session.commit()

                print("started adding rows in update maldi recipe")

                task.status = 'Processing'
                task.info = '0'
                db.session.commit()

                tmp_design_details = []

                total_rows = len(design_details)
                processed_rows = 0

                pre_design_col = 0
                pre_design_row = 0
                pre_design_feature = 0
                for design_detail in design_details:
                    if processed_rows == 0:
                        pre_design_col = design_detail.col
                        pre_design_row = design_detail.row
                        pre_design_feature = design_detail.feature

                    if design_detail.col != pre_design_col or design_detail.row != pre_design_row:
                        recipe_detail = MaldiRecipeDetails()
                        recipe_detail.recipe_id = recipeheader.id
                        recipe_detail.col = pre_design_col
                        recipe_detail.row = pre_design_row
                        recipe_detail.name = pre_design_feature
                        iid = int(pre_design_row) - 1 + (int(pre_design_col) - 1) * 15
                        recipe_detail.iid = iid
                        if spacer == '0':
                            recipe_detail.var_x = 982.43
                        else:
                            recipe_detail.var_x = 798.34

                        if standard == '0':
                            recipe_detail.var_z = 560.36
                        elif standard == '1':
                            recipe_detail.var_z = 1616.99
                        else:
                            recipe_detail.var_z = 2145.31
                        recipe_detail.var_x_key = 'Spacer'
                        recipe_detail.var_y_key = 'Desired'
                        recipe_detail.var_z_key = 'Standard'

                        if len(design_details) == 229:
                            recipe_detail.var_multi_csv = 'AD'
                            recipe_detail.var_multi_csv_keys = 'AD'
                        else:
                            recipe_detail.var_multi_csv = 'BC'
                            recipe_detail.var_multi_csv_keys = 'BC'

                        sequence = ""
                        var_y = 0
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
                                        sequence = sequence + design_short
                                        for amino in aminos:
                                            if amino.short == design_short:
                                                if protection == "1":
                                                    var_y = var_y + amino.mon_mass + amino.protgrp
                                                else:
                                                    var_y = var_y + amino.mon_mass
                                                break
                                    break

                        recipe_detail.sequence = sequence
                        recipe_detail.var_y = var_y
                        db.session.add(recipe_detail)
                        tmp_design_details = []

                    pre_design_col = design_detail.col
                    pre_design_row = design_detail.row
                    pre_design_feature = design_detail.feature

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
                    recipe_detail = MaldiRecipeDetails()
                    recipe_detail.recipe_id = recipeheader.id
                    recipe_detail.col = pre_design_col
                    recipe_detail.row = pre_design_row
                    recipe_detail.name = pre_design_feature
                    iid = int(pre_design_row) - 1 + (int(pre_design_col) - 1) * 15
                    recipe_detail.iid = iid
                    if spacer == '0':
                        recipe_detail.var_x = 982.43
                    else:
                        recipe_detail.var_x = 798.34

                    if standard == '0':
                        recipe_detail.var_z = 560.36
                    elif standard == '1':
                        recipe_detail.var_z = 1616.99
                    else:
                        recipe_detail.var_z = 2145.31
                    recipe_detail.var_x_key = 'Spacer'
                    recipe_detail.var_y_key = 'Desired'
                    recipe_detail.var_z_key = 'Standard'

                    if len(design_details) == 229:
                        recipe_detail.var_multi_csv = 'AD'
                        recipe_detail.var_multi_csv_keys = 'AD'
                    else:
                        recipe_detail.var_multi_csv = 'BC'
                        recipe_detail.var_multi_csv_keys = 'BC'

                    sequence = ""
                    var_y = 0
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
                                    sequence = sequence + design_short
                                    for amino in aminos:
                                        if amino.short == design_short:
                                            if protection == "1":
                                                var_y = var_y + amino.mon_mass + amino.protgrp
                                            else:
                                                var_y = var_y + amino.mon_mass
                                            break
                                break

                    recipe_detail.sequence = sequence
                    recipe_detail.var_y = var_y
                    db.session.add(recipe_detail)

                task.status = 'Processing'
                task.info = '100'
                db.session.commit()

                print("ended adding rows in update maldi recipe")

            '''
            task.status = 'Processing'
            task.info = '0'
            db.session.commit()

            total_rows = len(mask_list_array) * len(design_details)
            processed_rows = 1

            for mask_arg in mask_list_array:
                tmp = mask_arg.split(",")
                first_part = int(tmp[0])
                label_id = int(first_part / 10000)
                label_index = first_part % 10000
                design_short = tmp[1]

                for design_detail in design_details:
                    if design_detail.label_id == label_id:
                        recipe_detail = MaldiRecipeDetails.query.filter(MaldiRecipeDetails.recipe_id == recipeheader.id, MaldiRecipeDetails.col == design_detail.col, MaldiRecipeDetails.row == design_detail.row).first()
                        sequence = ""
                        var_y = 0
                        if recipe_detail is None:
                            recipe_detail = MaldiRecipeDetails()
                            recipe_detail.recipe_id = recipeheader.id
                            recipe_detail.col = design_detail.col
                            recipe_detail.row = design_detail.row
                            recipe_detail.name = design_detail.feature

                            iid = int(design_detail.row) - 1 + (int(design_detail.col) - 1) * 15
                            recipe_detail.iid = iid
                            if spacer == '0':
                                recipe_detail.var_x = 982.43
                            else:
                                recipe_detail.var_x = 798.34

                            if standard == '0':
                                recipe_detail.var_z = 560.36
                            elif standard == '1':
                                recipe_detail.var_z = 1616.99
                            else:
                                recipe_detail.var_z = 2145.31
                            recipe_detail.var_x_key = 'Spacer'
                            recipe_detail.var_y_key = 'Desired'
                            recipe_detail.var_z_key = 'Standard'

                            if len(design_details) == 229:
                                recipe_detail.var_multi_csv = 'AD'
                                recipe_detail.var_multi_csv_keys = 'AD'
                            else:
                                recipe_detail.var_multi_csv = 'BC'
                                recipe_detail.var_multi_csv_keys = 'BC'
                            db.session.add(recipe_detail)
                        else:
                            sequence = recipe_detail.sequence
                            var_y = recipe_detail.var_y

                        design_mask_array = design_detail.mask.split(",")
                        tmp = ""
                        if len(design_mask_array) > label_index:
                            tmp = design_mask_array[label_index]
                        if tmp == "1":
                            sequence = sequence + design_short
                            for amino in aminos:
                                if amino.short == design_short:
                                    if protection == "1":
                                        var_y = var_y + amino.mon_mass + amino.protgrp
                                    else:
                                        var_y = var_y + amino.mon_mass
                                    break

                        recipe_detail.sequence = sequence
                        recipe_detail.var_y = var_y

                        if processed_rows % 50000 == 0:
                            db.session.commit()

                        if processed_rows % 200 == 0:
                            sleep(0.001)

                    if processed_rows % 1000 == 0:
                        percent = int(processed_rows * 100 / total_rows)
                        task.info = str(percent)
                        db.session.commit()

                    processed_rows = processed_rows + 1
                db.session.commit()
            '''

            result['id'] = recipeheader.id
            result['result'] = 'SUCCESS'
            result['msg'] = ''

            task.status = 'Done'
            task.info = json.dumps(result)
            db.session.commit()
        except Exception as e:
            task.status = 'Stopped'
            task.info = str(e)
            db.session.commit()

            print("edit maldi recipe error:", e)

        return result


# edit maldi recipe
@app.route("/edit_maldi_recipe", methods=['POST'])
@login_required
def edit_maldi_recipe():
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
    AsyncUpdateMaldiRecipe(task_id=task_id, params=request.form, user_id=g.user.id, hostname=hostname)

    result['result'] = 'SUCCESS'
    result['msg'] = ''
    result['task_status_url'] = task_status_url
    return json.dumps(result)


# delete maldi recipe
@app.route("/delete_maldi_recipe", methods=['POST'])
@login_required
def delete_maldi_recipe():
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
        recipe = MaldiRecipeHeaders.query.filter(MaldiRecipeHeaders.id == recipe_id).first()
        recipe_name = recipe.name

        MaldiRecipeDetails.query.filter(MaldiRecipeDetails.recipe_id == recipe_id).delete()
        MaldiRecipeHeaders.query.filter(MaldiRecipeHeaders.id == recipe_id).delete()
        db.session.commit()

        session.pop("current_recipe_id", None)
        result['result'] = 'SUCCESS'
        result['msg'] = ''
        customfunc.add_activity(g.user.id, 'Deleted Maldi Recipe(' + recipe_name + ')')
    except Exception as e:
        print("delete recipe error:", e)
    return json.dumps(result)


# download maldi gal
@app.route("/download_maldi_gal", methods=['GET'])
@login_required
def download_maldi_gal():
    recipe_id = request.args.get('recipe_id', '')
    timeoffset = int(request.args.get('timeoffset', 0))

    recipe_header = MaldiRecipeHeaders.query.filter(MaldiRecipeHeaders.id == recipe_id).first()
    recipe_details = MaldiRecipeDetails.query.filter(MaldiRecipeDetails.recipe_id == recipe_id).order_by(MaldiRecipeDetails.row, MaldiRecipeDetails.col).first()

    if recipe_header is None or recipe_details is None:
        return "Recipe does not exist."

    design = Designs.query.filter(Designs.id == recipe_header.design_id).first()
    if design is None:
        return "Design does not exist."

    output = io.StringIO()
    output.write('ATF\t1.0\r\n')
    output.write('8\t9\r\n')
    output.write('Type=GenePix ArrayList V1.0\r\n')
    output.write('BlockCount=1\r\n')
    output.write('BlockType=' + str(recipe_header.block_type) + '\r\n')
    output.write('"Supplier=' + recipe_header.supplier + '"\r\n')
    output.write('ArrayName=' + recipe_header.protocol + '\r\n')
    output.write('ArrayerSoftwareVersion=1.1\r\n')
    output.write('SlideBarcode=SSA\r\n')
    output.write('"Block1= ' + str(recipe_header.x_origin) + ', ' + str(recipe_header.y_origin) + ', ' + str(recipe_header.feature_diameter) + ', ' + str(recipe_header.x_features) + ', ' + str(recipe_header.x_spacing) + ', ' + str(recipe_header.y_features) + ', ' + str(recipe_header.y_spacing) + '"\r\n')
    output.write('Block\tRow\tColumn\tName\tID\tExperimental_Var_X\tExperimental_Var_Y\tExperimental_Var_Z\tExperimental_Var_Multi_CSV\tExperimental_Var_X_Key\tExperimental_Var_Y_Key\tExperimental_Var_Z_Key\tExperimental_Var_Multi_CSV_Keys\tSequence\r\n')

    index = 1
    while True:
        recipe_details = MaldiRecipeDetails.query.filter(MaldiRecipeDetails.recipe_id == recipe_id).order_by(MaldiRecipeDetails.row, MaldiRecipeDetails.col).offset(index-1).limit(50000).all()
        if len(recipe_details) == 0:
            break

        for recipe_detail in recipe_details:
            var_x = ''
            if recipe_detail.var_x is not None:
                var_x = str(recipe_detail.var_x)

            var_y = ''
            if recipe_detail.var_y is not None:
                var_y = str(recipe_detail.var_y)

            var_z = ''
            if recipe_detail.var_z is not None:
                var_z = str(recipe_detail.var_z)

            var_multi_csv = ''
            if recipe_detail.var_multi_csv is not None:
                var_multi_csv = recipe_detail.var_multi_csv

            var_x_key = ''
            if recipe_detail.var_x_key is not None:
                var_x_key = recipe_detail.var_x_key

            var_y_key = ''
            if recipe_detail.var_y_key is not None:
                var_y_key = recipe_detail.var_y_key

            var_z_key = ''
            if recipe_detail.var_z_key is not None:
                var_z_key = recipe_detail.var_z_key

            var_multi_csv_keys = ''
            if recipe_detail.var_multi_csv_keys is not None:
                var_multi_csv_keys = recipe_detail.var_multi_csv_keys

            sequence = ''
            if recipe_detail.sequence is not None:
                sequence = recipe_detail.sequence

            output.write('1\t' + str(recipe_detail.row) + '\t' + str(recipe_detail.col) + '\t' + str(recipe_detail.name) + '\t' + str(recipe_detail.iid) + '\t' + str(var_x) + '\t' + str(var_y) + '\t' + str(var_z) + '\t' + var_multi_csv + '\t' + var_x_key + '\t' + var_y_key + '\t' + var_z_key + '\t' + var_multi_csv_keys + '\t' + sequence + '\r\n')

            if index % 1000 == 0:
                sleep(0.001)

            index = index + 1

    output.seek(0)

    response = Response()
    response.status_code = 200
    response.data = output.read()

    # Set filname and mimetype
    file_name = 'test.gal'
    if len(recipe_details) == 229:
        file_name = recipe_header.name + '_AD_gal.gal'
    else:
        file_name = recipe_header.name + '_BC_gal.gal'
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

    customfunc.add_activity(g.user.id, 'Downloaded GAL file for Maldi Recipe(' + recipe_header.name + ')')
    return response
