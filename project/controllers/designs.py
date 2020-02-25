#!/usr/bin/env python
from flask import render_template, json, request, session, url_for
from flask import copy_current_request_context
from project.views import app, login_required, db, g
from project.models import *
from project.classes import customfunc
from project.controllers.asynctask import new_task
from sqlalchemy import exc, func, or_
from time import sleep
import csv
import io
import threading


@app.route("/designs", methods=['GET'])
@login_required
def designs():
    blocktypes = BlockTypes.query.all()

    current_design_id = 0
    if 'current_design_id' in session:
        current_design_id = int(session['current_design_id'])

    labels = []
    tmp_labels = db.session.query(DesignDetailsLabels.id, DesignDetailsLabels.label, DesignDetailsLabels.label_num).all()
    for tmp in tmp_labels:
        json_obj = {
            'id': tmp.id,
            'label': tmp.label,
            'label_num': tmp.label_num
        }
        labels.append(json_obj)
    return render_template('designs.html', menu="designs", blocktypes=blocktypes, current_design_id=current_design_id, designdetailslabels=labels)


@app.route("/get_labels", methods=['POST'])
@login_required
def get_labels():
    result = {'result': 'ERROR', 'msg': '', 'data': []}
    designid = request.form['design_id']
    designdetailslabels = db.session.query(DesignDetails.label_id).group_by(DesignDetails.label_id).filter(DesignDetails.design_id == designid).order_by(DesignDetails.label_id.asc()).all()
    if designdetailslabels is not None and len(designdetailslabels) > 0:
        result['result'] = 'SUCCESS'

        for designdetailslabel in designdetailslabels:
            label = db.session.query(DesignDetailsLabels.label, DesignDetailsLabels.label_num).filter(DesignDetailsLabels.id == designdetailslabel.label_id).first()
            if label is not None:
                json_obj = {
                    'label_id': designdetailslabel.label_id,
                    'label': label.label,
                    'label_num': label.label_num
                }
                result['data'].append(json_obj)

    return json.dumps(result)


@app.route("/set_labels", methods=['POST'])
@login_required
def set_labels():
    result = {'result': 'ERROR', 'msg': 'Operation failed'}
    value = request.form['value']

    try:
        json_data = json.loads(value)
        for tmp in json_data:
            label_split = tmp['label'].split(",")
            label = DesignDetailsLabels.query.filter(DesignDetailsLabels.id == tmp['label_id']).first()
            if label is not None:
                if label.label_num == len(label_split):
                    label.label = tmp['label']
                    db.session.commit()
        customfunc.add_activity(g.user.id, "Changed designdetails labels")
        result['result'] = 'SUCCESS'
    except Exception as e:
        print("set labels error", e)

    return json.dumps(result)


# #########################
@app.route("/get_all_mask_sets", methods=['POST'])
@login_required
def get_all_mask_sets():
    result = {'result': 'ERROR', 'msg': '', 'data': []}
    designs = Designs.query.order_by(Designs.date).all()

    designdetailslabels = db.session.query(DesignDetails.label_id, DesignDetails.design_id).group_by(DesignDetails.label_id, DesignDetails.design_id).order_by(DesignDetails.label_id.asc()).all()

    if designs is not None:
        result['result'] = 'SUCCESS'
        for design in designs:

            active = design.active
            if design.active is None:
                active = 0
            active_text = "Yes"
            if active == 0:
                active_text = "No"

            is_maldi = design.is_maldi
            if design.is_maldi is None:
                is_maldi = 0
            is_maldi_text = "Yes"
            if is_maldi == 0:
                is_maldi_text = "No"

            label_ids = ""
            for designdetailslabel in designdetailslabels:
                if designdetailslabel.design_id == design.id:
                    if label_ids == "":
                        label_ids = str(designdetailslabel.label_id)
                    else:
                        label_ids = label_ids + "," + str(designdetailslabel.label_id)

            json_obj = {
                "id": design.id,
                "block_type_id": design.block_type,
                "active": active,
                "protocol": design.protocol,
                "supplier": design.supplier,
                "x_origin": design.x_origin,
                "y_origin": design.y_origin,
                "feature_diameter": design.feature_diameter,
                "x_features": design.x_features,
                "x_spacing": design.x_spacing,
                "y_features": design.y_features,
                "y_spacing": design.y_spacing,
                "feature_num": design.feature_num,
                "column_num": design.mask_num,
                "date": design.date,
                "active_text": active_text,
                "is_maldi": is_maldi,
                "is_maldi_text": is_maldi_text,
                "labels": label_ids
            }
            result['data'].append(json_obj)
    return json.dumps(result)
