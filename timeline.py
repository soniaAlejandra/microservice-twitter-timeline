import os
import copy
from flask import Flask, request, jsonify
import sys
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def checaUsuarioExistente(id):
    try:
        usuario = requests.get('https://twitter-eng2-users.herokuapp.com/'+id)
        
        if usuario.status_code == 404: return 404
    except Exception as e: return 500

@app.route('/<id>/post', methods=['GET'])
def post_timeline(id):
    if checaUsuarioExistente(id) == 404:
        return jsonify({ 'type': 'NOT_EXISTS', 'description': 'User <%s> does not exist' % id }), 404
    else:
        if checaUsuarioExistente(id) == 500:
            return jsonify({ 'type': 'UNKNOWN', 'description': 'An unknown error was detected'}), 500

    r                 = requests.get('http://messages-twitter.herokuapp.com/')
    mensagens         = r.json()
    mensagens_usuario = []
    
    for mensagem in range(len(mensagens['messages'])):
        if mensagens['messages'][mensagem]['user_id'] == int(id):
            mensagens_usuario.append({ 'mensagem': mensagens['messages'][mensagem]['message'], 'id': id})
    return jsonify({ 'messages': mensagens_usuario }), 200


@app.route('/<id>/home', methods=['GET'])
def home_timeline(id):
    if checaUsuarioExistente(id) == 404:
        return jsonify({ 'type': 'NOT_EXISTS', 'description': 'User <%s> does not exist' % id }), 404
    else:
        if checaUsuarioExistente(id) == 500:
            return jsonify({ 'type': 'UNKNOWN', 'description': 'An unknown error was detected'}), 500

    r                  = requests.get('http://messages-twitter.herokuapp.com/')
    mensagens          = r.json()
    r                  = requests.get('https://twitter-eng2-users.herokuapp.com/')
    usuarios           = r.json()
    mensagens_usuarios = []    
    for mensagem in range(len(mensagens['messages'])):
        if mensagens['messages'][mensagem]['user_id'] == int(id):
            mensagens_usuarios.append({'mensagem': mensagens['messages'][mensagem]['message'], 'id': id})
    
    for usuario in range(len(usuarios['users'])):
        if usuarios['users'][usuario]['id'] == int(id):
            for id_amigo in usuarios['users'][usuario]['following']:
                if checaUsuarioExistente(id) == 404:
                    return jsonify({ 'type': 'NOT_EXISTS', 'description': 'User <%s> does not exist' % id }), 404
                else: 
                    if checaUsuarioExistente(id) == 500:
                        return jsonify({ 'type': 'UNKNOWN', 'description': 'An unknown error was detected'}), 500
                for mensagem in range(len(mensagens['messages'])):
                    if mensagens['messages'][mensagem]['user_id'] == int(id_amigo):
                        mensagens_usuarios.append({'mensagem': mensagens['messages'][mensagem]['message'], 'id': id_amigo})
    return jsonify({ 'messages': mensagens_usuarios }), 200    


if __name__ == '__main__':
    app.run()
