# backend/routes/category.py

#APIRouter: Lets you modularize routes.
from fastapi import APIRouter, Depends, HTTPException, status #HTTPException and status: Used for standardized error responses.
from sqlalchemy.orm import Session
from backend.models.models_category import Category
from backend.models.models_user import User
from backend.schemas.schemas_category import CategoryCreate, CategoryResponse
from backend.auth import get_current_user # Gets the authenticated user from the JWT token.
from backend.database import get_db #provides db session


#Registers this group of routes under the URL path /categories
router = APIRouter(prefix="/categories", tags=["Categories"])

    #This is a route decorator that tells FastAPI:
    #HTTP Method: POST → used for creating new data.
    #Endpoint: /categories/ (because the router has a prefix "/categories").
            #when the client sends a POST request to /categories/, this function runs.
@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")
    existing = db.query(Category).filter(Category.name == category.name).first()
    if existing:
        #Checks for duplicate names to avoid redundancy.
        raise HTTPException(status_code=400, detail="Category already exists")
    #Creates, saves, and refreshes the new record in the database.
    new_category = Category(name=category.name)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

@router.get("/", response_model=list[CategoryResponse])
def get_all_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")
    return db.query(Category).all()

@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    updated_data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    category.name = updated_data.name
    db.commit()
    db.refresh(category)
    return category

@router.delete("/{category_id}", status_code=status.HTTP_200_OK)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(category)
    db.commit()
    return {"detail": f"Category '{category.name}' deleted successfully"}
