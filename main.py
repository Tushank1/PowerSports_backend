from fastapi import FastAPI,Depends,HTTPException,status
from database import db_models
from database.database import async_engine,AsyncSession,get_db
from fastapi.middleware.cors import CORSMiddleware
from routers import add_product,collection

from fastapi.security import OAuth2PasswordBearer
from jose import JWTError,jwt
from datetime import datetime,timedelta,timezone
from passlib.context import CryptContext
from database.db_models import User
import schemas
from sqlalchemy.future import select
from config import settings


app = FastAPI()


# List of allowed origins (can be specific or allow all with "*")
origins = [
    "http://localhost:5173",  # Frontend URL
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (POST, GET, etc.)
    allow_headers=["*"],  # Allow all headers
)

@app.on_event("startup")
async def on_startup():
    await create_tables()
    
async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(db_models.Base.metadata.create_all)
        
app.include_router(add_product.router)
app.include_router(collection.router)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"],deprecated="auto")

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(db_models.User).where(db_models.User.email == email))
    return result.scalars().first()

async def create_user(db: AsyncSession,user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = db_models.User(first_name=user.first_name,last_name=user.last_name,email=user.email,hashed_password=hashed_password)
    db.add(db_user)
    await db.commit()
    return "complete"

@app.post("/register")
async def register_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_email(db, email=user.email)  
    
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    await create_user(db=db, user=user)  
    return {"message": "User registered successfully"}

async def authenticate_user(email: str,password: str,db: AsyncSession):
    user = await db.execute(select(db_models.User).where(db_models.User.email == email))
    user = user.scalars().first()
    if not user:
        return False
    if not pwd_context.verify(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict,expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    return encoded_jwt  

@app.post("/token")
async def login_for_access_token(
    login_request: schemas.LoginRequest, db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(login_request.email, login_request.password, db)  # Ensure it's awaited
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email,"user_id": user.id}, expires_delta=access_token_expires)

    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/verify-token")
async def verify_user_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        if email is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Token is invalid or expired"
            )
        return {"message": "Token is valid", "email": email, "user_id": user_id}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Token is invalid or expired"
        )
        
@app.post("/checkout_Billing",status_code=status.HTTP_200_OK)
async def BillingAddress(request: schemas.BillingAddress,db: AsyncSession = Depends(get_db)):
    address = db_models.BillingAddress(country=request.country,first_name=request.first_name,last_name=request.last_name,address=request.address,city=request.city,state=request.state,pincode=request.pincode,mobile_no=request.phone_no,user_id=request.user_id)
    db.add(address)
    await db.commit()
    await db.refresh(address)
    return "Done"