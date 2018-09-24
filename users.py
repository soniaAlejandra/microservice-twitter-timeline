import os
import copy
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy import exc, orm

import sys

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////' + \
    os.path.join(basedir, 'app.sqlite')
app.config['SQLALCHEMY_MIGRATE_REPO'] = os.path.join(basedir, 'db_repository')

db = SQLAlchemy(app)
ma = Marshmallow(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(20), unique=True)
    full_name = db.Column(db.String(80))
    followers = db.Column(db.String())
    following = db.Column(db.String())
    short_bio = db.Column(db.String(140))

    def __init__(self, login, full_name, short_bio):
        self.login = login
        self.full_name = full_name
        self.followers = ''
        self.following = ''
        self.short_bio = short_bio


class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'login', 'full_name', 'followers', 'following', 'short_bio')


user_schema = UserSchema()
user_schemas = UserSchema(many=True)

db.create_all()

def validate_required(required_elements, request):
    contain_required_elements = True
    
    for field in required_elements:
        contain_required_elements = contain_required_elements and field in request.json
    
    if not request.json or not contain_required_elements:
        errorMessage = {}

        for field in required_elements:
            if(not field in request.json):
                errorMessage[field] = '%s is required' % field

        return jsonify({ 'type': 'REQUIRED', 'error': errorMessage, 'description': 'Please fill all the required fields' }), 400

    return None

def validate_data(fields, request):
    error = {}
    for field in fields:
        if(len(request.json[field[0]]) > field[1]):
            error[field[0]] = '%s can not be larger than %d characters' % (field[0], field[1])

    if(error):
        return jsonify({ 'type': 'LIMIT', 'description': 'Field is beyond the character limit', 'error': error }), 400
    return None

def string_to_array(string):
    array = string.split(';')
    array.pop()
    return array

def format_user_data(user):
    formatedUser = copy.deepcopy(user)
    
    formatedUser['following'] = string_to_array(user['following'])
    formatedUser['followers'] = string_to_array(user['followers'])

    return formatedUser

@app.route('/')
def list_users():
    all_users = User.query.all()
    result = user_schemas.dump(all_users)
    formated_data = []

    for user in result.data:
        formated_data.append(format_user_data(user))

    return jsonify({'users': formated_data}), 200


@app.route('/', methods=['POST'])
def create_user():

    requiredError = validate_required(['login', 'full_name'], request)
    if(requiredError): return requiredError
    
    dataError = validate_data([('login',20), ('full_name',80), ('short_bio',140)], request)
    if(dataError): return dataError

    login = request.json['login']
    full_name = request.json['full_name']
    short_bio = request.json.get('short_bio', '')

    try:
        new_user = User(login, full_name, short_bio)
        db.session.add(new_user)
        db.session.commit()

        new_user = user_schema.dump(new_user)
        formated_data = format_user_data(new_user.data)
        return jsonify({ 'user': formated_data }), 201

    except exc.IntegrityError as e:
        db.session.rollback()
        return jsonify({ 'type': 'UNIQUE', 'description': 'Field should be unique', 'error': ['username'] }), 409

    
    except Exception as e:
        db.session.rollback()
        print('Error:', e)
        return jsonify({ 'type': 'UNKNOWN', 'description': 'An unknown error was detected'}), 500

@app.route('/<id>', methods=['GET'])
def get_user(id):
    try:
        user = User.query.get(id)
        if(not user):
            return jsonify({ 'type': 'NOT_EXISTS', 'description': 'User <%s> does not exist' % id }), 404

        formated_data = user_schema.dump(user)
        formated_data = format_user_data(formated_data.data)

        return jsonify({'user': formated_data}), 200
    
    except Exception as e:
        db.session.rollback()
        print('Error:', e)
        return jsonify({ 'type': 'UNKNOWN', 'description': 'An unknown error was detected'}), 500

