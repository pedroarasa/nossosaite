import os
from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
import psycopg2

app = Flask(__name__)

# Configurações
app.config["UPLOAD_FOLDER"] = "static/uploads"  # Pasta onde as imagens serão salvas
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # Limite de 5MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Conectar ao banco de dados
conn = psycopg2.connect(
    "postgresql://neondb_owner:npg_izJKD7Qm0kEh@ep-wandering-resonance-a9e1300q-pooler.gwc.azure.neon.tech/neondb?sslmode=require"
)

# Função para verificar se o arquivo é uma imagem válida
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

        # Exclui a imagem fisicamente
        try:
            os.remove(os.path.join(app.config["UPLOAD_FOLDER"], image_url))  # Remove a imagem da pasta
        except FileNotFoundError:
            pass

    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
