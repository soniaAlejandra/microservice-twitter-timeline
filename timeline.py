import os
import copy
from flask import Flask, request, jsonify
import sys
import requests

app = Flask(__name__)

@app.route('/<id>/post', methods=['GET'])
def post_timeline(id):
    r                 = requests.get('http://messages-tpes2.herokuapp.com/')
    mensagens         = r.json()
    mensagens_usuario = []
    
    for mensagem in range(len(mensagens['messages'])):
        if mensagens['messages'][mensagem]['user_id'] == int(id):
            mensagens_usuario.append(mensagens['messages'][mensagem]['message'])
    return jsonify({ 'messages': mensagens_usuario }), 200


@app.route('/<id>/home', methods=['GET'])
def home_timeline(id):
    r                  = requests.get('http://messages-tpes2.herokuapp.com/')
    mensagens          = r.json()
    r                  = requests.get('https://twitter-eng2-users.herokuapp.com/')
    usuarios           = r.json()
    mensagens_usuarios = []
    
    for mensagem in range(len(mensagens['messages'])):
        if mensagens['messages'][mensagem]['user_id'] == int(id):
            mensagens_usuarios.append(mensagens['messages'][mensagem]['message'])
    
    for usuario in range(len(usuarios['users'])):
        if usuarios['users'][usuario]['id'] == int(id):
            for id_amigo in usuarios['users'][usuario]['following']:
                for mensagem in range(len(mensagens['messages'])):
                    if mensagens['messages'][mensagem]['user_id'] == int(id_amigo):
                        mensagens_usuarios.append(mensagens['messages'][mensagem]['message'])
    return jsonify({ 'messages': mensagens_usuarios }), 200    


if __name__ == '__main__':
    app.run()