# #########################


# get designs
@app.route("/get_designs", methods=['POST'])
@login_required
def get_designs():
    result = {'result': 'ERROR', 'msg': '', 'data': []}
    designs = Designs.query.order_by(Designs.date).all()
    if designs is not None:
        result['result'] = 'SUCCESS'
        for design in designs:
            active = design.active
            if design.active is None:
                active = 0
            json_obj = {
                "id": design.id,
                "protocol": design.protocol,
                "active": design.active,
                "date": design.date
            }
            result['data'].append(json_obj)
    return json.dumps(result)


# get design detail
@app.route("/get_design_detail", methods=['POST'])
@login_required
def get_design_detail():
    result = {'result': 'ERROR', 'msg': '', 'data': {}}
    design_id = request.form['design_id']
    b_get_detail = request.form['b_get_detail']

    design = db.session.query(Designs.id, Designs.protocol, Designs.supplier, Designs.block_type, BlockTypes.name.label("block_type_name"), Designs.x_origin, Designs.y_origin, Designs.feature_diameter, Designs.x_features, Designs.x_spacing, Designs.y_features, Designs.y_spacing, Designs.date, Designs.active, Designs.mask_num).outerjoin(BlockTypes, BlockTypes.id == Designs.block_type).filter(Designs.id == design_id).order_by(Designs.protocol).first()
    if design is not None:
        session['current_design_id'] = design_id

        result['result'] = 'SUCCESS'
        result['data']['block_type_id'] = design.block_type
        result['data']['block_type'] = design.block_type_name
        result['data']['protocol'] = design.protocol
        result['data']['supplier'] = design.supplier
        result['data']['x_origin'] = design.x_origin
        result['data']['y_origin'] = design.y_origin
        result['data']['feature_diameter'] = design.feature_diameter
        result['data']['x_features'] = design.x_features
        result['data']['x_spacing'] = design.x_spacing
        result['data']['y_features'] = design.y_features
        result['data']['y_spacing'] = design.y_spacing
        if design.active is None:
            result['data']['active'] = 0
        else:
            result['data']['active'] = design.active
        result['data']['mask_num'] = design.mask_num

        if b_get_detail == "1":
            result['data']['detail'] = []
            print("get desgin details start")
            design_details = DesignDetails.query.filter(DesignDetails.design_id == design_id).order_by(DesignDetails.col, DesignDetails.row, DesignDetails.feature).all()
            for design_detail in design_details:
                json_obj = {
                    'col': design_detail.col,
                    'row': design_detail.row,
                    'feature': design_detail.feature,
                    'mask': design_detail.mask
                }
                result['data']['detail'].append(json_obj)
            print("get desgin details end")
        else:
            result['data']['detail'] = None

    return json.dumps(result)


