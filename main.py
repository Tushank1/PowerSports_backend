from fastapi import FastAPI,Depends,Request,HTTPException,status
from database import db_models
from database.database import engine,get_db
from schemas import Product_form
from sqlalchemy.orm import Session
from sqlalchemy import exc
import json
from fastapi.middleware.cors import CORSMiddleware

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

@app.post("/dashboard")
def product_form(request: Product_form, db: Session = Depends(get_db)):
    # Parse input data
    data = request.model_dump_json()
    data = json.loads(data)
    print(data)

    try:
        # Step 1: Add or Retrieve the Category
        category = db.query(db_models.ProductCategory).filter_by(name=data["category"]).first()
        if not category:
            category = db_models.ProductCategory(
                name=data["category"], 
                description=data.get("category_description")
            )
            db.add(category)
            db.commit()
            db.refresh(category)

        # Step 2: Add or Retrieve the Brand
        brand_obj = db.query(db_models.Brand).filter_by(brand=data["brand"]).first()
        if not brand_obj:
            brand_obj = db_models.Brand(brand=data["brand"])
            db.add(brand_obj)
            db.commit()
            db.refresh(brand_obj)

        # Step 3: Add or Retrieve the Model
        model_obj = db.query(db_models.Model).filter_by(model=data["model"]).first()
        if not model_obj:
            model_obj = db_models.Model(model=data["model"])
            db.add(model_obj)
            db.commit()
            db.refresh(model_obj)

        # Step 4: Add the Product (with Brand and Model IDs now available)
        product = db_models.Product(
            product_category_id=category.id,
            product_img=data["images"][0],  # Assuming the first image is the main image
            product_name=data["name"],
            price=data["price"],
            brand_id=brand_obj.id,  # Automatically set from the brand relationship
            model_id=model_obj.id   # Automatically set from the model relationship
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        
        # Add product images
        for image_url in data["images"]:
            db.add(db_models.ProductImage(product_id=product.id, image_url=image_url))
        
        db.commit()


        # Step 5: Add Sizes
        size_objs = []
        for size in data["sizes"]:
            size_obj = db.query(db_models.Size).filter_by(size=size).first()
            if not size_obj:
                size_obj = db_models.Size(size=size)
                db.add(size_obj)
                db.commit()
                db.refresh(size_obj)
            size_objs.append(size_obj)

        # Step 6: Add Colors
        color_objs = []
        for color in data["colors"]:
            color_obj = db.query(db_models.Color).filter_by(color=color).first()
            if not color_obj:
                color_obj = db_models.Color(color=color)
                db.add(color_obj)
                db.commit()
                db.refresh(color_obj)
            color_objs.append(color_obj)


        # Step 7: Add ProductItems for Size and Color Combinations
        for size_obj in size_objs:
            for color_obj in color_objs:
                product_item = db_models.ProductItem(
                    product_id=product.id,
                    size_id=size_obj.id,
                    color_id=color_obj.id,
                    stock_qty=data.get("stock_qty", 1)  # Default to 0 if stock is not provided
                )
                db.add(product_item)

        db.commit()  # Commit all changes
        return {"message": "Product and associated data stored successfully"}

    except Exception as e:
        db.rollback()  # Rollback the transaction in case of error
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")



@app.delete("/delete_product_from_category/{category_id}",status_code=status.HTTP_200_OK)
def destroy_product(category_id: int,product_id: int,db: Session = Depends(get_db)):
    # Step 1: Check if the category exists
    category = db.query(db_models.ProductCategory).filter(db_models.ProductCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    
    # Step 2: Find the product in the given category by product_id
    product = db.query(db_models.Product).filter(db_models.Product.id == product_id, db_models.Product.product_category_id == category.id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found in the given category")
    
    try:
        # Step 3: Delete associated ProductItems (which are connected to Size, Color, etc.)
        product_items = db.query(db_models.ProductItem).filter(db_models.ProductItem.product_id == product_id).all()
        for item in product_items:
            # Manually delete related Size and Color (if not cascading)
            db.delete(item.size)  # Delete the associated Size (if not already handled by cascade)
            db.delete(item.color)  # Delete the associated Color (if not already handled by cascade)
            db.delete(item)  # Delete the ProductItem itself
            
        # Step 4: Delete associated ProductImages
        images = db.query(db_models.ProductImage).filter(db_models.ProductImage.product_id == product_id).all()
        for image in images:
            db.delete(image)
            
        # Step 5: Optionally delete associated Brand and Model if no other product uses them
        # Check if the Brand is used by any other product
        brand_in_use = db.query(db_models.Product).filter(db_models.Product.brand_id == product.brand_id).count()
        if brand_in_use == 1:  # No other products using this brand
            db.delete(product.brand)  # Delete the Brand

        # Check if the Model is used by any other product
        model_in_use = db.query(db_models.Product).filter(db_models.Product.model_id == product.model_id).count()
        if model_in_use == 1:  # No other products using this model
            db.delete(product.model)  # Delete the Model
        
        # Step 6: Delete the ProductCategory if no other product is associated with it
        category_in_use = db.query(db_models.Product).filter(db_models.Product.product_category_id == product.product_category_id).count()
        if category_in_use == 1:  # No other products using this category
            db.delete(product.category)  # Delete the ProductCategory

        # Step 7: Delete the Product itself
        db.delete(product)

        # Step 8: Commit the transaction to delete the product and all related records
        db.commit()  # Commit the deletion process

        return {"message": "Product and its details deleted successfully"}
    except exc.SQLAlchemyError as e:
        db.rollback()  # Rollback in case of error
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error deleting product details")