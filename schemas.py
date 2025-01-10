from pydantic import BaseModel,HttpUrl,validator,EmailStr,constr,Field,StringConstraints
from typing import List,Optional,Annotated


PasswordStr = constr(min_length=6, max_length=128)

class Product_form(BaseModel):
    category_id: int
    name: str
    price: float
    brand_id: int
    new_model: Optional[str] = None
    model_id: Optional[int] = None
    images: List[HttpUrl]
    colors: List[str]
    sizes: List[str]
    stock_qty: int
    
    @validator('stock_qty')
    def stock_qty_must_be_positive(cls, value):
        if value < 1:
            raise ValueError('Quantity must be greater than 0')
        return value
    
    @validator("images")
    def images_must_not_be_empty(cls, value):
        if not value:
            raise ValueError("At least one image is required")
        return value

    @validator("colors", "sizes", each_item=True)
    def non_empty_strings(cls, item):
        if not item.strip():
            raise ValueError("Colors and sizes must not be empty strings")
        return item

    @validator("price")
    def price_must_be_positive(cls, value):
        if value <= 0:
            raise ValueError("Price must be greater than 0")
        return value

    class Config:
        from_attributes = True
    
class Category(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
        
class CategoryCreate(BaseModel):
    new_category: str
    category_description: str
    
class BrandSchema(BaseModel):
    id: int
    brand_name: str
    brand_description: str
    product_category_id: int

    class Config:
        from_attributes = True
        
class BrandCreateSchema(BaseModel):
    new_brand: str
    brand_description: str
    category_id: int

class ModelSchema(BaseModel):
    id: int
    model: str
    brand_id: int
    
    class Config:
        from_attribute = True
        

class UserCreate(BaseModel):    
    first_name: str
    last_name: str
    email: EmailStr
    password: Annotated[str, StringConstraints(min_length=6, max_length=128)]
    
    class Config:
        from_attribute = True