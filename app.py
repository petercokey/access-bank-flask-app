# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
from bank import UserDashboard, Rewards
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import io
import matplotlib.pyplot as plt
import random
from werkzeug.security import generate_password_hash, check_password_hash


users = {}

app = Flask(__name__)
my_account = UserDashboard("0075623123", balance=0)
my_reward = Rewards(50000, 20)

app.secret_key = "supersecretkey"   # 🔥 change this in production
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# --- DATABASE MODEL ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # ✅ one-to-one relationship with Account
    account = db.relationship("Account", backref="owner", uselist=False)
    transactions = db.relationship("Transaction", backref="user", lazy=True)


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_number = db.Column(db.String(20), unique=True, nullable=False)
    balance = db.Column(db.Float, default=0.0)

    # link to user
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    type = db.Column(db.String(20))  # inflow/outflow
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # look up user in DB
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["user_name"] = user.full_name
            return redirect(url_for("landing"))
        else:
            return render_template("login.html", error="Invalid email or password")

    return render_template("login.html")


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        full_name = request.form.get('username')  # renamed for clarity
        email = request.form.get('email')
        password = request.form.get('password')

        if not full_name or not email or not password:
            flash('Please fill all fields', 'error')
            return render_template('signup.html')

        if User.query.filter_by(email=email).first():
            flash('User with that email already exists', 'error')
            return render_template('signup.html')

        # create new user
        hashed_pw = generate_password_hash(password)
        user = User(full_name=full_name, email=email, password=hashed_pw)
        db.session.add(user)
        db.session.commit()

        # create their bank account
        account = Account(user_id=user.id, account_number=str(random.randint(1000000000, 9999999999)), balance=0.0)
        db.session.add(account)
        db.session.commit()

        flash('✅ Account created successfully. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route("/other_banks", methods=["GET", "POST"])
def other_banks():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        bank = request.form.get("bank")
        acct_no = request.form.get("account_number")
        amount = float(request.form.get("amount", 0))

        user = User.query.get(session["user_id"])
        account = user.account

        if account.balance >= amount:
            account.balance -= amount

            txn = Transaction(
                title=f"Transfer to {bank} ({acct_no})",
                type="outflow",
                amount=amount,
                user=user
            )
            db.session.add(txn)
            db.session.commit()

            flash(f"₦{amount} sent to {bank}", "success")
        else:
            flash("Insufficient funds", "danger")

        return redirect(url_for("landing"))

    banks = ["Access Bank", "GTBank", "First Bank", "UBA", "Zenith Bank"]
    return render_template("other_banks.html", banks=banks)


@app.route("/landing")
def landing():
    if "user_id" not in session:
        flash("Please log in first", "warning")
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])
    account = user.account

    # recent transactions
    txns = Transaction.query.filter_by(user_id=user.id).order_by(Transaction.timestamp.desc()).limit(5).all()

    return render_template(
        "landing.html",
        name=user.full_name,
        balance=account.balance,
        account_number=account.account_number,
        recent_txns=txns
    )


@app.route("/learn_more")
def learn_more():
    return render_template("learn_more.html")

# --- keep your other routes (notifications, rewards, loans, etc.) unchanged ---
# I only cleaned the bcrypt / hashing problem


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)


