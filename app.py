from flask import Flask, render_template, request, redirect, session
from cs50 import SQL
from flask_session import Session
from flask_mail import Mail, Message
from datetime import datetime
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, register_required, login_required, get_actual_oil_prices_on_login, usd
from forex_python.converter import CurrencyRates
import re, random, copy

app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Send e-mail configuration
app.config["MAIL_DEFAULT_SENDER"] = 'iwilad@prokonto.pl'
app.config["MAIL_PASSWORD"] = '123!@#ewqEWQ'
app.config["MAIL_PORT"] = 465
app.config["MAIL_SERVER"] = 'poczta.o2.pl'
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USERNAME"] = 'iwilad@o2.pl'
mail = Mail(app)

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#export MAIL_PASSWORD="{your_mail_password}"

#connect to database
db = SQL("sqlite:///database.db")

@app.route("/")
@login_required
def index():
    return render_template("aboutus.html", fuel=session["fuel_prices"])

@app.route("/fuelhistory")
@login_required
def fuelhistory():
    prices = db.execute("SELECT * FROM fuel_prices")
    c = CurrencyRates()
    rate = c.get_rate('PLN', 'USD')
    dolar_prices = copy.deepcopy(prices)

    for row in dolar_prices:
        del row['entry_id']
        del row['date']
        for key in row:
            row[key] = usd(row[key]*rate)
    length = int(len(dolar_prices))
    print(prices)
    print(dolar_prices)
    #f"${value:,.2f}"

    return render_template("fuelprices.html", fuel=session["fuel_prices"], afd=prices, usd=dolar_prices, len=length)

@app.route("/getname", methods=["GET", "POST"])
@login_required
def getname():
    if request.method == "POST":
        name = request.form.get("name")
        if not name:
            return apology("You need to input name")
        check_name = name.isalpha()
        if check_name != True:
            return apology("Name can be only alpha")
        if len(name) > 20:
            return apology("Maxiumum name length is 20 chars")
        if len(name) < 2:
            return apology("Minimum name length is 2 chars")
        name = name.capitalize()

        now = datetime.now()
        formatted_date = now.strftime('%Y-%m-%d')

        return render_template("name.html", name=name, date=formatted_date, fuel=session["fuel_prices"])
    else:

        return render_template("getname.html", fuel=session["fuel_prices"])

@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("email"):
            return apology("must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # Query database for username
        userdata = db.execute("SELECT * FROM users WHERE mail = ?", request.form.get("email"))

        # Ensure username exists and password is correct
        if len(userdata) != 1 or not check_password_hash(userdata[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = userdata[0]["id"]

        get_actual_oil_prices_on_login()
        session["fuel_prices"] = db.execute('SELECT * FROM fuel_prices ORDER BY date DESC LIMIT 1')

        # Redirect user to home page
        return redirect("/")

    else:
        return(render_template("login.html"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        session.clear()
        email = request.form.get("email")

        if not email:
            return apology("Missing e-mail")
        
        #Step 2: Check if mail format is correct
        match = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', email)

        if match == None:
            return apology("Wrong e-mail adress")

        # check if name exists in database 
        verifyemail = db.execute("SELECT COUNT(mail) as email FROM users WHERE mail = ?", email)

        if verifyemail[0]["email"] != 0:
            return apology("E-mail already exists in database")

        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not password:
            return apology("you need to provide password") 
                
        if not confirmation:
            return apology("you need to provide confirmations")      
        
        # check if given passwords match
        if password != confirmation:
            return apology("passwords do not match")
        
        # check if password
        match = re.match('^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$', password)
        if match == None:
            return apology("Minimum eight characters, at least one letter and one number. Only letters and numbers.")

        passwordhash = generate_password_hash(password)
        verifyemailhash = random.getrandbits(32)

        message = Message("Email confirmation code: " + str(verifyemailhash), recipients=[email])
        mail.send(message)

        session["email"] = email
        session["passwordhash"] = passwordhash
        session["verifyemailhash"] = verifyemailhash

        return redirect("/confirmmail")

    else:
        return(render_template("register.html"))

@app.route("/confirmmail", methods=["GET", "POST"])
@register_required
def confirmmail():
    if request.method == "POST":
        userhash = request.form.get("code")
        print(userhash)
        print(request.form.get("code"))
        if int(userhash) != int(session["verifyemailhash"]):
            session.clear()
            return apology("Wrong verification code, you need to repeat registration process")
        else:        
            db.execute("INSERT INTO users (mail, hash) VALUES(?, ?)", session["email"], session["passwordhash"])
            session.clear()
            return render_template("login.html")
    else: 
        return(render_template("mailconfirmation.html"))

@app.route("/changepassword", methods=["GET", "POST"])
@login_required
def changepassword():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        currentpassword = request.form.get("currentpassword")

        # Ensure currentpassword was submitted
        if not currentpassword:
            return apology("must provide current password")

        newpassword = request.form.get("newpassword")

        # Ensure new password was submitted
        if not newpassword:
            return apology("must provide new password")

        newpasswordrepeat = request.form.get("newpasswordrepeat")

        # Ensure new password reentered mietek
        if not newpasswordrepeat:
            return apology("must repeat new password")
        
        match = re.match('^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$', newpassword)
        if match == None:
            return apology("Minimum eight characters, at least one letter and one number.")

        # Ensure new passwords match
        if newpassword != newpasswordrepeat:
            return apology("passwords do not match")

        # Query database for logged user id
        userdata = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])

        # Ensure current password is correct
        if not check_password_hash(userdata[0]["hash"], currentpassword):
            return apology("current password is invalid")

        hashpass = generate_password_hash(newpassword)
        db.execute("UPDATE users SET hash = ? WHERE id = ?", hashpass, session["user_id"])

        session.clear()
        # Redirect user to home page
        return redirect("/login")

    else:
        return render_template("changepassword.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")



if __name__ == '__main__':
    app.run(debug=True)