# add recipe
class AsyncAddDesign(object):
    def __init__(self, task_id, params, stream,  user_id, hostname):
        self.task_id = task_id
        self.params = params
        self.stream = stream
        self.user_id = user_id
        self.hostname = hostname

        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):
        result = {'result': 'ERROR', 'msg': 'Operation failed.'}
        _request = self.params

        protocol = _request['protocol']
        supplier = _request['supplier']
        block_type = _request['block_type']
        x_origin = _request['x_origin']
        y_origin = _request['y_origin']
        feature_diameter = _request['feature_diameter']
        x_features = _request['x_features']
        x_spacing = _request['x_spacing']
        y_features = _request['y_features']
        y_spacing = _request['y_spacing']
        active = _request['active']
        is_maldi = _request['is_maldi']

        task = Tasks.query.filter(Tasks.id == self.task_id).first()
        if task is None:
            return False

        design = Designs.query.filter(func.lower(Designs.protocol) == func.lower(protocol)).first()
        if design is not None:
            task.status = "Stopped"
            task.info = 'Duplicate: The protocl already exist.'
            db.session.commit()
            return False

        csv_input = csv.reader(self.stream)

        mask_num = 0
        feature_num = 0
        rowindex = 0
        colindex = 0
        for row in csv_input:
            if feature_num == 0:
                mask_num = len(row) - 3
                if mask_num <= 0:
                    task.status = "Stopped"
                    task.info = 'CSV file should have at least 1 mask set.'
                    db.session.commit()
                    return False

                if row[0].upper() == 'ROW':
                    rowindex = 0
                    colindex = 1
                else:
                    rowindex = 1
                    colindex = 0
            feature_num = feature_num + 1

        if feature_num > 0:
            feature_num = feature_num - 1
        else:
            task.status = "Stopped"
            task.info = 'CSV file should have at least 1 feature.'
            db.session.commit()
            return False

        design = Designs()
        try:
            design.protocol = protocol
            design.supplier = supplier
            design.block_type = block_type
            design.x_origin = x_origin
            design.y_origin = y_origin
            design.feature_diameter = feature_diameter
            design.x_features = x_features
            design.x_spacing = x_spacing
            design.y_features = y_features
            design.y_spacing = y_spacing
            design.active = active
            design.date = datetime.utcnow()
            design.mask_num = mask_num
            design.feature_num = feature_num
            design.is_maldi = is_maldi

            db.session.add(design)
            db.session.commit()

            self.stream.seek(0)
            index = 0

            print("started adding rows to design_details in add_design")
            task.status = 'Processing'
            task.info = '1'
            db.session.commit()

            label_id = 0
            label_str = ""
            label_num = 0
            for row in csv_input:
                if index == 0:
                    new_row = row[3:]
                    new_row_str = ','.join(new_row)

                    designdetailslabel = DesignDetailsLabels()
                    designdetailslabel.label_num = len(new_row)
                    designdetailslabel.label = new_row_str

                    db.session.add(designdetailslabel)
                    db.session.commit()
                    label_id = designdetailslabel.id
                    label_str = new_row_str
                    label_num = len(new_row)
                elif label_id > 0:
                    design_detail = DesignDetails()
                    design_detail.design_id = design.id
                    design_detail.label_id = label_id
                    design_detail.col = row[colindex]
                    design_detail.row = row[rowindex]

                    feature = int(float(row[2]))
                    design_detail.feature = feature

                    new_row = row[3:]
                    mask = ','.join(new_row)
                    design_detail.mask = mask

                    db.session.add(design_detail)

                if index % 50000 == 0:
                    db.session.commit()

                if index % 100 == 0:
                    sleep(0.001)

                if index % 1000 == 0:
                    percent = int(index * 100 / feature_num)
                    if percent == 0:
                        percent = 1
                    task.info = percent
                    db.session.commit()

                index = index + 1
            db.session.commit()

            print("ended adding rows to design_details in add_design")

            feature_num = DesignDetails.query.filter_by(design_id=design.id).count()
            design.feature_num = feature_num
            db.session.commit()

            result['id'] = design.id
            result['label_id'] = str(label_id)
            result['label_str'] = label_str
            result['label_num'] = label_num
            result['feature_num'] = feature_num
            result['column_num'] = mask_num
            result['date'] = design.date
            result['result'] = 'SUCCESS'
            result['msg'] = ''

            task.status = "Done"
            task.info = json.dumps(result)
            db.session.commit()

            customfunc.add_activity_hostname(self.user_id, 'Added new mask set("' + protocol + '")', self.hostname)
        except Exception as e:
            print("add design detail error:", e)

            task.status = "Stopped"
            task.info = str(e)
            db.session.commit()

        if self.stream is not None:
            self.stream.close()

        return False


