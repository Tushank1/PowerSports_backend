from fastapi import APIRouter,Depends,HTTPException,status
from database import db_models
from database.database import get_db
from schemas import Product_form,Category,CategoryCreate,BrandSchema,ModelSchema,BrandCreateSchema,ModelCreateSchema
from sqlalchemy import exc
import json
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

router = APIRouter(
    prefix = "/dashboard",
    tags = ["Form"]
)


@router.post("",status_code=status.HTTP_201_CREATED)
async def product_form(request: Product_form, db: AsyncSession = Depends(get_db)):
    data = json.loads(request.model_dump_json())
    # print(data)
        
    try:
        # Step 1 : Category
        if data["category_id"] == "" or data["category_id"] is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="Category ID is mandatory")
            
        # Step 2 : Brands
        if data["brand_id"] == "" or data["brand_id"] is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="Brand is mandatory")
            
        #Step 3 : Models
        if data["model_id"] is None or data["model_id"] == "":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model is mandatory")
        
        # Step 4 : Products
        product = db_models.Products(
            name=data["name"],
            price=data["price"],
            brand_id=data["brand_id"],
            model_id=data["model_id"]
        )
        db.add(product)
        await db.flush()  # Ensures `product.id` is available

        # Step 5 : Sizes
        for specific_size in data["sizes"]:
            size = db_models.Sizes(sizes=specific_size, products_id=product.id)
            db.add(size)

        # Step 6 : Images
        for specific_img in data["images"]:
            img = db_models.Images(image_url=specific_img, product_id=product.id)
            db.add(img)

        # Step 7 : ProductItem
        productItem = db_models.ProductItem(product_id=product.id, quantity=data["stock_qty"])
        db.add(productItem)
        await db.flush()  # Ensures `productItem.id` is available

        # Step 8 : Colors
        for specific_color in data["colors"]:
            color = db_models.Colors(available_colors=specific_color, product_item_id=productItem.id)
            db.add(color)

        await db.commit()
    
        return {"message": "Product and associated data stored successfully"}
        
    except Exception as e:
        await db.rollback() 
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{e}")
    
@router.get("/categories",response_model=List[Category],status_code=status.HTTP_200_OK)
async def get_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(db_models.ProductCategory))
    category = result.scalars().all()
    return category

@router.post("/categories", response_model=Category,status_code=status.HTTP_201_CREATED)
async def add_category(category: CategoryCreate, db: AsyncSession = Depends(get_db)):
    print(category)
    new_category = db_models.ProductCategory(name=category.new_category,description=category.category_description)
    db.add(new_category)
    await db.commit()
    await db.refresh(new_category)
    return new_category

@router.post("/category/{category}", response_model=Category,status_code=status.HTTP_200_OK)
async def for_category_id(category: str,db: AsyncSession = Depends(get_db)):
    # print(category)
    result = await db.execute(select(db_models.ProductCategory).where(db_models.ProductCategory.name == category))
    category_id = result.scalars().first()
    return category_id


@router.get("/brands", response_model=list[BrandSchema],status_code=status.HTTP_200_OK)
async def get_brands_by_category(category_id: int, db: AsyncSession = Depends(get_db)):
    # Fetch brands associated with the category
    result = await db.execute(select(db_models.Brands).where(db_models.Brands.product_category_id == category_id))
    brands = result.scalars().all()
    
    if not brands:
        raise HTTPException(status_code=404, detail="No brands found for the given category ID")

    return brands

@router.post("/brands",response_model=BrandSchema,status_code=status.HTTP_201_CREATED)
async def add_brand_by_category(request: BrandCreateSchema,db: AsyncSession = Depends(get_db)):
    print(request)
    brand = db_models.Brands(brand_name=request.new_brand,brand_description=request.brand_description,product_category_id=request.category_id)
    db.add(brand)
    await db.commit()
    await db.refresh(brand)
    
    return brand

