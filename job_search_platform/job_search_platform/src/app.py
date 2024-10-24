import os
import bcrypt
import datetime
from dotenv import load_dotenv
from faunadb import query as q
from faunadb.client import FaunaClient
from faunadb import errors as fauna_errors
from flask import Flask, render_template, request, redirect, url_for, flash, session

# Load the env-vars from `.env` file
load_dotenv()

# Initialize the client
client = FaunaClient(secret=os.getenv("FAUNADB_SECRET"))

# Initialize the flask-app
app = Flask(__name__)
app.secret_key = os.getenv("FLASH_SECRET").encode()

app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(hours=1)

hash_password = lambda p: bcrypt.hashpw(p.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
check_password = lambda hp, p: bcrypt.checkpw(p.encode('utf-8'), hp.encode('utf-8'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/<user_type>', methods=['GET'])
def register_login(user_type):
    return render_template('register_login.html', user_type=user_type)
  
@app.route('/<user_type>/register', methods=['POST'])
def register(user_type):
    # Extract data from <form>
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')

    # Validate confirmation
    if password != confirm_password:
        flash("Passwords doesn't match! Please try again.", 'error')
        return redirect(f'/{user_type}')

    # Hash password
    hashed_password = hash_password(password)

    # Save to database
    try:
        result = client.query(
            q.create(
                q.collection(f'{user_type}s'),
                {"data": dict(name=name, email=email, password=hashed_password)}
            )
        )
    except fauna_errors.BadRequest as ex:
        flash(f'Account already exists! Please login with <{email}>', 'warning')
        return redirect(f'/{user_type}')

    flash(f'[{result["ref"].id()}] Registration successful! Please login.', 'success')
    return redirect(f'/{user_type}')

@app.route('/<user_type>/login', methods=['POST'])
def login(user_type):
    email = request.form.get('email')
    password = request.form.get('password')

    # Authenticate user credentials
    try:
        result = client.query(
            q.get(q.match(q.index(f'{user_type}s_by_email'), email))
        )

        if check_password(result['data']['password'], password):
            session['email'] = email
            session['user_type'] = user_type
            session['user_id'] = result['ref'].id()

            flash(f'[{session["user_id"]}] Login successful!', 'success')
            match user_type:
                case "employer":
                    try:
                        results = client.query(
                            q.paginate(q.match(q.index(f'job_posts_by_email'), session['email']))
                        )
                        jobs = list((ref.id(), client.query(q.get(q.ref(q.collection('job_posts'),
                                    ref.id())))['data']) for ref in results['data'])
                        return render_template('employer/index.html', jobs=jobs)
                    except fauna_errors.NotFound:
                        flash(f'No jobs found with mail <{session["email"]}>', 'danger')
                        return render_template('employer/index.html', jobs=list())
                case "employee":
                    try:
                        results = client.query(q.paginate(q.documents(q.collection('job_posts'))))
                        jobs = list(client.query(q.get(q.ref(q.collection('job_posts'),
                                    ref.id())))['data'] for ref in results['data'])
                        return render_template('employee/index.html', jobs=jobs)
                    except fauna_errors.NotFound:
                        flash('Unexpected error occured! Please refresh and try again...', 'danger')
                        return render_template('employee/index.html', jobs=list())
        else:
            flash('Invalid combination! Please try again...', 'danger')
            return redirect(f'/{user_type}')
    except fauna_errors.NotFound:
        flash(f'No {user_type} found with email: {email}! Please register.', 'danger')
        return redirect(f'/{user_type}')
    except Exception as ex:
        flash('Unknown error occured! Please try again...', 'warning')
        flash(f'{ex}', 'danger')
        return redirect(url_for('index'))

@app.route('/employer/add-job', methods=['GET', 'POST'])
def add_job():
    match request.method:
        case 'GET':
            if 'email' not in session or 'user_type' not in session or 'user_id' not in session:
                flash('Please login to continue!', 'warning')
                return redirect(url_for('index'))

            return render_template('employer/new.html')
        case 'POST':
            if 'email' not in session or 'user_type' not in session or 'user_id' not in session:
                flash('Please login to continue!', 'warning')
                return redirect(url_for('index'))

            job_title = request.form.get('job_title')
            job_description = request.form.get('job_description')
            location = request.form.get('location')
            salary = int(request.form.get('salary'))
            skillsRequired = request.form.get('skillsRequired')
            datePosted = str(datetime.date.today())
            expiryDate = request.form.get('expiryDate')
            isFilled = False if request.form.get('isFilled') == 'false' else True
            employerEmail = session['email']

            try:
                result = client.query(
                    q.create(
                        q.collection('job_posts'),
                        {"data": dict(job_title=job_title,
                                    job_description=job_description,
                                    location=location,
                                    salary=salary,
                                    skillsRequired=skillsRequired,
                                    datePosted=datePosted,
                                    expiryDate=expiryDate,
                                    isFilled=isFilled,
                                    email=employerEmail)
                        }
                    )
                )
            except fauna_errors.BadRequest as ex:
                flash(f'Job already exists! Please [Edit] if necessary.', 'warning')

            try:
                results = client.query(
                    q.paginate(q.match(q.index(f'job_posts_by_email'), session['email']))
                )
                jobs = list((ref.id(), client.query(q.get(q.ref(q.collection('job_posts'),
                            ref.id())))['data']) for ref in results['data'])
                return render_template('employer/index.html', jobs=jobs)
            except fauna_errors.NotFound:
                flash(f'No jobs found with mail <{session["email"]}>', 'danger')
                return render_template('employer/index.html', jobs=list())
        case _:
            flash('Method not supported!', 'danger')
            return redirect(url_for('index'))

@app.route('/edit/jobs/<int:job_id>', methods=["GET", "POST"])
def edit_jobs(job_id):
    match request.method:
        case "GET":
            if 'email' not in session or 'user_type' not in session or 'user_id' not in session:
                flash('Please login to continue!', 'warning')
                return redirect(url_for('index'))

            result = client.query(
                q.get(q.ref(q.collection('job_posts'), job_id))
            )
            return render_template('employer/edit.html', job=result['data'], job_id=job_id)
        case "POST":
            if 'email' not in session or 'user_type' not in session or 'user_id' not in session:
                flash('Please login to continue!', 'warning')
                return redirect(url_for('index'))

            job_title = request.form.get('job_title')
            job_description = request.form.get('job_description')
            location = request.form.get('location')
            salary = int(request.form.get('salary'))
            skillsRequired = request.form.get('skillsRequired')
            datePosted = str(datetime.date.today())
            expiryDate = request.form.get('expiryDate')
            isFilled = False if request.form.get('isFilled') == 'false' else True
            employerEmail = session['email']

            try:
                result = client.query(
                    q.update(
                        q.ref(q.collection('job_posts'), job_id),
                        {"data": dict(job_title=job_title,
                                    job_description=job_description,
                                    location=location,
                                    salary=salary,
                                    skillsRequired=skillsRequired,
                                    datePosted=datePosted,
                                    expiryDate=expiryDate,
                                    isFilled=isFilled,
                                    email=employerEmail)
                        }
                    )
                )
            except Exception as ex:
                flash(f'Unable to edit the job! Please try again later...', 'warning')

            try:
                results = client.query(
                    q.paginate(q.match(q.index(f'job_posts_by_email'), session['email']))
                )
                jobs = list((ref.id(), client.query(q.get(q.ref(q.collection('job_posts'),
                            ref.id())))['data']) for ref in results['data'])
                return render_template('employer/index.html', jobs=jobs)
            except fauna_errors.NotFound:
                flash(f'No jobs found with mail <{session["email"]}>', 'danger')
                return render_template('employer/index.html', jobs=list())

        case _:
            flash('Method not supported!', 'danger')
            return redirect(url_for('index'))

@app.route('/delete/jobs/<int:job_id>', methods=["GET"])
def delete_jobs(job_id):
    try:
        result = client.query(q.delete(q.ref(q.collection('job_posts'), job_id)))
        flash(f"Job [{job_id}] deleted, successfully!", 'info')

        try:
            results = client.query(
                q.paginate(q.match(q.index(f'job_posts_by_email'), session['email']))
            )
            jobs = list((ref.id(), client.query(q.get(q.ref(q.collection('job_posts'),
                        ref.id())))['data']) for ref in results['data'])
            return render_template('employer/index.html', jobs=jobs)
        except fauna_errors.NotFound:
            flash(f'No jobs found with mail <{session["email"]}>', 'danger')
            return render_template('employer/index.html', jobs=list())

    except fauna_errors.NotFound:
        flash(f"Unable to delete a job, which doesn't exist <{job_id}>", 'danger')
        return redirect(url_for('index'))
    except Exception as ex:
        flash(f"Unexpected error occured: {ex}", 'danger')
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    if 'email' not in session or 'user_type' not in session or 'user_id' not in session:
        flash("Can't logout before login!", 'warning')
        return redirect(url_for('index'))

    session.pop('email', None)
    session.pop('user_type', None)
    session.pop('user_id', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
