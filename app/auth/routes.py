from flask_jwt_extended.utils import set_access_cookies
from ..decorators import admin_required
from flask_cors import cross_origin
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from .errors import unauthorized, bad_request, forbidden, not_found
from flask_jwt_extended import jwt_required
from flask import json, request, jsonify
from ..email import send_email, send_recovery_email
from ..models import User
from .. import db
from . import auth


@auth.post('/login')
@cross_origin()
def login():
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    user = User.query.filter_by(username=username).first()
    if user is not None and user.verify_password(password):
        user.ping()
        access_token = create_access_token(identity=user.username)
        response = jsonify({'current_user': {
                            'username': user.username,
                            'role': f'{user.role.name}',
                            'status': user.status,
                            'is_first_login': user.is_first_login
                            },
                        'access_token': access_token})
        set_access_cookies(response, access_token)
        return response
    return unauthorized('Credenciais inválidas.')

@auth.post('/register')
def register():
    user = request.json.get('user', None)
    personal = request.json.get('personal', None)
    cellphone = personal['phone']
    phone_number = f'{cellphone["area"]}{cellphone["number"]}'
    address = personal['address']
    payment = request.json.get('payment', None)
    motorcycle = request.json.get('motorcycle', None)
    try:
        new_user = User(username=user['username'], password=user['password'],
                    name=personal['name'], birth_date=personal['birth_date'], email=personal['email'],
                    cpf=personal['cpf'], rg=personal['rg'], cellphone=phone_number,
                    state=address['state'], city=address['city'], street=address['street'],
                    number=address['number'], zipcode=address['zipcode'], district=address['district'],
                    bank=payment['bank_code'], bank_number=payment['number'], agency=payment['agency_code'],
                    motor_brand=motorcycle['brand'], motor_model=motorcycle['model'], motor_year=motorcycle['year'])
        db.session.add(new_user)
        db.session.commit()
        try:
            send_email(subject='Seja bem-vindo!', to=personal['email'],
                        username=user['username'], password=user['password'])
        except Exception as err:
            print(err)
        return jsonify({'status': 'Success',
                        'user': str(new_user.username)
                        }), 200
    except:
        return bad_request('Invalid arguments')

@auth.delete('/user/delete')
@jwt_required()
@admin_required
def delete():
    username = request.json.get('username', None)
    try:
        user = User.query.filter_by(username=username).first()
        db.session.delete(user)
        db.session.commit()
        return jsonify('User has been removed successfully'), 200
    except:
        return not_found('User not found')

@auth.post('/forgot-password')
def forgot_password():
    email = request.json.get('email', None)
    user = User.query.filter_by(email=email).first()
    if user:
        #send_recovery_email(user)
        return jsonify(user.get_reset_token())
    return jsonify('Usuário não encontrado')

@auth.post('/verify-token')
def verify_password():
    token = request.json.get('token', None)
    user = User.verify_reset_token(token=token)
    if not user:
        return not_found('Link inválido. Usuário não encontrado')
    password = request.json.get('new_password', None)
    confirm_password = request.json.get('new_password_confirm', None)
    if password != confirm_password:
        return forbidden('As senhas devem ser iguais.')
    user.password = password
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'Senha alterada com sucesso!', 'status': 200})
 
@auth.post('/change-password')
@jwt_required()
def change_password():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    current_password = request.json.get('current_password', None)
    new_password = request.json.get('new_password', None)
    new_password_confirm = request.json.get('new_password_confirm', None)
    if user is not None and user.verify_password(current_password):
        if new_password != new_password_confirm:
            return forbidden('As senhas devem ser iguais.')
        user.password = new_password
        user.is_first_login = False
        db.session.add(user)
        db.session.commit()
        return jsonify({'message': 'Senha alterada com sucesso!', 'status': 200})
    return forbidden('O usuário necessita estar logado.')