@router.get("/models",response_model=List[ModelSchema],status_code=status.HTTP_200_OK)
async def get_model_by_brand(brand_id: int,db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(db_models.Models).where(db_models.Models.brand_id == brand_id))
    models = result.scalars().all()
    
    if not models:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No models found for the given brand ID")
    
     # Convert ORM objects to Pydantic-compatible dictionaries
    serialized_models = [
        ModelSchema(
            id=model.id,
            model=model.model_name,
            brand_id=model.brand_id
        )
        for model in models
    ]
    return serialized_models

@router.post("/models",response_model=List[ModelSchema],status_code=status.HTTP_200_OK)
async def add_model_by_brandId(request:ModelCreateSchema,db: AsyncSession = Depends(get_db)):
    print(request)
    model = db_models.Models(model_name=request.new_model,brand_id=request.brand_id)
    db.add(model)
    await db.commit()
    await db.refresh(model)
    
    model_dict = {
        "id": model.id,
        "model": model.model_name,  # Ensure this matches your actual model attributes
        "brand_id": model.brand_id,
    }
    
    return [ModelSchema(**model_dict)]

@router.delete("/delete_product_from_category/{category_id}",status_code=status.HTTP_200_OK)
async def destroy_product(category_id: int,product_id: int,db: AsyncSession = Depends(get_db)):
    # Step 1: Check if the category exists
    # category = db.query(db_models.ProductCategory).filter(db_models.ProductCategory.id == category_id).first()
    category = await db.execute(select(db_models.ProductCategory).where(db_models.ProductCategory.id == category_id))
    category = category.scalars().first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    
    # brand_in_use = db.query(db_models.Products).filter(db_models.Products.brand_id == product.brand_id).count()
    brand = await db.execute(select(db_models.Brands).where(db_models.Brands.product_category_id == category))
    brand = brand.scalars().first()
    brand_in_use = await db.execute(select(db_models.Products).where(db_models.Products.brand_id == brand))
    brand_in_use = brand_in_use.scalars().count()
    if brand_in_use == 1:
        db.delete(brand)
    else:
        pass
    
    if brand_in_use == 1:  # No other products using this brand
        # brand = db.query(db_models.Brands).filter(db_models.Brands.id == product.brand_id).first()
        if brand:
            db.delete(brand)
    
    # Step 2: Find the product in the given category by product_id
    # product = db.query(db_models.Products).filter(db_models.Products.id == product_id, db_models.Products.product_category_id == category.id).first()
    product = db.execute(select(db_models.Products).where(db_models.Products.id == product_id))
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found in the given category")
    
    try:
        # Step 3: Delete associated ProductItems (which are connected to Size, Color, etc.)
        product_items = db.query(db_models.ProductItem).filter(db_models.ProductItem.product_id == product_id).all()
        for item in product_items:
            # Delete related Colors
            colors = db.query(db_models.Colors).filter(db_models.Colors.product_item_id == item.id).all()
            for color in colors:
                db.delete(color)
                
            # Delete related Size
            size = db.query(db_models.Sizes).filter(db_models.Sizes.products_id == product_id).first()
            if size:
                db.delete(size)
                
            # Delete the ProductItem itself
            db.delete(item)
            
        # Step 4: Delete associated Images
        images = db.query(db_models.Images).filter(db_models.Images.product_id == product_id).all()
        for image in images:
            db.delete(image)
            
        # Step 5: Optionally delete associated Brand and Model if no other product uses them
        # Check if the Brand is used by any other product
        

        # Check if the Model is used by any other product
        model_in_use = db.query(db_models.Products).filter(db_models.Products.model_id == product.model_id).count()
        if model_in_use == 1:  # No other products using this model
            model = db.query(db_models.Models).filter(db_models.Models.id == product.model_id).first()
            if model:
                db.delete(model)
        
        # Step 6: Optionally delete the ProductCategory if no other product is associated with it
        category_in_use = db.query(db_models.Products).filter(db_models.Products.product_category_id == product.product_category_id).count()
        if category_in_use == 1:  # No other products using this category
            db.delete(category)

        # Step 7: Delete the Product itself
        db.delete(product)

        # Step 8: Commit the transaction to delete the product and all related records
        db.commit()  # Commit the deletion process

        return {"message": "Product and its details deleted successfully"}
    except exc.SQLAlchemyError as e:
        db.rollback()  # Rollback in case of error
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error deleting product details")