# add design
@app.route("/add_design", methods=['POST'])
@login_required
def add_design():
    result = {'result': 'ERROR', 'msg': 'Operation failed.', 'id': ''}
    if g.user.design_editor == 0:
        result['msg'] = 'Permission denied'
        return json.dumps(result)

    if 'file' not in request.files:
        result['msg'] = 'No file part'
        return json.dumps(result)

    file = request.files['file']
    if file.filename == '':
        result['msg'] = 'No selected file'
        return json.dumps(result)

    if file.filename == '':
        result['msg'] = 'No selected file'
        return json.dumps(result)

    @copy_current_request_context
    def upload_design_file(taskid, user_id, host_name):
        f = request.files['file']
        stream = io.StringIO(f.stream.read().decode("UTF8"), newline=None)
        AsyncAddDesign(task_id=taskid, params=request.form, stream=stream, user_id=user_id, hostname=host_name)

    ipaddress = customfunc.get_ip_address()
    hostname = ''
    try:
        hostname = customfunc.get_host_name_by_ip(ipaddress)
    except Exception as e:
        hostname = customfunc.get_ip_address()

    task_id = new_task()
    task_status_url = url_for('task_status', task_id=task_id)

    task = Tasks.query.filter(Tasks.id == task_id).first()
    if task is not None:
        task.status = "Uploading"
        task.info = '0'
        db.session.commit()

    t = threading.Thread(target=upload_design_file, args=(task_id, g.user.id, hostname))
    t.start()

    result['result'] = 'SUCCESS'
    result['msg'] = ''
    result['task_status_url'] = task_status_url
    return json.dumps(result)


