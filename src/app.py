"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

import os
import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

DATABASE_PATH = Path(os.getenv("DATABASE_PATH", current_dir / "activities.sqlite"))

# Seed data for the database on first run
INITIAL_ACTIVITIES = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS activities (
                name TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                schedule TEXT NOT NULL,
                max_participants INTEGER NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS registrations (
                activity_name TEXT NOT NULL,
                email TEXT NOT NULL,
                PRIMARY KEY (activity_name, email),
                FOREIGN KEY (activity_name) REFERENCES activities(name) ON DELETE CASCADE
            )
            """
        )

        existing_count = connection.execute("SELECT COUNT(*) FROM activities").fetchone()[0]
        if existing_count > 0:
            return

        for activity_name, details in INITIAL_ACTIVITIES.items():
            connection.execute(
                """
                INSERT INTO activities (name, description, schedule, max_participants)
                VALUES (?, ?, ?, ?)
                """,
                (
                    activity_name,
                    details["description"],
                    details["schedule"],
                    details["max_participants"],
                ),
            )

            connection.executemany(
                "INSERT INTO registrations (activity_name, email) VALUES (?, ?)",
                [(activity_name, email) for email in details["participants"]],
            )


def fetch_activity(activity_name: str) -> sqlite3.Row | None:
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT name, description, schedule, max_participants
            FROM activities
            WHERE name = ?
            """,
            (activity_name,),
        ).fetchone()


def fetch_participants(activity_name: str) -> list[str]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT email
            FROM registrations
            WHERE activity_name = ?
            ORDER BY email
            """,
            (activity_name,),
        ).fetchall()
        return [row["email"] for row in rows]


def fetch_all_activities() -> dict[str, dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                a.name,
                a.description,
                a.schedule,
                a.max_participants,
                r.email
            FROM activities a
            LEFT JOIN registrations r ON r.activity_name = a.name
            ORDER BY a.name, r.email
            """
        ).fetchall()

    activities: dict[str, dict] = {}
    for row in rows:
        activity_name = row["name"]
        if activity_name not in activities:
            activities[activity_name] = {
                "description": row["description"],
                "schedule": row["schedule"],
                "max_participants": row["max_participants"],
                "participants": [],
            }

        if row["email"] is not None:
            activities[activity_name]["participants"].append(row["email"])

    return activities


@app.on_event("startup")
def on_startup() -> None:
    initialize_database()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return fetch_all_activities()


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Validate activity exists
    activity = fetch_activity(activity_name)
    if activity is None:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Validate student is not already signed up
    if email in fetch_participants(activity_name):
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO registrations (activity_name, email) VALUES (?, ?)",
            (activity_name, email),
        )

    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    # Validate activity exists
    activity = fetch_activity(activity_name)
    if activity is None:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Validate student is signed up
    if email not in fetch_participants(activity_name):
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM registrations WHERE activity_name = ? AND email = ?",
            (activity_name, email),
        )

    return {"message": f"Unregistered {email} from {activity_name}"}
