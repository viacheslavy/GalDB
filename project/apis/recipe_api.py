from flask import Flask, request, json
from flask_restful import Resource, Api
from project.models import *
from project.views import app
from project import config

api = Api(app)


class Recipes(Resource):
    def get(self):
        result = {'result': 'ERROR', 'data': []}
        token = ''
        if 'token' in request.args:
            token = request.args['token']

        if token != config.API_TOKEN:
            result['msg'] = 'token invalid'
            return json.jsonify(result)

        recipes = db.session.query(RecipeHeaders.id, RecipeHeaders.name, RecipeHeaders.notes, RecipeHeaders.design_id, RecipeHeaders.date, RecipeHeaders.userid, RecipeHeaders.mask_list, Designs.protocol, Designs.mask_num, RecipeHeaders.active).outerjoin(Designs, Designs.id == RecipeHeaders.design_id).order_by(RecipeHeaders.date.desc(), RecipeHeaders.name.asc(), ).all()
        if recipes is not None:
            result['result'] = 'SUCCESS'
            for recipe in recipes:
                json_obj = {
                    "active": recipe.active,
                    'date': recipe.date,
                    "mask_num": recipe.mask_num,
                    "mask_list": recipe.mask_list,
                    "notes": recipe.notes,
                    "design_name": recipe.protocol,
                    "design_id": recipe.design_id,
                    'user_id': recipe.userid,
                    'name': recipe.name,
                    'id': recipe.id
                }
                result['data'].append(json_obj)

        return json.jsonify(result)


class Recipes_Detail(Resource):
    def get(self, recipe_id):
        result = {'result': 'ERROR', 'data': []}
        token = ''
        if 'token' in request.args:
            token = request.args['token']

        if token != config.API_TOKEN:
            result['msg'] = 'token invalid'
            return json.jsonify(result)

        recipe = db.session.query(RecipeHeaders.id, RecipeHeaders.name, RecipeHeaders.notes, RecipeHeaders.design_id, RecipeHeaders.date, RecipeHeaders.userid, RecipeHeaders.mask_list, Designs.protocol, Designs.mask_num, RecipeHeaders.active).outerjoin(Designs, Designs.id == RecipeHeaders.design_id).filter(RecipeHeaders.id == recipe_id).first()
        if recipe is not None:
            result['result'] = 'SUCCESS'
            json_obj = {
                "active": recipe.active,
                'date': recipe.date,
                "mask_num": recipe.mask_num,
                "mask_list": recipe.mask_list,
                "notes": recipe.notes,
                "design_name": recipe.protocol,
                "design_id": recipe.design_id,
                'user_id': recipe.userid,
                'name': recipe.name,
                'id': recipe.id
            }
            result['data'].append(json_obj)
        else:
            result['msg'] = 'Recipe not found'
        return json.jsonify(result)


api.add_resource(Recipes, '/apis/recipes')
api.add_resource(Recipes_Detail, '/apis/recipe/<recipe_id>')