# add recipe
class AsyncUpdateDesign(object):
    def __init__(self, task_id, params, exist_file, stream,  user_id, hostname):
        self.task_id = task_id
        self.params = params
        self.exist_file = exist_file
        self.stream = stream
        self.user_id = user_id
        self.hostname = hostname

        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):
        result = {'result': 'ERROR', 'msg': 'Operation failed.'}
        _request = self.params

        design_id = _request['design_id']
        protocol = _request['protocol']
        supplier = _request['supplier']
        block_type = _request['block_type']
        block_type_text = _request['block_type_text']
        x_origin = _request['x_origin']
        y_origin = _request['y_origin']
        feature_diameter = _request['feature_diameter']
        x_features = _request['x_features']
        x_spacing = _request['x_spacing']
        y_features = _request['y_features']
        y_spacing = _request['y_spacing']
        active = _request['active']
        active_text = _request['active_text']
        is_maldi = _request['is_maldi']
        is_maldi_text = _request['is_maldi_text']
        is_append = _request['append']
        arg_label_id = _request['label_id']

        task = Tasks.query.filter(Tasks.id == self.task_id).first()
        if task is None:
            return False

        design = Designs.query.filter(Designs.id == design_id).first()
        if design is None:
            task.status = "Stopped"
            task.info = 'Mask Set does not exist'
            db.session.commit()
            return False

        feature_num = int(design.x_features) * int(design.y_features)
        if self.exist_file is False:
            try:
                log_str = ''
                if design.protocol != protocol:
                    log_str = 'protocol("' + protocol + '")'

                if design.supplier != supplier:
                    if log_str == '':
                        log_str = 'supplier("' + supplier + '")'
                    else:
                        log_str = log_str + ',' + 'supplier("' + supplier + '")'

                if design.block_type != int(block_type):
                    if log_str == '':
                        log_str = 'block type("' + block_type_text + '")'
                    else:
                        log_str = log_str + ',' + 'block type("' + block_type_text + '")'

                if design.x_origin != int(x_origin):
                    if log_str == '':
                        log_str = 'x origin("' + x_origin + '")'
                    else:
                        log_str = log_str + ',' + 'x origin("' + x_origin + '")'

                if design.y_origin != int(y_origin):
                    if log_str == '':
                        log_str = 'y origin("' + y_origin + '")'
                    else:
                        log_str = log_str + ',' + 'y origin("' + y_origin + '")'

                if design.feature_diameter != float(feature_diameter):
                    if log_str == '':
                        log_str = 'feature diameter("' + feature_diameter + '")'
                    else:
                        log_str = log_str + ',' + 'feature diameter("' + feature_diameter + '")'

                if design.x_features != int(x_features):
                    if log_str == '':
                        log_str = 'x features("' + x_features + '")'
                    else:
                        log_str = log_str + ',' + 'x features("' + x_features + '")'

                if design.x_spacing != float(x_spacing):
                    if log_str == '':
                        log_str = 'x spacing("' + x_spacing + '")'
                    else:
                        log_str = log_str + ',' + 'x spacing("' + x_spacing + '")'

                if design.y_features != int(y_features):
                    if log_str == '':
                        log_str = 'y features("' + y_features + '")'
                    else:
                        log_str = log_str + ',' + 'y features("' + y_features + '")'

                if design.y_spacing != float(y_spacing):
                    if log_str == '':
                        log_str = 'y spacing("' + y_spacing + '")'
                    else:
                        log_str = log_str + ',' + 'y spacing("' + y_spacing + '")'

                if design.is_maldi != int(is_maldi):
                    if log_str == '':
                        log_str = 'maldi("' + is_maldi_text + '")'
                    else:
                        log_str = log_str + ',' + 'maldi("' + is_maldi_text + '")'

                if design.active != int(active):
                    if log_str == '':
                        log_str = 'active("' + active_text + '")'
                    else:
                        log_str = log_str + ',' + 'active("' + active_text + '")'

                design.protocol = protocol
                design.supplier = supplier
                design.block_type = block_type
                design.x_origin = x_origin
                design.y_origin = y_origin
                design.feature_diameter = feature_diameter
                design.x_features = x_features
                design.x_spacing = x_spacing
                design.y_features = y_features
                design.y_spacing = y_spacing
                design.is_maldi = is_maldi
                design.active = active
                db.session.commit()

                if log_str != '':
                    customfunc.add_activity_hostname(self.user_id, 'Changed ' + log_str + ' on Mask Set("' + design.protocol + '")', self.hostname)

                result['result'] = 'SUCCESS'
                result['msg'] = ''
                result['label_id'] = "0"
                result['feature_num'] = design.feature_num
                result['column_num'] = design.mask_num
                result['msg'] = ''

                task.status = "Done"
                task.info = json.dumps(result)
                db.session.commit()
                return False
            except Exception as e:
                task.status = "Stopped"
                task.info = str(e)
                db.session.commit()

            return False

        csv_input = csv.reader(self.stream)

        mask_num = 0
        feature_num = 0
        rowindex = 0
        colindex = 0

        for row in csv_input:
            if feature_num == 0:
                mask_num = len(row) - 3

                if mask_num <= 0:
                    task.status = "Stopped"
                    task.info = 'CSV file should have at least 1 mask set.'
                    db.session.commit()
                    return False

                if row[0].upper() == 'ROW':
                    rowindex = 0
                    colindex = 1
                else:
                    rowindex = 1
                    colindex = 0
            feature_num = feature_num + 1

        if feature_num > 0:
            feature_num = feature_num - 1
        else:
            task.status = "Stopped"
            task.info = 'CSV file should have at least 1 feature.'
            db.session.commit()
            return False

        try:

            log_str = ''
            if design.protocol != protocol:
                log_str = 'protocol("' + protocol + '")'

            if design.supplier != supplier:
                if log_str == '':
                    log_str = 'supplier("' + supplier + '")'
                else:
                    log_str = log_str + ',' + 'supplier("' + supplier + '")'

            if design.block_type != int(block_type):
                if log_str == '':
                    log_str = 'block type("' + block_type_text + '")'
                else:
                    log_str = log_str + ',' + 'block type("' + block_type_text + '")'

            if design.x_origin != int(x_origin):
                if log_str == '':
                    log_str = 'x origin("' + x_origin + '")'
                else:
                    log_str = log_str + ',' + 'x origin("' + x_origin + '")'

            if design.y_origin != int(y_origin):
                if log_str == '':
                    log_str = 'y origin("' + y_origin + '")'
                else:
                    log_str = log_str + ',' + 'y origin("' + y_origin + '")'

            if design.feature_diameter != float(feature_diameter):
                if log_str == '':
                    log_str = 'feature diameter("' + feature_diameter + '")'
                else:
                    log_str = log_str + ',' + 'feature diameter("' + feature_diameter + '")'

            if design.x_features != int(x_features):
                if log_str == '':
                    log_str = 'x features("' + x_features + '")'
                else:
                    log_str = log_str + ',' + 'x features("' + x_features + '")'

            if design.x_spacing != float(x_spacing):
                if log_str == '':
                    log_str = 'x spacing("' + x_spacing + '")'
                else:
                    log_str = log_str + ',' + 'x spacing("' + x_spacing + '")'

            if design.y_features != int(y_features):
                if log_str == '':
                    log_str = 'y features("' + y_features + '")'
                else:
                    log_str = log_str + ',' + 'y features("' + y_features + '")'

            if design.y_spacing != float(y_spacing):
                if log_str == '':
                    log_str = 'y spacing("' + y_spacing + '")'
                else:
                    log_str = log_str + ',' + 'y spacing("' + y_spacing + '")'

            if design.active != int(active):
                if log_str == '':
                    log_str = 'active("' + active_text + '")'
                else:
                    log_str = log_str + ',' + 'active("' + active_text + '")'

            if design.active != int(active):
                if log_str == '':
                    log_str = 'active("' + active_text + '")'
                else:
                    log_str = log_str + ',' + 'active("' + active_text + '")'

            if is_append == '1':
                if design.x_features != int(x_features):
                    task.status = "Stopped"
                    task.info = 'X Features should be same as the already existing one.'
                    db.session.commit()
                    return False

                if design.y_features != int(y_features):
                    task.status = "Stopped"
                    task.info = 'Y Features should be same as the already existing one.'
                    db.session.commit()
                    return False

                if design.mask_num is None or mask_num > design.mask_num:
                    design.mask_num = mask_num

                if design.feature_num is None or feature_num > design.feature_num:
                    design.feature_num = feature_num
            else:
                design.mask_num = mask_num
                design.feature_num = feature_num

            design.protocol = protocol
            design.supplier = supplier
            design.block_type = block_type
            design.x_origin = x_origin
            design.y_origin = y_origin
            design.feature_diameter = feature_diameter
            design.x_features = x_features
            design.x_spacing = x_spacing
            design.y_features = y_features
            design.y_spacing = y_spacing
            design.is_maldi = is_maldi
            design.active = active

            db.session.commit()

            if is_append == '0':
                # get designdetailslabels
                labels = db.session.query(DesignDetails.label_id).group_by(DesignDetails.label_id).filter(DesignDetails.design_id == design_id).all()

                # delete designdetails
                DesignDetails.query.filter(DesignDetails.design_id == design.id).delete()

                # delete designdetailslabel
                for label in labels:
                    DesignDetailsLabels.query.filter(DesignDetailsLabels.id == label.label_id).delete()

                db.session.commit()

            self.stream.seek(0)

            print("started adding rows to designdetails in update_design")

            task.status = 'Processing'
            task.info = '1'
            db.session.commit()

            label_id = 0
            label_str = ""
            label_num = 0

            index = 0
            for row in csv_input:
                if index == 0:
                    if arg_label_id == "0":
                        new_row = row[3:]
                        new_row_str = ','.join(new_row)

                        designdetailslabel = DesignDetailsLabels()
                        designdetailslabel.label_num = len(new_row)
                        designdetailslabel.label = new_row_str

                        db.session.add(designdetailslabel)
                        db.session.commit()
                        label_id = designdetailslabel.id
                        label_str = new_row_str
                        label_num = len(new_row)

                    else:
                        designdetailslabel = DesignDetailsLabels.query.filter(DesignDetailsLabels.id == arg_label_id).first()
                        if designdetailslabel is not None:
                            label_str = designdetailslabel.label
                            label_num = designdetailslabel.label_num
                            label_id = designdetailslabel.id
                        else:
                            label_id = 0

                elif label_id > 0:
                    design_detail = None
                    if int(arg_label_id) > 0:
                        design_detail = DesignDetails.query.filter(DesignDetails.design_id == design.id, DesignDetails.label_id == label_id, DesignDetails.col == row[colindex], DesignDetails.row == row[rowindex]).first()
                    if design_detail is None:
                        design_detail = DesignDetails()
                        db.session.add(design_detail)

                    design_detail.design_id = design.id
                    design_detail.label_id = label_id
                    design_detail.col = row[colindex]
                    design_detail.row = row[rowindex]

                    feature = int(float(row[2]))
                    design_detail.feature = feature

                    new_row = row[3:]
                    mask = ','.join(new_row)
                    design_detail.mask = mask

                if index % 30000 == 0:
                    db.session.commit()

                if index % 100 == 0:
                    sleep(0.001)

                if index % 1000 == 0:
                    percent = int(index*100/feature_num)
                    if percent == 0:
                        percent = 1
                    task.info = percent
                    db.session.commit()

                index = index + 1

            db.session.commit()

            print("ended adding rows to designdetails in update_design")

            if log_str != '':
                customfunc.add_activity_hostname(self.user_id, 'Changed ' + log_str + ' on Mask Set("' + design.protocol + '")', self.hostname)

            designdetailslabels = db.session.query(DesignDetails.label_id).group_by(DesignDetails.label_id).filter(DesignDetails.design_id == design_id).order_by(DesignDetails.label_id.asc()).all()
            feature_num = 0
            for designdetailslabel in designdetailslabels:
                tmp_feature_num = DesignDetails.query.filter_by(design_id=design_id, label_id=designdetailslabel.label_id).count()
                if tmp_feature_num > feature_num:
                    feature_num = tmp_feature_num

            design.feature_num = feature_num
            db.session.commit()

            result['msg'] = ''
            result['result'] = 'SUCCESS'
            result['label_id'] = str(label_id)
            result['label_str'] = label_str
            result['label_num'] = label_num
            result['feature_num'] = feature_num
            result['column_num'] = mask_num

            if self.stream is not None:
                self.stream.close()

            task.status = "Done"
            task.info = json.dumps(result)
            db.session.commit()
            return False
        except Exception as e:
            print('update mask set detail error:', e)
            task.status = "Stopped"
            task.info = str(e)
            db.session.commit()

        if self.stream is not None:
            self.stream.close()

        return False


