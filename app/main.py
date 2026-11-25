# this code creates a web API that allows users to: 
# register
# log in 
# and perform calculations that are saved in a database 

# this code creates the backedn that makes our calculator app possible

# import statements
from contextlib import asynccontextmanager # helps manage processes that happen when the app starts/stops
from datetime import datetime, timezone, timedelta # works with dates/times, manages timezones, represents duration
from uuid import UUID # unique identifiers
from typing import List # allows for describing of a list of items in Python's type hints
from fastapi import Body, FastAPI, Depends, HTTPException, status
# FastAPI is the main tool used to create the API 
# Depends allows FastAPI to automatically provide things a function needs
# HTTPException allows the API to return an error to the person making a request
# status provides reasonable names for response codes
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# handles username/password login submitted through form
from sqlalchemy.orm import Session # represents a connection/session used to interact with db

# importing app files
from app.auth.dependencies import get_current_active_user
from app.models.calculation import Calculation
from app.models.user import User
from app.schemas.calculation import CalculationBase, CalculationResponse, CalculationUpdate
from app.schemas.token import TokenResponse
from app.schemas.user import UserCreate, UserResponse, UserLogin
from app.database import Base, get_db, engine

# Create tables on startup
# Note: db tables MUST exist before the API starts accepting requests
@asynccontextmanager # decorator - helps manage what happens during startup and shutdown
async def lifespan(app: FastAPI): # creates lifespan function, receives FastAPI app as input
    print("Creating tables...")
    Base.metadata.create_all(bind=engine) # tells SQLAlchemy to look at defined db models and create the db tables if they don't already exist
    print("Tables created successfully!")
    yield # startup is finished, app can run 
    # if shuttingdown, any code after yield would be cleanup code

# creating the app
app = FastAPI( # name of app
    title="Calculations API", # gives app a name
    description="API for managing calculations", # explanation
    version="1.0.0", 
    lifespan=lifespan # tells FastAPI to use the startup/shutdown process defined above
)
# this is important because the API endpoints that we create later will be attached to this application using app

# ------------------------------------------------------------------------------
# Health Endpoint
# ------------------------------------------------------------------------------
# responds to HTTP GET (retrieve info) request
@app.get("/health", tags=["health"]) # /health = URL, tags group the endpoint under the heading 'health' in documentation
# this function runs whenever someone makes a GET request to /health
def read_health():
    return {"status": "ok"}
# this endpoint is used to check whether the API is running properly

# ------------------------------------------------------------------------------
# User Registration Endpoint
# ------------------------------------------------------------------------------
# this endpoint allows users to register a new account 
# POST request = submit info or create something new 
@app.post(
    "/auth/register", # address used to register
    response_model=UserResponse, # the API will format a response based on UserResponse scheme
    status_code=status.HTTP_201_CREATED, # status code that is returned if successful
    tags=["auth"] # groups under authentication in API docs
)
# this function handles registration
def register(user_create: UserCreate, db: Session = Depends(get_db)): 
    # input 1: UserCreate schema defines what info is expected to be provided, FastAPI checks against the schema
    # input 2: FastAPI provides the database connection every time a user is registering (dependency injection)
    
    # Exclude confirm_password before passing data to User.register
    user_data = user_create.dict(exclude={"confirm_password"}) # takes the registration info and converts it into a Python dictionary
    try: # where the actual user registration happens
        user = User.register(db, user_data) # calls the register method inside the User model and passes the db connection + registration info
        db.commit() # saves the changes to the db permanently 
        db.refresh(user) # refreshes the user object with the latest info from the db
        return user # returns the newly created user to whoever made the API request 
    except ValueError as e:
        db.rollback() # reverses any uncommited db changes
        raise HTTPException( # sends an error response to the person using the API
            status_code=status.HTTP_400_BAD_REQUEST, # 400 means the request was invalid
            detail=str(e). # converts the error into readable text
        )

# summary of the endpoint: 
# - receives registration details 
# - creates a user account 
# - saves user to the db 
# - returns the result 
# if registration failes, reverses changes and returns an error

# ------------------------------------------------------------------------------
# User Login Endpoints
# ------------------------------------------------------------------------------
# there are 2 login endpoints - both authenticate a user, but accept info in different formats

