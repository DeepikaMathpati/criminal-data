from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import sqlite3

app = FastAPI()
app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)
templates = Jinja2Templates(directory="templates")
from database import db, cursor

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {"request": request}
    )

@app.get("/criminal")
def criminal_form(request: Request):
    return templates.TemplateResponse(
        request,
        "add_criminal.html",
        {"request": request}
    )

@app.post("/criminal")
def add_criminal(
    request: Request,
    criminal_id: int = Form(...),
    name: str = Form(...),
    age: int = Form(...),
    gender: str = Form(...)
):
    sql = """
    INSERT INTO Criminal
    VALUES (?,?,?,?)
    """

    try:
        cursor.execute(
            sql,
            (criminal_id, name, age, gender)
        )
        db.commit()
    except sqlite3.IntegrityError as e:
        return templates.TemplateResponse(
            request,
            "add_criminal.html",
            {"request": request, "error": str(e)}
        )

    return RedirectResponse(
        "/",
        status_code=303
    )

@app.get("/crime")
def crime_form(request: Request):
    return templates.TemplateResponse(
        request,
        "add_crime.html",
        {"request": request}
    )

@app.post("/crime")
def add_crime(
    request: Request,
    crime_id: int = Form(...),
    crime_type: str = Form(...),
    crime_date: str = Form(...),
    crime_time: str = Form(...),
    location: str = Form(...),
    location_id: int = Form(...),
    criminal_id: int = Form(...)
):

    sql = """
    INSERT INTO Crime (
        Crime_ID, Crime_Type, Crime_Date, Crime_Time,
        Location_ID, Criminal_ID, Location
    )
    VALUES (?,?,?,?,?,?,?)
    """

    try:
        cursor.execute(
            sql,
            (
                crime_id,
                crime_type,
                crime_date,
                crime_time,
                location_id,
                criminal_id,
                location
            )
        )
        db.commit()
    except sqlite3.IntegrityError as e:
        return templates.TemplateResponse(
            request,
            "add_crime.html",
            {"request": request, "error": str(e)}
        )

    return RedirectResponse(
        "/",
        status_code=303
    )

@app.get("/crimes")
def view_crimes(request: Request):
    # Support search and filter via query parameters
    q_type = request.query_params.get("crime_type")
    q_date = request.query_params.get("date")
    q_location = request.query_params.get("location")
    q_criminal = request.query_params.get("criminal")
    q_criminal_id = request.query_params.get("criminal_id")

    base_sql = """
    SELECT
        Crime.Crime_ID,
        Crime.Crime_Type,
        Crime.Crime_Date,
        Crime.Crime_Time,
        Crime.Location,
        Crime.Location_ID,
        Criminal.Name
    FROM Crime
    LEFT JOIN Criminal ON Crime.Criminal_ID = Criminal.Criminal_ID
    """

    where = []
    params = []
    if q_type:
        where.append("Crime.Crime_Type LIKE ?")
        params.append(f"%{q_type}%")
    if q_date:
        where.append("Crime.Crime_Date = ?")
        params.append(q_date)
    if q_location:
        where.append("Crime.Location LIKE ?")
        params.append(f"%{q_location}%")
    if q_criminal_id and q_criminal_id.isdigit():
        where.append("Crime.Criminal_ID = ?")
        params.append(int(q_criminal_id))
    elif q_criminal:
        where.append("Criminal.Name LIKE ?")
        params.append(f"%{q_criminal}%")

    if where:
        base_sql += " WHERE " + " AND ".join(where)

    base_sql += " ORDER BY Crime.Crime_Date DESC"

    if params:
        cursor.execute(base_sql, tuple(params))
    else:
        cursor.execute(base_sql)

    crimes = cursor.fetchall()

    return templates.TemplateResponse(
        request,
        "crimes.html",
        {
            "request": request,
            "crimes": crimes,
            "filters": {
                "crime_type": q_type or "",
                "date": q_date or "",
                "location": q_location or "",
                "criminal": q_criminal or "",
                "criminal_id": q_criminal_id or "",
            }
        }
    )


@app.get("/criminals")
def view_criminals(request: Request):
    q_name = request.query_params.get("name")
    if q_name:
        cursor.execute(
            "SELECT Criminal_ID, Name, Age, Gender FROM Criminal WHERE Name LIKE ? ORDER BY Name",
            (f"%{q_name}%",)
        )
    else:
        cursor.execute(
            "SELECT Criminal_ID, Name, Age, Gender FROM Criminal ORDER BY Name"
        )

    criminals = cursor.fetchall()

    return templates.TemplateResponse(
        request,
        "criminals.html",
        {"request": request, "criminals": criminals, "filter_name": q_name or ""}
    )


@app.get("/criminal/{criminal_id}")
def criminal_detail(request: Request, criminal_id: int):
    cursor.execute(
        "SELECT Criminal_ID, Name, Age, Gender FROM Criminal WHERE Criminal_ID = ?",
        (criminal_id,)
    )
    criminal = cursor.fetchone()
    if not criminal:
        return RedirectResponse("/criminals", status_code=303)

    cursor.execute(
        "SELECT COUNT(*) FROM Crime WHERE Criminal_ID = ?",
        (criminal_id,)
    )
    crime_count = cursor.fetchone()[0]

    return templates.TemplateResponse(
        request,
        "criminal_detail.html",
        {"request": request, "criminal": criminal, "crime_count": crime_count}
    )


@app.post("/crime/delete/{crime_id}")
def delete_crime(request: Request, crime_id: int):
    cursor.execute("DELETE FROM Crime WHERE Crime_ID=?", (crime_id,))
    db.commit()
    return RedirectResponse("/crimes", status_code=303)


@app.post("/criminal/delete/{criminal_id}")
def delete_criminal(request: Request, criminal_id: int):
    # Delete criminal; this will leave orphaned crimes unless handled explicitly
    cursor.execute("DELETE FROM Criminal WHERE Criminal_ID=?", (criminal_id,))
    db.commit()
    return RedirectResponse("/", status_code=303)


@app.get("/crime/edit/{crime_id}")
def edit_crime_form(request: Request, crime_id: int):
    cursor.execute(
        "SELECT Crime_ID, Crime_Type, Crime_Date, Crime_Time, Location, Location_ID, Criminal_ID FROM Crime WHERE Crime_ID=?",
        (crime_id,)
    )
    crime = cursor.fetchone()
    if not crime:
        return RedirectResponse("/crimes", status_code=303)

    return templates.TemplateResponse(
        request,
        "edit_crime.html",
        {"request": request, "crime": crime}
    )


@app.post("/crime/edit/{crime_id}")
def edit_crime(request: Request, crime_id: int,
               crime_type: str = Form(...),
               crime_date: str = Form(...),
               crime_time: str = Form(...),
               location: str = Form(""),
               location_id: int = Form(None),
               criminal_id: int = Form(None)):

    try:
        cursor.execute(
            """
            UPDATE Crime SET
                Crime_Type = ?,
                Crime_Date = ?,
                Crime_Time = ?,
                Location = ?,
                Location_ID = ?,
                Criminal_ID = ?
            WHERE Crime_ID = ?
            """,
            (crime_type, crime_date, crime_time, location, location_id, criminal_id, crime_id)
        )
        db.commit()
    except sqlite3.IntegrityError as e:
        return templates.TemplateResponse(
            request,
            "edit_crime.html",
            {"request": request, "crime": (crime_id, crime_type, crime_date, crime_time, location, location_id, criminal_id), "error": str(e)}
        )

    return RedirectResponse("/crimes", status_code=303)