# Update designs
@app.route("/update_design", methods=['POST'])
@login_required
def update_design():
    result = {'result': 'FAIL', 'msg': 'Operation failed.'}
    if g.user.design_editor == 0:
        result['msg'] = 'Permission denied'
        return json.dumps(result)

    @copy_current_request_context
    def upload_design_file2(taskid, user_id, host_name):
        f = request.files['file']
        stream = io.StringIO(f.stream.read().decode("UTF8"), newline=None)
        AsyncUpdateDesign(task_id=taskid, params=request.form, exist_file=True, stream=stream, user_id=user_id, hostname=host_name)

    exist_file = True
    file = None
    if 'file' not in request.files:
        exist_file = False
    else:
        file = request.files['file']
        if file.filename == '':
            exist_file = False

    ipaddress = customfunc.get_ip_address()
    hostname = ''
    try:
        hostname = customfunc.get_host_name_by_ip(ipaddress)
    except Exception as e:
        hostname = customfunc.get_ip_address()

    task_id = new_task()
    task_status_url = url_for('task_status', task_id=task_id)

    if exist_file is False:
        AsyncUpdateDesign(task_id=task_id, params=request.form, exist_file=exist_file, stream=None, user_id=g.user.id, hostname=hostname)
    else:
        task = Tasks.query.filter(Tasks.id == task_id).first()
        if task is not None:
            task.status = "Uploading"
            task.info = '0'
            db.session.commit()

        t = threading.Thread(target=upload_design_file2, args=(task_id, g.user.id, hostname, ))
        t.start()

    result['result'] = 'SUCCESS'
    result['msg'] = ''
    result['task_status_url'] = task_status_url
    return json.dumps(result)