# creates an endpoint for logging in using JSON
@app.post("/auth/login", response_model=TokenResponse, tags=["auth"])
def login_json(user_login: UserLogin, db: Session = Depends(get_db)): # UserLogin defines what info is expected, Depends provides db session
    """Login with JSON payload"""
    auth_result = User.authenticate(db, user_login.username, user_login.password) # calls authenticate method inside User model
    if auth_result is None: # checks if authentication has failed, returns None if not successful
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, # 401 status code
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"}, # header tells the client that Bearer authentication is expected
            # Bearer token is simply an access token that the client includes when making requests
        )
    # what happens if the authentication succeeds: 
    user = auth_result["user"] # gets users info from result
    db.commit()  # Commit the last_login update 

    # Ensure expires_at is timezone-aware
    # hanldes token expiration time
    expires_at = auth_result.get("expires_at")
    if expires_at is None:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    elif expires_at.tzinfo is None:
        xpires_at = expires_at.replace(tzinfo=timezone.utc)

    # returns successful login info
    return TokenResponse(
        access_token=auth_result["access_token"],
        refresh_token=auth_result["refresh_token"],
        token_type="bearer",
        expires_at=expires_at,
        user_id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        is_verified=user.is_verified
    )
    # TokenResponse schema determines how this response should be structurede 

