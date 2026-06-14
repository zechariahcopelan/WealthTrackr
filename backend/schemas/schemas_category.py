# ~/Documents/WealthTrackr/schemas/schemas_category.py
from pydantic import BaseModel, validator
from typing import Optional

class CategoryCreate(BaseModel):
    name: str
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Category name cannot be empty')
        if len(v.strip()) > 50:
            raise ValueError('Category name must be less than 50 characters')
        return v.strip()
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "name": "Food & Dining"
            }
        }

class CategoryResponse(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Food & Dining"
            }
        }

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Category name cannot be empty')
            if len(v.strip()) > 50:
                raise ValueError('Category name must be less than 50 characters')
            return v.strip()
        return v
    
    class Config:
        from_attributes = True
