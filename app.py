import os
from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
import psycopg2

app = Flask(__name__)

# Configurações de upload
app.config["UPLOAD_FOLDER"] = "static/uploads"  # Pasta onde as imagens serão salvas
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # Limite de 5MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Usando a variável de ambiente para configurar a conexão com o banco de dados
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL is None:
    raise ValueError("A variável de ambiente 'DATABASE_URL' não está configurada")

# Conectar ao banco de dados
conn = psycopg2.connect(DATABASE_URL)

# Função para verificar se o arquivo é uma imagem válida
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Função para verificar se a imagem existe fisicamente
def image_exists(image_filename):
    """Verifica se a imagem existe fisicamente no diretório"""
    return os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"], image_filename))

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["file"]
        comment = request.form["comment"]

        if file and allowed_file(file.filename):
            # Salva o arquivo na pasta 'static/uploads'
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)  # Caminho correto
            file.save(file_path)

            # Inserir dados no banco com apenas o nome do arquivo
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO uploads (image_url, comment) VALUES (%s, %s)",
                (filename, comment)  # Armazenamos apenas o nome do arquivo
            )
            conn.commit()
            cursor.close()

    # Pega as imagens do banco
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM uploads")
    uploads = cursor.fetchall()
    cursor.close()

    # Verifica se a imagem existe fisicamente antes de exibir
    uploads = [(upload[0], upload[1], upload[2]) for upload in uploads if image_exists(upload[1])]

    return render_template("index.html", uploads=uploads)

@app.route("/delete/<int:image_id>", methods=["POST"])
def delete(image_id):
    password = request.form["password"]
    
    # Verifica a senha
    if password == "123ok":
        cursor = conn.cursor()
        cursor.execute("SELECT image_url FROM uploads WHERE id = %s", (image_id,))
        image_url = cursor.fetchone()[0]

        # Exclui a imagem do banco de dados
        cursor.execute("DELETE FROM uploads WHERE id = %s", (image_id,))
        conn.commit()
        cursor.close()

        # Exclui a imagem fisicamente, se ela existir
        if image_exists(image_url):
            try:
                os.remove(os.path.join(app.config["UPLOAD_FOLDER"], image_url))  # Remove a imagem da pasta
            except FileNotFoundError:
                pass  # Caso o arquivo já tenha sido removido, não faça nada

    return redirect(url_for("index"))

if __name__ == "__main__":
    # Pega a variável de ambiente PORT ou usa a 5000 por padrão
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