# login using form data instead of JSON data
# second endpoint is in place because the OAuth2 password form integration makes it easier to test authentication using OpenAPI's features
# OAuth2PasswordRequestForm automatically extracts the user and pass from form data
@app.post("/auth/token", tags=["auth"])
def login_form(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login with form data for Swagger UI"""
    auth_result = User.authenticate(db, form_data.username, form_data.password) # calls the same authentication method in the JSON endpoint
    if auth_result is None: # checks if authentication has failed
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # if successful, returns the access token and its type
    return {
        "access_token": auth_result["access_token"],
        "token_type": "bearer"
    }
# Note: unlike /auth/login, this endpoint doesn't return the refresh token or user detailts
# only returns the info need by teh OAuth2 password form workflow

# ------------------------------------------------------------------------------
# Calculations Endpoints (BREAD)
# ------------------------------------------------------------------------------
# main functionality of the app - managing calculations
# B - browse
# R - read
# E - edit
# A - add
# D - delete

# Create (Add) Calculation – using CalculationBase so that 'user_id' from the client is ignored.
@app.post(
    "/calculations", # defines the HTTP POST endpoint 
    response_model=CalculationResponse, # specifies the structure of the response returned to the client
    status_code=status.HTTP_201_CREATED, # 201 status code 
    tags=["calculations"], # groups under Calculations in API docs
)

# function parameters
def create_calculation(
    calculation_data: CalculationBase, # receives the calculation type and input values from the client
    current_user = Depends(get_current_active_user), # users FastAPI dependency injection to id authenticated user
    db: Session = Depends(get_db) # provides db session
):
# Note: uses CalculationBase rather than accepting a user ID from the client
# app determines ownership using the authenticated user's id rather than trusting a potentially manipulated user ID in the request
    """
    Compute and persist a calculation.
    
    The endpoint reads the calculation type and inputs from the request (ignoring any extra fields),
    computes the result using the appropriate operation, and assigns the authenticated user's ID.
    """
    try:
        # Create the calculation using the factory method.
        # calls the create() factory method defined in the Calculation model
        new_calculation = Calculation.create(
            calculation_type=calculation_data.type, # requested calculation type
            user_id=current_user.id, # authenticated user ID
            inputs=calculation_data.inputs, # inputs needed to perform calculation
        )
        new_calculation.result = new_calculation.get_result() # computing the result

        # Persist the calculation to the database.
        db.add(new_calculation) # add calc to the db session
        db.commit() # commits result and saves the record
        db.refresh(new_calculation) # refreshes the record, including any generated values 
        return new_calculation # returns the  calculation back to the client 

    # error handling
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    # if the calculation factory/logic raises a ValueError, the request is rolled back and the client gets a 404
    # this is to prevent invalid calc requests from being treated as successful 

# Browse / List Calculations (for the current user)
# this calculation retreives all calcs belonging to the currently authenticated user
@app.get("/calculations", response_model=List[CalculationResponse], tags=["calculations"])
def list_calculations(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
): # authentication and db acess are provided throught dependency injection
# main query:
    calculations = db.query(Calculation).filter(Calculation.user_id == current_user.id).all()
    # db.query - starts db query against the Calculation table 
    # .filter() - adds condition to restrict records 
    # current_user.id - ensures that only calculations owned by the authenticated user are returned 
    # .all = all matching records
    return calculations # returns list of calculations

# Read / Retrieve a Specific Calculation by ID
@app.get("/calculations/{calc_id}", response_model=CalculationResponse, tags=["calculations"]) # {calc_id} - path parameter
def get_calculation(
    calc_id: str,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
# validates the calculation ID: 
# app expects calc IDs to be UUIDs
    try:
        calc_uuid = UUID(calc_id) # validates the supplied string and converts it into a UUID obj 
    # if the format is invalid, the app returns a 404
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid calculation id format.")
    # retrives the calc
    calculation = db.query(Calculation).filter( # query checks 2 conditions
        Calculation.id == calc_uuid, # calculation ID matches the requested ID
        Calculation.user_id == current_user.id # calculation belongs to the authenticated user
    ).first()
    # handles missing calculations
    if not calculation: # if no matching calculation exists, app returns 404
        raise HTTPException(status_code=404, detail="Calculation not found.")
    return calculation # requested calc is returned to the client

# Edit / Update a Calculation
@app.put("/calculations/{calc_id}", response_model=CalculationResponse, tags=["calculations"])
def update_calculation(
    calc_id: str, # identifies the calc to update
    calculation_update: CalculationUpdate, # contains the updated info
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try: # endpoint first validates the UUID and searches for the calculation. ensures only the authenticated user can make modifications
        calc_uuid = UUID(calc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid calculation id format.")
    # 
    calculation = db.query(Calculation).filter(
        Calculation.id == calc_uuid,
        Calculation.user_id == current_user.id
    ).first()
    if not calculation:
        raise HTTPException(status_code=404, detail="Calculation not found.")

    # updates the inputs
    if calculation_update.inputs is not None:
        calculation.inputs = calculation_update.inputs
        calculation.result = calculation.get_result()
    calculation.updated_at = datetime.utcnow() # updates the timestamp
    # saves/refreshes changes and returns the updated record
    db.commit()
    db.refresh(calculation)
    return calculation

# Delete a Calculation
# endpoint permanently removes a calculation belonging to the authenticated user
@app.delete("/calculations/{calc_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["calculations"])
def delete_calculation(
    calc_id: str,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try: # first validates the UUID and retrives the matching record 
        calc_uuid = UUID(calc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid calculation id format.")
    calculation = db.query(Calculation).filter(
        Calculation.id == calc_uuid,
        Calculation.user_id == current_user.id
    ).first()
    # what happens if the calculation does not exist or does not belong to the current user
    if not calculation:
        raise HTTPException(status_code=404, detail="Calculation not found.")
    # when the deletion happens
    db.delete(calculation) # marks the record for deletion
    db.commit() # permanently commits the deletion by refreshing 
    return None # returns no response body
# Note: should return 204 status code (no content) - indicates the deletion was successful

# ------------------------------------------------------------------------------
# Main Block to Run the Server
# ------------------------------------------------------------------------------
# allows FastAPI app to run directly using Python

if __name__ == "__main__": # ensures the server starts only when this file is directly expcuted
    import uvicorn # imports the ASGI server used to run FastAPI
    uvicorn.run("app.main:app", host="127.0.0.1", port=8001, log_level="info")
    # app.main: app - ids the app instance, app.main refers to the module and second app refers to FastAPI obj 
    # host - makes the server accessible through localhost 
    # port - runs the app on this port 
    # log_level='info' - displays informational server logs

# can run app by: 
# python -m app.main -or-
# uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload 
# the second command enables automatic reloading during dev

# FINAL SUMMARY:
# calculation section provides complete CRUD-style interface for managing calculations 
# authenticated user controls ownership, Calculation model handles logic, and SQLAlchemy hanldes db persistence 
# keeping these responsibilities separate makes the app easier to maintain, test, and extend