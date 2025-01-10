from fastapi import APIRouter,Depends,HTTPException,status
from database import db_models
from database.database import get_db
from schemas import Product_form,Category,CategoryCreate,BrandSchema,ModelSchema,BrandCreateSchema
from sqlalchemy import exc
import json
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

router = APIRouter(
    prefix = "/collection",
    tags = ["Products"]
)



@router.post("/{categoryID}",status_code=status.HTTP_200_OK)
async def all_stuff(categoryID: int,db: AsyncSession = Depends(get_db)):
    
    category = await db.execute(select(db_models.ProductCategory).where(db_models.ProductCategory.id == categoryID))
    category = category.scalars().first()
    
    brands = await db.execute(select(db_models.Brands).where(db_models.Brands.product_category_id == categoryID))
    brands = brands.scalars().all()
    
    brand_ids = [brand.id for brand in brands]
    # .in_() => SQLAlchemy function to check if the column value exists in the given list
    models = await db.execute(select(db_models.Models).where(db_models.Models.brand_id.in_(brand_ids)))
    models = models.scalars().all()
    
    model_ids = [model.id for model in models]
    products = await db.execute(select(db_models.Products).where(db_models.Products.brand_id.in_(brand_ids),db_models.Products.model_id.in_(model_ids)))
    products = products.scalars().all()

    
    product_ids = [product.id for product in products]
    sizes = await db.execute(select(db_models.Sizes).where(db_models.Sizes.products_id.in_(product_ids)))
    sizes = sizes.scalars().all()
    img = await db.execute(select(db_models.Images).where(db_models.Images.product_id.in_(product_ids)))
    img  = img.scalars().all()
    product_items = await db.execute(select(db_models.ProductItem).where(db_models.ProductItem.product_id.in_(product_ids)))
    product_items = product_items.scalars().all()
    
    product_item_ids = [product_item.id for product_item in product_items]
    colors = await db.execute(select(db_models.Colors.product_item_id.in_(product_item_ids)))
    colors = colors.scalars().all()
    
    return {"category": category,"brands" : brands,"models" : models,"products" :products,"sizes":sizes,"img":img,"product_items":product_items,"colors":colors}

@router.post("/productItem/{productItemID}",status_code=status.HTTP_200_OK)
async def productItemDetail(productItemID: int,db: AsyncSession = Depends(get_db)):
    product = await db.execute(select(db_models.Products).where(db_models.Products.id == productItemID))
    product = product.scalars().first()
    # print(product.__dict__)
    
    size_store = []
    sizes = await db.execute(select(db_models.Sizes).where(db_models.Sizes.products_id == product.id))
    sizes= sizes.scalars().all()
    for size in sizes:
        size_store.append(size)
    
    img_store = []
    img = await db.execute(select(db_models.Images).where(db_models.Images.product_id == productItemID))
    img = img.scalars().all()
    for image in img:
        img_store.append(image)
        
    product_item = await db.execute(select(db_models.ProductItem).where(db_models.ProductItem.product_id == productItemID))
    product_item = product_item.scalars().first()
    
    color_store = []
    color = await db.execute(select(db_models.Colors).where(db_models.Colors.product_item_id == product_item.id))
    color = color.scalars().all()
    for col in color:
        color_store.append(col)
    
    return {"Product": product,"Size":size_store,"Image":img_store,"Product_item":product_item,"Color": color_store}