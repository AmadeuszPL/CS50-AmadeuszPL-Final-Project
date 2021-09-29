from flask import Flask, render_template, request, redirect, session
from functools import wraps
from cs50 import SQL
import subprocess, os, tablib, re
from datetime import datetime

db = SQL("sqlite:///database.db")

def apology(message):
    message = message.upper()
    return render_template("apology.html", message=message)

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def register_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("email") is None:
            session.clear()
            return redirect("/register")
        return f(*args, **kwargs)
    return decorated_function

def get_actual_oil_prices_on_login():
    now = datetime.now()
    formatted_date = now.strftime('%Y-%m-%d')
    verifydata = db.execute("SELECT COUNT(date) as d FROM fuel_prices WHERE date = ?", formatted_date)

    if verifydata[0]["d"] == 0:      
        if os.path.exists('fuelprices/fuelprices.csv'):
            os.remove('fuelprices/fuelprices.csv')

        spider_name = "fuelprices_autocentrum"
        subprocess.run(['scrapy', 'crawl', spider_name], cwd='fuelprices/')

        dataset = tablib.Dataset()
        with open(os.path.join(os.path.dirname(__file__),'fuelprices/fuelprices.csv')) as f:
            dataset.csv = f.read()
        
        d = dict()
        for line in dataset:
            #d[line[0]] = line[1]
            string = re.sub("[^0-9,]", "", line[1])
            new = string.replace(",", ".")
            d[line[0]] = float(new)
        
        db.execute("INSERT INTO fuel_prices (benzin_price, pbenzin_price, oil_price, poil_price, lpg_price, date) VALUES(?, ?, ?, ?, ?, ?)", d['95'], d['98'], d['ON'], d['ON+'], d['LPG'], now)

def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"