# Job Search Platform

A Flask-based web application for job listings and applications. This project provides functionality for both employers and employees to register, post job listings, and apply for jobs.

## Project Structure

```
.
├── bin
├── include
├── lib
├── lib64
├── pyvenv.cfg
├── requirements.txt
└── src
    ├── app.py
    ├── setup_db.py
    └── templates
        ├── employee
        │   ├── index.html
        │   └── layout.html
        ├── employer
        │   ├── edit.html
        │   ├── index.html
        │   ├── layout.html
        │   └── new.html
        ├── index.html
        └── register_login.html
```

## Prerequisites

- Python 3.11
- Docker (Optional)

## Installation

1. Navigate to the project directory:
   ```
   cd path_to_directory
   ```

2. (Recommended) Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install required packages:
   ```
   pip install -r requirements.txt
   ```

4. Run the Flask application:
   ```
   python src/app.py
   ```

## Docker Deployment (Optional)

1. Build the Docker image:
   ```
   docker build -t <your_flask_app_name> .
   ```

2. Run the Docker container:
   ```
   docker run -d -p 5000:5000 --name flask_container <your_flask_app_name>
   ```

Access the Flask application at `http://localhost:5000`.

## Features

- Employer registration and login.
- Employee registration and login.
- Employers can post new job listings.
- Employers can edit job listings.
- Employers can delete job listings.
- Employees can search for job listings and apply.

## License

[MIT](./LICENSE)
