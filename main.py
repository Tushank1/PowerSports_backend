from fastapi import FastAPI,Depends,Request,HTTPException,status
from database import db_models
from database.database import engine,get_db
from schemas import Product_form,Category,CategoryCreate,BrandSchema,ModelSchema
from sqlalchemy.orm import Session
from sqlalchemy import exc
import json
from fastapi.middleware.cors import CORSMiddleware
from typing import List

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

db_models.Base.metadata.create_all(engine)
    
@app.post("/dashboard",status_code=status.HTTP_201_CREATED)
def product_form(request: Product_form, db: Session = Depends(get_db)):
    data = request.model_dump_json()
    data = json.loads(data)
    print(data)
    
    try:
        # Step 1 : Category
        if data["category"] == "" or data["category"] is None or data["category"] == "string":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="Category name is mandatory")
        else:
            category = db.query(db_models.ProductCategory).filter_by(name=data["category"]).first()
            if not category:
                if data["category_description"] is None or data["category_description"] == "" or data["category_description"] == "string":
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="Category Description is mandatory")
                else:
                    category = db_models.ProductCategory(name=data["category"],description=data["category_description"])
                    db.add(category)
                    db.commit()
                    db.refresh(category)
            
        # Step 2 : Brands
        if data["brand"] == "" or data["brand"] is None or data["brand"] == "string":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="Brand is mandatory")
        else:
            brand = db.query(db_models.Brands).filter_by(brand_name=data["brand"]).first()
            if not brand:
                brand = db_models.Brands(brand_name=data["brand"],product_category_id=category.id)
                db.add(brand)
                db.commit()
                db.refresh(brand)
            
        #Step 3 : Models
        if data["model"] == "" or data["model"] is None or data["model"] == "string":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="Model is mandatory")
        else:
            model = db.query(db_models.Models).filter_by(model_name=data["model"]).first()
            if not model:
                model = db_models.Models(model_name=data["model"],brand_id=brand.id)
                db.add(model)
                db.commit()
                db.refresh(model)
            
        # Step 4 : Products
        if data["name"] == "" or data["name"] is None or data["name"] == "string" :
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="Name is mandatory")
        elif data["price"] < 1 or data["price"] is None or not isinstance(data["price"], (int, float)):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="Price is mandatory")
        else:
            product = db_models.Products(name=data["name"],price=data["price"],brand_id=brand.id,model_id=model.id)
            db.add(product)
            db.commit()
            db.refresh(product)  
        
        # Step 5 : Sizes
        if not data["sizes"] or data["sizes"] == [""] or data["sizes"] == ["string"] or data["sizes"] == "string":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="Size is mandatory")
        else:
            for specific_size in data["sizes"]:
                size = db_models.Sizes(sizes=specific_size,products_id=product.id)
                db.add(size)
                db.commit()
                db.refresh(size)  
            
        # Step 6 : Imaages
        if not data["images"] or data["images"] == [""] or data["images"] == ["https://example.com/"] or data["images"] == "https://example.com/":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="Proper Image URL is mandatory")
        else:
            for specific_img in data["images"]:
                img = db_models.Images(image_url=specific_img,product_id=product.id)
                db.add(img)
                db.commit()
                db.refresh(img)
            
        # Step 7 : ProductItem
        if data["stock_qty"] < 1 or data["stock_qty"] is None or not isinstance(data["stock_qty"], int):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="Quantity is mandatory")
        else:
            productItem = db_models.ProductItem(product_id=product.id,quantity=data["stock_qty"])
            db.add(productItem)
            db.commit()
            db.refresh(productItem)
        
        # Step 8 : Colors
        if not data["colors"] or data["colors"] == [""] or data["colors"] == ["string"] or data["colors"] == "string":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="Color is mandatory")
        else:
            for specific_color in data["colors"]:
                color = db_models.Colors(available_colors=specific_color,product_item_id=productItem.id)
                db.add(color)
                db.commit()
                db.refresh(color)
        
        return {"message": "Product and associated data stored successfully"}
        
    except Exception as e:
        db.rollback()  # Rollback the transaction in case of error
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{e}")
    
@app.get("/dashboard/categories",response_model=List[Category],status_code=status.HTTP_200_OK)
def get_categories(db: Session = Depends(get_db)):
    category = db.query(db_models.ProductCategory).all()
    return category

@app.post("/dashboard/categories", response_model=Category,status_code=status.HTTP_201_CREATED)
def add_category(category: CategoryCreate, db: Session = Depends(get_db)):
    print(category)
    # Check if the category already exists
    existing_category = db.query(db_models.ProductCategory).filter_by(name=category.name).first()
    if existing_category:
        raise HTTPException(status_code=400, detail="Category already exists.")

    # Create new category
    new_category = db_models.ProductCategory(name=category.name,description=category.category_description)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category


@app.get("/dashboard/brands", response_model=list[BrandSchema],status_code=status.HTTP_200_OK)
def get_brands_by_category(category_id: int, db: Session = Depends(get_db)):
    # Fetch brands associated with the category
    # print(category_id)
    brands = db.query(db_models.Brands).filter(db_models.Brands.product_category_id == category_id).all()
    
    if not brands:
        raise HTTPException(status_code=404, detail="No brands found for the given category ID")
    # Manually map the ORM object to Pydantic model
    result = []
    for brand in brands:
        # print(brand.__dict__)
        # Manually create a dictionary and pass it to the Pydantic schema
        brand_data = {
            "id": brand.id,
            "name": brand.brand_name,
            "product_category_id": brand.product_category_id
        }
        result.append(BrandSchema(**brand_data))

    return result

@app.get("/dashboard/models",response_model=List[ModelSchema],status_code=status.HTTP_200_OK)
def get_model_by_brand(brand_id: int,db: Session = Depends(get_db)):
    models = db.query(db_models.Models).filter(db_models.Models.brand_id == brand_id).all()
    
    if not models:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No models found for the given brand ID")
    
    result = []
    for model in models:
        print(model.__dict__)
        model_data = {
            "id" : model.id,
            "model": model.model_name,
            "brand_id": model.brand_id
        }
        result.append(ModelSchema(**model_data))
    print(result)
    return result

    
@app.delete("/delete_product_from_category/{category_id}",status_code=status.HTTP_200_OK)
def destroy_product(category_id: int,product_id: int,db: Session = Depends(get_db)):
    # Step 1: Check if the category exists
    category = db.query(db_models.ProductCategory).filter(db_models.ProductCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    
    # Step 2: Find the product in the given category by product_id
    product = db.query(db_models.Products).filter(db_models.Products.id == product_id, db_models.Products.product_category_id == category.id).first()
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
        brand_in_use = db.query(db_models.Products).filter(db_models.Products.brand_id == product.brand_id).count()
        if brand_in_use == 1:  # No other products using this brand
            brand = db.query(db_models.Brands).filter(db_models.Brands.id == product.brand_id).first()
            if brand:
                db.delete(brand)

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