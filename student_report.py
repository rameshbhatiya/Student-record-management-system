import os
from datetime import datetime, timezone
from functools import wraps
from flask import (
    Flask,
    request,
    redirect,
    url_for,
    render_template_string,
    session,
    flash,
    abort,
)
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash

# ------------------------------------------
# APPLICATION CONFIGURATION
# ------------------------------------------
app = Flask(__name__)

# Enforce explicit secret key set in production environment
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-key-change-in-production")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///school_erp.db"
).replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

db = SQLAlchemy(app)
csrf = CSRFProtect(app)

# ------------------------------------------
# CONSTANTS
# ------------------------------------------
ROLES = ("super_admin", "school_owner", "principal", "admin", "teacher", "parent", "student")

# ------------------------------------------
# DATABASE MODELS
# ------------------------------------------
class School(db.Model):
    __tablename__ = "schools"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    school_code = db.Column(db.String(30), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(300))
    logo = db.Column(db.String(300))
    status = db.Column(db.String(20), default="pending", nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    users = db.relationship("User", back_populates="school", cascade="all, delete-orphan")


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id"), nullable=True, index=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    school = db.relationship("School", back_populates="users")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id"), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    action = db.Column(db.String(150), nullable=False)
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


# ------------------------------------------
# COMMON HELPERS & DECORATORS
# ------------------------------------------
def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    user = db.session.get(User, user_id)
    if not user or not user.is_active:
        session.clear()
        return None
    return user


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash("Please login first.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def role_required(*allowed_roles):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            user = current_user()
            if user.role not in allowed_roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def school_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user.school_id:
            abort(403)
        school = db.session.get(School, user.school_id)
        if not school or school.status != "active":
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def log_action(action, details=""):
    user = current_user()
    if not user:
        return
    entry = AuditLog(
        school_id=user.school_id, user_id=user.id, action=action, details=details
    )
    db.session.add(entry)


# ------------------------------------------
# BASIC PAGE DESIGN
# ------------------------------------------
BASE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{{ title }} | School ERP</title>
    <style>
        * { box-sizing: border-box; }
        body { margin: 0; background: #f4f6fa; color: #202b3c; font-family: Arial, sans-serif; }
        .navbar { background: #172b4d; color: white; padding: 18px 6%; display: flex; justify-content: space-between; align-items: center; }
        .navbar a { color: white; text-decoration: none; margin-left: 15px; }
        .container { width: min(1100px, 92%); margin: 35px auto; }
        .card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 3px 15px #0000000b; margin-bottom: 20px; }
        input, select { width: 100%; padding: 12px; border: 1px solid #d6dce5; border-radius: 7px; margin: 7px 0 15px; }
        button, .btn { background: #2459a6; color: white; border: 0; padding: 12px 18px; border-radius: 7px; cursor: pointer; text-decoration: none; display: inline-block; }
        .btn-success { background: #28a745; }
        .message { padding: 12px; background: #e8f1ff; border-radius: 7px; margin-bottom: 12px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 15px; }
        .muted { color: #758195; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 10px; border: 1px solid #d6dce5; text-align: left; }
        @media(max-width: 600px) { .navbar { padding: 15px; flex-wrap: wrap; gap: 10px; } }
    </style>
</head>
<body>
    <nav class="navbar">
        <strong>School ERP</strong>
        <div>
            {% if user %}
                <span>{{ user.full_name }} ({{ user.role }})</span>
                <a href="{{ url_for('dashboard') }}">Dashboard</a>
                <a href="{{ url_for('logout') }}">Logout</a>
            {% else %}
                <a href="{{ url_for('home') }}">Home</a>
                <a href="{{ url_for('login') }}">Login</a>
            {% endif %}
        </div>
    </nav>
    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% for category, message in messages %}
                <div class="message">{{ message }}</div>
            {% endfor %}
        {% endwith %}
        {{ content|safe }}
    </div>
</body>
</html>
"""


def page(title, content, **context):
    return render_template_string(
        BASE_HTML,
        title=title,
        content=render_template_string(content, **context),
        user=current_user(),
    )


# ------------------------------------------
# PUBLIC HOMEPAGE
# ------------------------------------------
@app.route("/")
def home():
    content = """
    <div class="card">
        <h1>Welcome to School ERP</h1>
        <p class="muted">
            A centralized platform for schools, teachers, students and parents.
        </p>
        <a class="btn" href="{{ url_for('login') }}"> Login to Portal </a>
        <a class="btn" href="{{ url_for('register_school') }}"> Register Your School </a>
    </div>
    """
    return page("Home", content)


# ------------------------------------------
# SCHOOL REGISTRATION
# ------------------------------------------
@app.route("/register-school", methods=["GET", "POST"])
def register_school():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        owner = request.form.get("owner", "").strip()
        password = request.form.get("password", "")

        if not all([name, email, owner, password]):
            flash("Please complete all required fields.", "danger")
            return redirect(url_for("register_school"))

        if len(password) < 10:
            flash("Password must contain at least 10 characters.", "danger")
            return redirect(url_for("register_school"))

        if User.query.filter_by(email=email).first():
            flash("This email is already registered.", "danger")
            return redirect(url_for("register_school"))

        if School.query.filter_by(email=email).first():
            flash("This school email is already registered.", "danger")
            return redirect(url_for("register_school"))

        code = "SCH" + os.urandom(4).hex().upper()
        school = School(
            name=name, school_code=code, email=email, phone=phone, status="pending"
        )
        db.session.add(school)
        db.session.flush()

        account = User(
            school_id=school.id, full_name=owner, email=email, role="school_owner"
        )
        account.set_password(password)
        db.session.add(account)
        db.session.commit()

        flash("Registration submitted. Awaiting super-admin approval.", "success")
        return redirect(url_for("login"))

    content = """
    <div class="card">
        <h2>Register Your School</h2>
        <form method="POST">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
            <label>School Name</label>
            <input name="name" required maxlength="150">
            <label>Official School Email</label>
            <input type="email" name="email" required>
            <label>Contact Number</label>
            <input name="phone">
            <label>Owner / Principal Name</label>
            <input name="owner" required>
            <label>Create Password</label>
            <input type="password" name="password" minlength="10" required>
            <button type="submit">Submit Registration</button>
        </form>
    </div>
    """
    return page("School Registration", content)


# ------------------------------------------
# LOGIN
# ------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user():
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("login"))

        if not user.is_active:
            flash("This account is disabled.", "danger")
            return redirect(url_for("login"))

        if user.school_id:
            school = db.session.get(School, user.school_id)
            if not school or school.status != "active":
                flash("School account is awaiting approval.", "warning")
                return redirect(url_for("login"))

        session.clear()
        session["user_id"] = user.id
        log_action("User login")
        db.session.commit()

        return redirect(url_for("dashboard"))

    content = """
    <div class="card">
        <h2>Portal Login</h2>
        <form method="POST">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
            <label>Email Address</label>
            <input type="email" name="email" required>
            <label>Password</label>
            <input type="password" name="password" required>
            <button type="submit">Login</button>
        </form>
    </div>
    """
    return page("Login", content)


# ------------------------------------------
# DASHBOARD ROUTER & ENDPOINTS
# ------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    if user.role == "super_admin":
        return redirect(url_for("super_admin_dashboard"))
    if user.role in ("school_owner", "principal", "admin"):
        return redirect(url_for("school_dashboard"))
    if user.role == "teacher":
        return redirect(url_for("teacher_dashboard"))
    if user.role == "student":
        return redirect(url_for("student_dashboard"))
    if user.role == "parent":
        return redirect(url_for("parent_dashboard"))
    abort(403)


@app.route("/dashboard/super-admin")
@role_required("super_admin")
def super_admin_dashboard():
    pending_schools = School.query.filter_by(status="pending").all()
    active_schools = School.query.filter_by(status="active").all()

    content = """
    <div class="card">
        <h2>Super Admin Portal</h2>
        <h3>Pending School Registrations</h3>
        {% if pending_schools %}
        <table>
            <tr><th>School</th><th>Code</th><th>Email</th><th>Action</th></tr>
            {% for s in pending_schools %}
            <tr>
                <td>{{ s.name }}</td>
                <td>{{ s.school_code }}</td>
                <td>{{ s.email }}</td>
                <td>
                    <form method="POST" action="{{ url_for('approve_school', school_id=s.id) }}" style="margin:0;">
                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                        <button type="submit" class="btn btn-success">Approve</button>
                    </form>
                </td>
            </tr>
            {% endfor %}
        </table>
        {% else %}
            <p class="muted">No pending school requests.</p>
        {% endif %}
    </div>
    <div class="card">
        <h3>Active Schools ({{ active_schools|length }})</h3>
        <ul>
        {% for s in active_schools %}
            <li><strong>{{ s.name }}</strong> ({{ s.school_code }})</li>
        {% endfor %}
        </ul>
    </div>
    """
    return page("Super Admin Dashboard", content, pending_schools=pending_schools, active_schools=active_schools)


@app.route("/approve-school/<int:school_id>", methods=["POST"])
@role_required("super_admin")
def approve_school(school_id):
    school = db.session.get(School, school_id)
    if school:
        school.status = "active"
        log_action("Approve school", f"Approved school ID: {school.id}")
        db.session.commit()
        flash(f"School '{school.name}' has been activated.", "success")
    return redirect(url_for("super_admin_dashboard"))


@app.route("/dashboard/school")
@school_required
@role_required("school_owner", "principal", "admin")
def school_dashboard():
    content = """
    <div class="card">
        <h2>School Administration Dashboard</h2>
        <p>Welcome to your school administration workspace.</p>
    </div>
    """
    return page("School Dashboard", content)


@app.route("/dashboard/teacher")
@school_required
@role_required("teacher")
def teacher_dashboard():
    content = """
    <div class="card">
        <h2>Teacher Portal</h2>
        <p>Manage your classes, students, and marks here.</p>
    </div>
    """
    return page("Teacher Dashboard", content)


@app.route("/dashboard/student")
@school_required
@role_required("student")
def student_dashboard():
    content = """
    <div class="card">
        <h2>Student Portal</h2>
        <p>View your course reports, attendance, and grades.</p>
    </div>
    """
    return page("Student Dashboard", content)


@app.route("/dashboard/parent")
@school_required
@role_required("parent")
def parent_dashboard():
    content = """
    <div class="card">
        <h2>Parent Portal</h2>
        <p>Track your child's academic performance and school announcements.</p>
    </div>
    """
    return page("Parent Dashboard", content)


# ------------------------------------------
# LOGOUT
# ------------------------------------------
@app.route("/logout")
@login_required
def logout():
    user = current_user()
    if user:
        log_action("User logout")
        db.session.commit()
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


# ------------------------------------------
# DATABASE INITIALIZATION & SEEDING COMMAND
# ------------------------------------------
@app.cli.command("init-db")
def init_db():
    db.create_all()

    # Seed a default Super Admin if none exists
    admin = User.query.filter_by(role="super_admin").first()
    if not admin:
        admin = User(
            full_name="System Super Admin",
            email="admin@system.local",
            role="super_admin",
            is_active=True,
        )
        admin.set_password("AdminPassword123!")
        db.session.add(admin)
        db.session.commit()
        print("Database initialized and default Super Admin created (email: admin@system.local, pass: AdminPassword123!).")
    else:
        print("Database initialized.")


# ------------------------------------------
# APPLICATION ENTRY POINT
# ------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
