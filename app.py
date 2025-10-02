# app.py
from flask import Flask, render_template, request, redirect, url_for 
from bank import UserDashboard
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask import session, flash
from bank import Rewards
from datetime import datetime
import io
import matplotlib.pyplot as plt
from flask import Response
import random



users= {}


app = Flask(__name__)
my_account = UserDashboard( "0075623123", balance=0)
my_reward = Rewards(50000, 20)

app.secret_key = "supersecretkey"   # 🔥 change this in production
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


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

        if user and bcrypt.check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["user_name"] = user.full_name
            return redirect(url_for("landing"))
        else:
            return render_template("login.html", error="Invalid email or password")

    return render_template("login.html")




@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        fullname = request.form["fullname"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            return render_template("signup.html", error="Passwords do not match")

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return render_template("signup.html", error="Email already registered")

        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")

        # Create user
        new_user = User(full_name=fullname, email=email, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

        # ✅ Generate account number & create account
        
        acct_number = str(random.randint(1000000000, 9999999999))  # 10-digit acct no
        account = Account(account_number=acct_number, balance=0.0, owner=new_user)
        db.session.add(account)
        db.session.commit()

        

        flash("Signup successful! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")



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

        return redirect(url_for("transfer_successful"))

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
 
@app.route("/notification")
def notifications():
    return render_template("notification.html")

@app.route("/rewards")
def rewards():
    if "user" not in session:
        return redirect(url_for("login"))

    email = session["user"]
    points = users[email]["rewards"].points

    return render_template("rewards.html", reward=points)


@app.route("/loans")
def loans():
    return render_template("loans.html")

@app.route("/evocher")
def evocher():
    return render_template("evocher.html")
@app.route("/bill_payment")
def bill_payment():
    return render_template("bill_payment.html")

@app.route("/menu")
def menu():
    return render_template("menu.html")
@app.route("/mobile_topup")
def mobile_topup():
    return render_template("mobile_topup.html")


@app.route("/profile")
def profile():
    return render_template("profile.html")

@app.route("/support")
def support():
    return render_template("support.html")

@app.route("/international_airtime")
def international_airtime():
    return render_template("international_airtime.html")

@app.route("/wealth")
def wealth():
    return render_template("wealth.html")

@app.route("/breezepay")
def breezepay():
    return render_template("breezepay.html")

@app.route("/access_transfers")
def access_transfers():
    return render_template("access_transfers.html")

@app.route("/scan")
def scan():
    return render_template("scan.html")

@app.route("/sport_wallet")
def sport_wallet():
    return render_template("sport_wallet.html")


@app.route("/transactional_history", methods=["GET", "POST"])
def transactional_history():
    if request.method == "POST":
        history = my_account.get_transaction_history()
        return render_template("transactional_history.html", history=history)
    return render_template("transactional_history.html")


@app.route("/spending_chart")
def spending_chart():
    if "user" not in session:
        return redirect(url_for("login"))

    email = session["user"]
    dashboard = users[email]["dashboard"]

    labels = ["Inflow", "Outflow"]
    values = [dashboard.inflow, dashboard.outflow]

    fig, ax = plt.subplots(figsize=(4, 4))
    ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90,
           colors=["#10B981", "#EF4444"])
    ax.axis("equal")

    img = io.BytesIO()
    plt.savefig(img, format="png", bbox_inches="tight", transparent=True)
    img.seek(0)
    plt.close(fig)
    return Response(img.getvalue(), mimetype="image/png")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)


