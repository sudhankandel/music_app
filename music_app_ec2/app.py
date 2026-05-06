from flask import Flask, render_template, redirect, url_for
from api import api_bp

app = Flask(__name__)
app.secret_key = "abc123"  # required for session

# Register API routes
app.register_blueprint(api_bp)


@app.route("/")
def home():
    return redirect(url_for("login_page"))


@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/register")
def register_page():
    return render_template("register.html")


@app.route("/main")
def main_page():
    return render_template("main.html")


if __name__ == "__main__":
    app.run( debug=True)