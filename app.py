from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime
import secrets

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

# Configuração Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.seu_email.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'seu_email@dominio.com'
app.config['MAIL_PASSWORD'] = 'sua_senha'
mail = Mail(app)

# Banco de dados SQLite
DB_NAME = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# ======== Rota de Login ========
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user['senha'], senha):
            session['user_id'] = user['id']
            session['user_nome'] = user['nome']
            return redirect(url_for('index'))
        else:
            flash('E-mail ou senha incorretos.', 'danger')

    return render_template('login.html')

# ======== Rota de Registro ========
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = generate_password_hash(request.form['senha'])

        conn = get_db_connection()
        conn.execute("INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)", (nome, email, senha))
        conn.commit()
        conn.close()

        flash('Cadastro realizado com sucesso!', 'success')
        return redirect(url_for('login'))

    return render_template('registro.html')

# ======== Rota de Logout ========
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ======== Página Principal (Calendário) ========
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', user_nome=session.get('user_nome'))

# ======== Agendar Novo Evento ========
@app.route('/agendar', methods=['GET', 'POST'])
def agendar():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    clientes = conn.execute("SELECT * FROM clientes WHERE usuario_id = ?", (session['user_id'],)).fetchall()

    if request.method == 'POST':
        cliente_id = request.form['cliente_id']
        titulo = request.form['titulo']
        data = request.form['data']
        hora = request.form['hora']
        descricao = request.form['descricao']

        conn.execute(
            "INSERT INTO agendamentos (usuario_id, cliente_id, titulo, data, hora, descricao) VALUES (?, ?, ?, ?, ?, ?)",
            (session['user_id'], cliente_id, titulo, data, hora, descricao)
        )
        conn.commit()
        conn.close()
        flash('Agendamento criado com sucesso!', 'success')
        return redirect(url_for('lista_agendamentos'))

    conn.close()
    return render_template('agendar.html', clientes=clientes)

# ======== Lista de Agendamentos ========
@app.route('/lista_agendamentos')
def lista_agendamentos():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    agendamentos = conn.execute(
        "SELECT a.*, c.nome AS cliente_nome FROM agendamentos a LEFT JOIN clientes c ON a.cliente_id = c.id WHERE a.usuario_id = ? ORDER BY a.data, a.hora",
        (session['user_id'],)
    ).fetchall()
    conn.close()
    return render_template('lista_agendamentos.html', agendamentos=agendamentos)

# ======== Cadastro e Listagem de Clientes ========
@app.route('/clientes', methods=['GET', 'POST'])
def clientes():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()

    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        telefone = request.form['telefone']

        conn.execute(
            "INSERT INTO clientes (usuario_id, nome, email, telefone) VALUES (?, ?, ?, ?)",
            (session['user_id'], nome, email, telefone)
        )
        conn.commit()
        flash('Cliente cadastrado com sucesso!', 'success')

    clientes = conn.execute(
        "SELECT * FROM clientes WHERE usuario_id = ?", 
        (session['user_id'],)
    ).fetchall()

    conn.close()
    return render_template('clientes.html', clientes=clientes)

# ======== Suporte ========
@app.route('/suporte', methods=['GET', 'POST'])
def suporte():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        assunto = request.form['assunto']
        mensagem = request.form['mensagem']

        # Envia e-mail
        msg = Message(subject=f"Suporte: {assunto}",
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[app.config['MAIL_USERNAME']],
                      body=f"Nome: {nome}\nEmail: {email}\nMensagem: {mensagem}")
        mail.send(msg)
        flash('Solicitação enviada com sucesso!', 'success')
        return redirect(url_for('suporte'))

    return render_template('suporte.html')

# ======== Treinamento ========
@app.route('/treinamento')
def treinamento():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('treinamento.html')

# ======== Redefinir Senha ========
@app.route('/redefinir_senha', methods=['GET', 'POST'])
def redefinir_senha():
    if request.method == 'POST':
        email = request.form['email']

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()

        if user:
            token = secrets.token_urlsafe(16)
            conn.execute("UPDATE usuarios SET reset_token = ? WHERE id = ?", (token, user['id']))
            conn.commit()

            # Envia e-mail
            msg = Message(subject="Redefinir Senha",
                          sender=app.config['MAIL_USERNAME'],
                          recipients=[email],
                          body=f"Acesse o link para redefinir sua senha: {request.url_root}redefinir_senha/{token}")
            mail.send(msg)
            flash('E-mail enviado com instruções!', 'success')
        else:
            flash('E-mail não encontrado.', 'danger')

        conn.close()

    return render_template('redefinir_senha.html')

# ======== Rota para resetar senha com token ========
@app.route('/redefinir_senha/<token>', methods=['GET', 'POST'])
def redefinir_senha_token(token):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM usuarios WHERE reset_token = ?", (token,)).fetchone()

    if not user:
        flash('Token inválido ou expirado.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        nova_senha = generate_password_hash(request.form['senha'])
        conn.execute("UPDATE usuarios SET senha = ?, reset_token = NULL WHERE id = ?", (nova_senha, user['id']))
        conn.commit()
        conn.close()
        flash('Senha redefinida com sucesso!', 'success')
        return redirect(url_for('login'))

    conn.close()
    return render_template('redefinir_senha_token.html', token=token)

# ======== API para eventos do calendário ========
# ======== Rota para listar eventos do calendário ========
@app.route('/get_events')
def get_events():
    # Verifica se o usuário está logado
    if 'user_id' not in session:
        return jsonify([])

    # Conecta ao banco
    conn = get_db_connection()
    events = conn.execute(
        "SELECT id, titulo AS title, data || 'T' || hora AS start FROM agendamentos WHERE usuario_id = ?",
        (session['user_id'],)
    ).fetchall()
    conn.close()

    # Monta a lista de eventos no formato que o FullCalendar entende
    eventos = []
    for e in events:
        eventos.append({
            "id": e["id"],      # ID do evento (necessário para editar/excluir)
            "title": e["title"],# Título do evento (nome do cliente ou título da reunião)
            "start": e["start"],# Data e hora combinadas no formato ISO
            "allDay": False     # False porque queremos horário específico
        })

    return jsonify(eventos)


# ======== Rodar app ========
if __name__ == '__main__':
    if not os.path.exists(DB_NAME):
        conn = get_db_connection()
        conn.execute("""
        CREATE TABLE usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            reset_token TEXT
        )
        """)
        conn.execute("""
        CREATE TABLE clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            email TEXT,
            telefone TEXT,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        )
        """)
        conn.execute("""
        CREATE TABLE agendamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            cliente_id INTEGER,
            titulo TEXT NOT NULL,
            data TEXT NOT NULL,
            hora TEXT NOT NULL,
            descricao TEXT,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id),
            FOREIGN KEY(cliente_id) REFERENCES clientes(id)
        )
        """)
        conn.commit()
        conn.close()

    app.run(host='0.0.0.0', port=5000, debug=True)

@app.route("/teste_clientes")
def teste_clientes():
    return render_template("clientes.html")