# delete design
@app.route("/delete_design", methods=['POST'])
@login_required
def delete_design():
    result = {'result': 'ERROR', 'msg': ''}
    design_id = request.form['design_id']

    try:
        # delete Recipes related to this design
        recipes = RecipeHeaders.query.filter(RecipeHeaders.design_id == design_id).all()
        for recipe in recipes:
            RecipeDetails.query.filter(RecipeDetails.recipe_id == recipe.id).delete()
        RecipeHeaders.query.filter(RecipeHeaders.design_id == design_id).delete()

        # delete Maldi Recipes related to this design
        maldi_recipes = MaldiRecipeHeaders.query.filter(MaldiRecipeHeaders.design_id == design_id).all()
        for maldi_recipe in maldi_recipes:
            MaldiRecipeDetails.query.filter(MaldiRecipeDetails.recipe_id == maldi_recipe.id).delete()
        MaldiRecipeHeaders.query.filter(MaldiRecipeHeaders.design_id == design_id).delete()

        # get designdetailslabels
        labels = db.session.query(DesignDetails.label_id).group_by(DesignDetails.label_id).filter(DesignDetails.design_id == design_id).all()

        # delete design
        DesignDetails.query.filter(DesignDetails.design_id == design_id).delete()
        Designs.query.filter(Designs.id == design_id).delete()

        # delete designdetailslabel
        for label in labels:
            DesignDetailsLabels.query.filter(DesignDetailsLabels.id == label.label_id).delete()

        db.session.commit()

        result['result'] = 'SUCCESS'
    except exc.SQLAlchemyError as e:
        result['msg'] = 'Operation Failed.'
        print("Delete Design error:", e)

    return json.dumps(result)
