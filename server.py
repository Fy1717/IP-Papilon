
import os, ftfy, cv2, re, urllib
import pytesseract as tess
from flask import Flask, url_for, redirect, render_template, request, session, flash
from wtforms import Form, BooleanField, StringField, PasswordField, validators
from flask_uploads import UploadSet, configure_uploads, IMAGES
from flask_jwt import JWT, jwt_required, current_identity
from werkzeug.security import safe_str_cmp
from flask_mysqldb import MySQL
from functools import wraps
from PIL import Image


project_dir = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__,
            static_url_path = '',
            static_folder = 'static',
            template_folder = 'templates')

photos = UploadSet('photos', IMAGES)

# -------------------------------------- DATABASE CONNECTION -----------------------------------------------------
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "papilon"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
app.config['SECRET_KEY'] = 'papilon-defence'

mysql = MySQL(app)
# -----------------------------------------------------------------------------------------------------------------

# ------------------------------------------  REGISTER FORM -------------------------------------------------------
class RegisterForm(Form):
    username = StringField(validators=[validators.Length(min=4, max=30)])
    password = PasswordField(validators=[
        validators.DataRequired(message= "Enter a Password"),
        validators.EqualTo(fieldname= "confirm", message= "False Password")])
    confirm = PasswordField(description="Confirm")
# -----------------------------------------------------------------------------------------------------------------

# ------------------------------------------  LOGIN FORM --------------------------------------------------------
class LoginForm(Form):
    username = StringField("USERNAME")
    password = PasswordField("PASSWORD")
# ----------------------------------------------------------------------------------------------------------------

# -------------------------------------- IMAGE PROCESSING ---------------------------------------------------
class ImageText(object):
    def __init__(self, file):
        self.file = ftfy.fix_encoding(
            ftfy.fix_text(
                tess.image_to_string(
                    Image.open(project_dir + '/images/' + file))))
# -----------------------------------------------------------------------------------------------------------------                  

# -------------------------------------- LOGIN DECORATOR ------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Please Login The System!", "danger")
            return redirect(url_for("login"))
    
    return decorated_function
#-----------------------------------------------------------------------------------------------------------------

# --------------------------------------- LOGIN CONTROL ------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)

    if request.method == "POST":
        username = form.username.data
        password = form.password.data
        cursor = mysql.connection.cursor()
        sorgu = "Select * From users where username = %s"
        result = cursor.execute(sorgu, (username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]

            if password == real_password:
                session["logged_in"] = True
                session["username"] = username

                return redirect(url_for("profile"))
            else:
                return redirect(url_for("login"))
        else:
            flash("Please try again!", "danger")

            return redirect(url_for("login"))
    return render_template("login.html", form = form)
# ----------------------------------------------------------------------------------------------------------------- 

# ------------------------------------------ LOGOUT ------------------------------------------------------
@app.route("/logout")
@login_required
def logout():
    session.clear()

    return redirect(url_for("home"))
# -----------------------------------------------------------------------------------------------------------------                 

# ----------------------------------------- ID CONTROL ------------------------------------------------------
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST' and 'photo' in request.files:
        photo = request.files['photo']
        path = os.path.join('images', photo.filename)
        photo.save(path) 
        textObject = ImageText(photo.filename)
        result = textObject.file
        
        return redirect(url_for('register', result=result))
    return render_template('index.html')
# -----------------------------------------------------------------------------------------------------------------                  

# ----------------------------------------- REGISTER CONTROL ------------------------------------------------------
@app.route('/result', methods=['GET', 'POST'])
def register():
    query = request.args.get('result', None)
    list_of_text = query.split('%0A')[0].split('\n')
    form = RegisterForm(request.form)

    username = form.username.data
    password = form.password.data
    lastdate = list_of_text[24].split(' ')[0].split('.')

    idInformation = {
        'id_number': list_of_text[5],
        'name': list_of_text[13],
        'surname': list_of_text[9],
        'serial_number': list_of_text[20].split(':')[0],
        'last_date': lastdate[-1] + '-' + lastdate[1] + '-' + lastdate[0] 
    }

    #print(idInformation)

    cursor = mysql.connection.cursor()

    if request.method == "POST" and form.validate():
        sorgu = "Insert into users(name, id_number, username, surname, password, serial_number, last_date) VALUES(%s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(sorgu,(idInformation.get('name'), idInformation.get('id_number'), username, 
                idInformation.get('surname'), password, idInformation.get('serial_number'), idInformation.get('last_date'),))
        mysql.connection.commit()
        cursor.close()

        return redirect(url_for("login"))
    return render_template('register.html', idInformation=idInformation, form = form)
# -----------------------------------------------------------------------------------------------------------------              

# ----------------------------------------- PROFILE ------------------------------------------------------
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    cursor = mysql.connection.cursor()

    sorgu = "Select * From users where username = %s"
    result = cursor.execute(sorgu, (session["username"],))

    if result > 0:
        user = cursor.fetchone()
        #print(user)
        mysql.connection.commit()
        cursor.close()
        
    flash("Login Success!", "success")

    return render_template("profile.html", user = user)
# ----------------------------------------------------------------------------------------------------------------- 


if __name__ == '__main__':
    app.run(debug = True)

