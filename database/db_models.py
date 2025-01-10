from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .database import Base


class ProductCategory(Base):
    __tablename__ = "product_category"
    
    id = Column(Integer,primary_key=True,index=True)
    name = Column(String,nullable=False)
    description = Column(String,nullable=False)
    
    # Relationship to products
    products = relationship("Brands",back_populates="category",cascade="all, delete")
    
class Products(Base):
    __tablename__ = "products"
    
    id = Column(Integer,primary_key=True,index=True)
    name = Column(String,nullable=False)
    price = Column(Float,nullable=False)
    brand_id = Column(Integer,ForeignKey("brand.id"))
    model_id  = Column(Integer,ForeignKey("model.id"))
    
    # Relationship to Brands
    brand = relationship("Brands",back_populates="products")
    
    # Relationship to Models
    model = relationship("Models",back_populates="products")
    
    # Relationship to Sizes
    size = relationship("Sizes",back_populates="products",cascade="all, delete")
    
    # Relationship to Images
    images = relationship("Images",back_populates="products",cascade="all, delete")
    
    # Relationship to ProductItem
    productItem = relationship("ProductItem",back_populates="products",cascade="all, delete")
    
class Brands(Base):
    __tablename__ = "brand"
    
    id = Column(Integer,primary_key=True,index=True)
    brand_name = Column(String,nullable=False)
    brand_description: str = Column(String,nullable=False)
    product_category_id = Column(Integer,ForeignKey("product_category.id"))
    
    # Relationship to Products
    products = relationship("Products",back_populates="brand")
    
    # Relationship to ProductCategory
    category = relationship("ProductCategory",back_populates="products")
    
    #Relationship to Model
    model = relationship("Models",back_populates="brand") 
    
class Models(Base):
    __tablename__ = "model"
    
    id = Column(Integer,primary_key=True,index=True)
    model_name = Column(String,nullable=False)
    brand_id = Column(Integer,ForeignKey("brand.id"),nullable=False)

    # Relationship to Products
    products = relationship("Products",back_populates="model")
    
    #Relationship to Brand
    brand = relationship("Brands",back_populates="model")
    
class Sizes(Base):
    __tablename__ = "size"
    
    id = Column(Integer,primary_key=True,index=True)
    sizes = Column(String,nullable=False)
    products_id = Column(Integer,ForeignKey("products.id"))
    
    # Relationship to Products
    products = relationship("Products",back_populates="size")
    
class Images(Base):
    __tablename__ = "image"
    
    id = Column(Integer,primary_key=True,index=True)
    image_url = Column(String,nullable=False)
    product_id = Column(Integer,ForeignKey("products.id"))
    
    # Realtionship to Products
    products = relationship("Products",back_populates="images")
    
class ProductItem(Base):
    __tablename__ = "product_item"
    
    id = Column(Integer,primary_key=True,index=True)
    product_id = Column(Integer,ForeignKey("products.id"))
    quantity = Column(Integer,nullable=False)
    
    # Relationship to Products
    products = relationship("Products",back_populates="productItem")
    
    # relationship to Colors
    color = relationship("Colors",back_populates="product_item",cascade="all, delete")

class Colors(Base):
    __tablename__ = "color"
    
    id = Column(Integer,primary_key=True,index=True)
    available_colors = Column(String,nullable=False)
    product_item_id = Column(Integer,ForeignKey("product_item.id"))
    
    # Relationship to ProductItem
    product_item = relationship("ProductItem",back_populates="color")
    
    
    
class User(Base):
    __tablename__ = "user"
    
    id = Column(Integer,primary_key=True,nullable=False,index=True)
    first_name = Column(String,nullable=False)
    last_name = Column(String,nullable=False)
    email = Column(String,unique=True,nullable=False)
    hashed_password = Column(String)