from fastapi import FastAPI,Depends,Request,HTTPException,status
from database import db_models
from database.database import engine,get_db
from schemas import Product_form,Category,CategoryCreate,BrandSchema,ModelSchema,BrandCreateSchema
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
    
    # return request
    
    try:
        # Step 1 : Category
        if data["category_id"] == "" or data["category_id"] is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="Category ID is mandatory")
            
        # Step 2 : Brands
        if data["brand_id"] == "" or data["brand_id"] is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="Brand is mandatory")
            
        #Step 3 : Models
        if data["new_model"] is not None:
            model = db_models.Models(model_name=data["new_model"],brand_id=data["brand_id"])
            db.add(model)
            db.commit()
            db.refresh(model)
        elif data["model_id"] is not None:
            pass
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="New Model name or Existing Model name is necessary!!")
            
        # Step 4 : Products
        product = db_models.Products(name=data["name"],price=data["price"],brand_id=data["brand_id"],model_id=data["model_id"] or model.id)
        db.add(product)
        db.commit()
        db.refresh(product)
        
        # Step 5 : Sizes
        for specific_size in data["sizes"]:
            size = db_models.Sizes(sizes=specific_size,products_id=product.id)
            db.add(size)
            db.commit()
            db.refresh(size)  
            
        # Step 6 : Imaages
        for specific_img in data["images"]:
            img = db_models.Images(image_url=specific_img,product_id=product.id)
            db.add(img)
            db.commit()
            db.refresh(img)
            
        # Step 7 : ProductItem
        productItem = db_models.ProductItem(product_id=product.id,quantity=data["stock_qty"])
        db.add(productItem)
        db.commit()
        db.refresh(productItem)
        
        # Step 8 : Colors
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
    # Create new category
    new_category = db_models.ProductCategory(name=category.new_category,description=category.category_description)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

@app.post("/dashboard/category/{category}", response_model=Category,status_code=status.HTTP_200_OK)
def for_category_id(category: str,db: Session = Depends(get_db)):
    print(category)
    category_id = db.query(db_models.ProductCategory).filter_by(name=category).first()
    return category_id


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
            "brand_name": brand.brand_name,
            "brand_description": brand.brand_description,
            "product_category_id": brand.product_category_id
        }
        result.append(BrandSchema(**brand_data))

    return result

@app.post("/dashboard/brands",response_model=BrandSchema,status_code=status.HTTP_201_CREATED)
def add_brand_by_category(request: BrandCreateSchema,db: Session = Depends(get_db)):
    print(request)
    brand = db_models.Brands(brand_name=request.new_brand,brand_description=request.brand_description,product_category_id=request.category_id)
    db.add(brand)
    db.commit()
    db.refresh(brand)
    
    return brand

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

@app.post("/collections/{categoryID}",status_code=status.HTTP_200_OK)
def all_stuff(categoryID: int,db: Session = Depends(get_db)):
    
    category = db.query(db_models.ProductCategory).filter(db_models.ProductCategory.id == categoryID).first()
    
    brands = db.query(db_models.Brands).filter(db_models.Brands.product_category_id == categoryID).all()
    
    brand_ids = [brand.id for brand in brands]
    models = db.query(db_models.Models).filter(db_models.Models.brand_id.in_(brand_ids)).all() # .in_() => SQLAlchemy function to check if the column value exists in the given list
    
    model_ids = [model.id for model in models]
    products = db.query(db_models.Products).filter(db_models.Products.brand_id.in_(brand_ids),db_models.Products.model_id.in_(model_ids)).all()
    
    product_ids = [product.id for product in products]
    sizes = db.query(db_models.Sizes).filter(db_models.Sizes.products_id.in_(product_ids)).all()
    img = db.query(db_models.Images).filter(db_models.Images.product_id.in_(product_ids)).all()
    product_items = db.query(db_models.ProductItem).filter(db_models.ProductItem.product_id.in_(product_ids)).all()
    
    product_item_ids = [product_item.id for product_item in product_items]
    colors = db.query(db_models.Colors).filter(db_models.Colors.product_item_id.in_(product_item_ids)).all()
    
    return {"category": category,"brands" : brands,"models" : models,"products" :products,"sizes":sizes,"img":img,"product_items":product_items,"colors":colors}
    # return category,brands,models,products,sizes,img,product_items,colors

@app.post("/productItem/{productItemID}",status_code=status.HTTP_200_OK)
def productItemDetail(productItemID: int,db: Session = Depends(get_db)):
    product = db.query(db_models.Products).filter(db_models.Products.id == productItemID).first()
    # print(product.__dict__)
    
    size_store = []
    sizes = db.query(db_models.Sizes).filter(db_models.Sizes.products_id == product.id).all()
    for size in sizes:
        size_store.append(size)
    
    img_store = []
    img = db.query(db_models.Images).filter(db_models.Images.product_id == productItemID).all()
    for image in img:
        img_store.append(image)
        
    product_item = db.query(db_models.ProductItem).filter(db_models.ProductItem.product_id == productItemID).first()
    
    color_store = []
    color = db.query(db_models.Colors).filter(db_models.Colors.product_item_id == product_item.id).all()
    for col in color:
        color_store.append(col)
    
    # print({"Product": product,"Size":size_store,"Image":img_store,"Product_item":product_item,"Color": color_store})
    return {"Product": product,"Size":size_store,"Image":img_store,"Product_item":product_item,"Color": color_store}
    
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