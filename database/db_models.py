from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .database import Base

# Product Category Table
class ProductCategory(Base):
    __tablename__ = "product_category"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)  # Unique category name
    description = Column(String(500), nullable=True)  # Optional description

    # Relationship
    products = relationship("Product", back_populates="category", cascade="all, delete")

# Product Table
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    product_category_id = Column(Integer, ForeignKey("product_category.id"), nullable=False, index=True)
    product_img = Column(String, nullable=False)  
    product_name = Column(String(255), nullable=False)
    price = Column(Float, nullable=False)
    brand_id = Column(Integer, ForeignKey("brand.id"), nullable=False)
    model_id = Column(Integer, ForeignKey("model.id"), nullable=False)

    # Relationships
    category = relationship("ProductCategory", back_populates="products")
    product_items = relationship("ProductItem", back_populates="product", cascade="all, delete")
    brand = relationship("Brand", back_populates="products")
    model = relationship("Model", back_populates="products")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete")
    
# Product Image
class ProductImage(Base):
    __tablename__ = "product_images"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)  # Reference to the product
    image_url = Column(String, nullable=False)
    
    product = relationship("Product", back_populates="images")

# Brand Table
class Brand(Base):
    __tablename__ = "brand"
    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String(255), nullable=False, unique=True)

    # Relationship
    products = relationship("Product", back_populates="brand")

# Model Table
class Model(Base):
    __tablename__ = "model"
    id = Column(Integer, primary_key=True, index=True)
    model = Column(String(255), nullable=False, unique=True)

    # Relationship
    products = relationship("Product", back_populates="model")

# Product Item Table (Variants)
class ProductItem(Base):
    __tablename__ = "product_item"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    size_id = Column(Integer, ForeignKey("size.id"), nullable=False)
    color_id = Column(Integer, ForeignKey("color.id"), nullable=False)
    stock_qty = Column(Integer, nullable=False, default=1)  # Quantity in stock for this variant

    # Relationships
    product = relationship("Product", back_populates="product_items")
    size = relationship("Size", back_populates="product_items")
    color = relationship("Color", back_populates="product_items")

# Size Table
class Size(Base):
    __tablename__ = "size"
    id = Column(Integer, primary_key=True, index=True)
    size = Column(String(50), nullable=False)

    # Relationship
    product_items = relationship("ProductItem", back_populates="size")

# Color Table
class Color(Base):
    __tablename__ = "color"
    id = Column(Integer, primary_key=True, index=True)
    color = Column(String(50), nullable=False)

    # Relationship
    product_items = relationship("ProductItem", back_populates="color")


# # Stock Table
# class Stock(Base):
#     __tablename__ = "stock"
#     id = Column(Integer, primary_key=True, index=True)
#     qty_in_stock = Column(Integer, nullable=False,default=1)

#     product_items = relationship("ProductItem", back_populates="stock")

# User Table
class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)

    addresses = relationship("UserAddress", back_populates="user")
    carts = relationship("ShopCart", back_populates="user")

# User Address Table  
class UserAddress(Base):
    __tablename__ = "user_address"
    user_id = Column(Integer, ForeignKey("user.id"), primary_key=True)
    address_id = Column(Integer, ForeignKey("address.id"), primary_key=True)
    is_default = Column(Boolean, default=False)

    user = relationship("User", back_populates="addresses")
    address = relationship("Address", back_populates="user_addresses")

# Address Table
class Address(Base):
    __tablename__ = "address"
    id = Column(Integer, primary_key=True, index=True)
    address_1 = Column(String, nullable=False)
    address_2 = Column(String, nullable=True)
    postal_code = Column(String, nullable=False)
    address_zone_id = Column(Integer, ForeignKey("address_zone.id"), nullable=False)

    user_addresses = relationship("UserAddress", back_populates="address")
    address_zone = relationship("AddressZone", back_populates="addresses")

# Address Zone Table
class AddressZone(Base):
    __tablename__ = "address_zone"
    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, nullable=False)
    country = Column(String, nullable=False)

    addresses = relationship("Address", back_populates="address_zone")

# Shop Cart Table
class ShopCart(Base):
    __tablename__ = "shop_cart"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)

    user = relationship("User", back_populates="carts")
    cart_items = relationship("ShopCartItem", back_populates="shop_cart")

# Shop Cart Items Table
class ShopCartItem(Base):
    __tablename__ = "shop_cart_items"
    id = Column(Integer, primary_key=True, index=True)
    product_item_id = Column(Integer, ForeignKey("product_item.id"), nullable=False)
    qty = Column(Integer, nullable=False)
    shop_cart_id = Column(Integer, ForeignKey("shop_cart.id"), nullable=False)

    shop_cart = relationship("ShopCart", back_populates="cart_items")
    # product_item = relationship("ProductItem", back_populates="cart_items")
