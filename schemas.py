from pydantic import BaseModel,HttpUrl,validator
from typing import List

class Product_form(BaseModel):
    category: str
    category_description: str
    name: str
    price: float
    brand: str
    model: str
    images: List[HttpUrl]
    colors: List[str]
    sizes: List[str]
    stock_qty: int
    
    @validator('stock_qty')
    def stock_qty_must_be_positive(cls, value):
        if value < 1:
            raise ValueError('Quantity must be greater than 0')
        return value

    class Config:
        from_attributes = True
    