from faunadb import query as q
from faunadb.client import FaunaClient

import os
from dotenv import load_dotenv

load_dotenv()

# Initialize the client
client = FaunaClient(secret=os.getenv("FAUNADB_SECRET"))

# Create 'employers' collection
client.query(q.create_collection({"name": "employers"}))

# Create 'employees' collection
client.query(q.create_collection({"name": "employees"}))

# Create 'job_posts' collection
client.query(q.create_collection({"name": "job_posts"}))

# Index for searching job posts by title
client.query(q.create_index({
    "name": "job_posts_by_title",
    "source": q.collection("job_posts"),
    "terms": [{"field": ["data", "title"]}]
}))

# Index for searching job posts by location
client.query(q.create_index({
    "name": "job_posts_by_location",
    "source": q.collection("job_posts"),
    "terms": [{"field": ["data", "location"]}]
}))

# Index for searching job posts by salary
client.query(q.create_index({
    "name": "job_posts_by_salary",
    "source": q.collection("job_posts"),
    "terms": [{"field": ["data", "salary"]}]
}))

# Index for searching job posts by skillsRequired
client.query(q.create_index({
    "name": "job_posts_by_skillsRequired",
    "source": q.collection("job_posts"),
    "terms": [{"field": ["data", "skillsRequired"]}]
}))

# Index for searching job posts by email
client.query(q.create_index({
    "name": "job_posts_by_email",
    "source": q.collection("job_posts"),
    "terms": [{"field": ["data", "email"]}]
}))

# Index for employers by email (useful for login)
client.query(q.create_index({
    "name": "employers_by_email",
    "source": q.collection("employers"),
    "terms": [{"field": ["data", "email"]}],
    "unique": True
}))

# Index for employees by email (also useful for login)
client.query(q.create_index({
    "name": "employees_by_email",
    "source": q.collection("employees"),
    "terms": [{"field": ["data", "email"]}],
    "unique": True
}))

print("Database setup completed!")