@app.route('/<id>', methods=['DELETE'])
def remove_user(id):
    try:
        user = User.query.get(id)
        
        all_users = User.query.all()
        dumped_users = user_schemas.dump(all_users)
        dumped_users = dumped_users.data
        
        print(dumped_users)

        for i in range(0,len(all_users)):
            print('user', dumped_users[i])
            if(id in dumped_users[i]['following']):
                following = string_to_array(dumped_users[i]['following'])
                following.remove(str(id))
                all_users[i].following = ''.join([str(f) + ';' for f in following])
            if(id in dumped_users[i]['followers']):
                followers = string_to_array(dumped_users[i]['followers'])
                followers.remove(str(id))
                all_users[i].followers = ''.join([str(f) + ';' for f in followers])      
        
        db.session.delete(user)

        db.session.commit()

        return jsonify({ 'description': 'User <%s> was deleted' % id })

    except orm.exc.UnmappedInstanceError as e:
        db.session.rollback()
        return jsonify({ 'type': 'NOT_EXISTS', 'description': 'User <%s> does not exist' % id }), 404

    
    except Exception as e:
        db.session.rollback()
        print('Error:', e)
        return jsonify({ 'type': 'UNKNOWN', 'description': 'An unknown error was detected'}), 500


@app.route('/<id>/follow', methods=['PUT'])
def follow(id):
    requiredError = validate_required(['follow_user'], request)
    if(requiredError): return requiredError

    try:
        user = User.query.get(id)
        user_to_follow = User.query.get(request.json['follow_user'])
        
        if(not user_to_follow):
            return jsonify({ 'type': 'NOT_EXISTS', 'description': 'Unable to follow, User <%s> does not exist' % request.json['follow_user']}), 404
        
        user_data = user_schema.dump(user)
        user_data = user_data.data
        formated_data = format_user_data(user_data)

        user_to_follow_data = user_schema.dump(user_to_follow)
        user_to_follow_data = user_to_follow_data.data

        follow_user = str(request.json['follow_user'])
        
        if(follow_user not in formated_data['following']):
            user.following = user_data['following'] + follow_user + ';'
            user_to_follow.followers = user_to_follow_data['followers'] + str(id) + ';'
            db.session.commit()

            return jsonify({}), 204

        else:
            return jsonify({ 'type': 'INVALID', 'description': 'User <%s> already follows User <%s>' % (id, follow_user) }), 400

    except orm.exc.UnmappedInstanceError as e:
        db.session.rollback()
        return jsonify({ 'type': 'NOT_EXISTS', 'description': 'User <%s> does not exist' % id }), 404

    
    except Exception as e:
        db.session.rollback()
        print('Error:', e)
        return jsonify({ 'type': 'UNKNOWN', 'description': 'An unknown error was detected'}), 500

@app.route('/<id>/unfollow', methods=['PUT'])
def unfollow(id):
    requiredError = validate_required(['unfollow_user'], request)
    if(requiredError): return requiredError

    try:
        user = User.query.get(id)
        user_to_unfollow = User.query.get(request.json['unfollow_user'])
        
        if(not user_to_unfollow):
            return jsonify({ 'type': 'NOT_EXISTS', 'description': 'Unable to unfollow, User <%s> does not exist' % request.json['unfollow_user']}), 404
        
        user_data = user_schema.dump(user)
        user_data = user_data.data
        formated_data = format_user_data(user_data)

        user_to_unfollow_data = user_schema.dump(user_to_unfollow)
        user_to_unfollow_data = user_to_unfollow_data.data
        unfollow_formated_data = format_user_data(user_to_unfollow_data)

        unfollow_id = str(request.json['unfollow_user'])
        
        if(unfollow_id in formated_data['following']):
            formated_data['following'].remove(unfollow_id)
            user.following = ''.join([str(f) + ';' for f in formated_data['following']])
            unfollow_formated_data['followers'].remove(str(id))
            user_to_unfollow.followers = ''.join([str(f) + ';' for f in unfollow_formated_data['followers']])
            db.session.commit()

            return jsonify({}), 204

        else:
            return jsonify({ 'type': 'INVALID', 'description': 'User <%s> does not follow User <%s>' % (id, unfollow_id) }), 400

    except orm.exc.UnmappedInstanceError as e:
        db.session.rollback()
        return jsonify({ 'type': 'NOT_EXISTS', 'description': 'User <%s> does not exist' % id }), 404

    
    except Exception as e:
        db.session.rollback()
        print('Error:', e)
        return jsonify({ 'type': 'UNKNOWN', 'description': 'An unknown error was detected'}), 500

    
if __name__ == '__main__':
    app.run()
