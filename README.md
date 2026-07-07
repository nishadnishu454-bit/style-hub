STYLE-HUB

STYLE-HUB is a full-featured e-commerce web application developed using Python and Django. The platform provides a complete online shopping experience with secure authentication, product browsing, shopping cart, wishlist, online payments, coupon management, wallet system, order management, product reviews, and an admin dashboard.

The application is deployed on AWS EC2 using Gunicorn and Nginx with PostgreSQL as the production database and is accessible through a custom domain.

Live Website

https://nishad.site

_____________________

Features:

 User Features

- User Registration and Authentication
- Product Listing
- Product Search
- Category Filtering
- Product Variants (Size & Color)
- Product Images Gallery
- Shopping Cart
- Wishlist
- Coupon System
- Wallet System
- Razorpay Payment Integration
- Cash on Delivery
- Order Placement
- Order Tracking
- Order Cancellation
- Product Return
- Product Reviews and Ratings
- User Profile Management
- Address Management

 ________________________
 
 Admin Features

- Admin Authentication
- Admin Dashboard
- Product Management
- Category Management
- Variant Management
- Order Management
- User Management
- Coupon Management
- Sales Reports
- Offer Management
- Review Management

________________________

Technologies Used

Backend

- Python
- Django

Database

- PostgreSQL

Frontend

- HTML
- CSS
- JavaScript

Payment Gateway

- Razorpay API

________________________

Installation:

Clone the repository:
git clone https://github.com/nishadnishu454-bit/style-hub.git


Move into the project directory:
cd STYLE-HUB


Create a virtual environment:
python -m venv svenv


Activate the virtual environment:
svenv\Scripts\activate



Install the dependencies:
pip install -r requirements.txt


Apply migrations:
python manage.py migrate


Create a superuser:
python manage.py createsuperuser

Run the development server:
python manage.py runserver


______________________

Project Structure :

STYLE-HUB/

admin_panel/
    adminauth
    admindashboard
    categorymanagement
    couponmanagement
    offermanagement
    ordermanagement
    productmanagement
    reviewmanagement
    usermanagement
    variantmanagement

user/
  addresses
  authentication
  cart
  category
  checkout
  core
  orders
  products
  profile
  wallet
  wishlist

media/
static/
templates/
manage.py
requirements.txt


_________________________

Deployment

The application is deployed on AWS EC2 using:

- Gunicorn
- Nginx
- PostgreSQL
- Custom Domain (https://nishad.site)


___________________________


Author
Muhammed Nishad K

Python Django Full Stack Developer
