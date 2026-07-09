# STYLE-HUB

STYLE-HUB is a full-featured e-commerce web application developed using **Python and Django**. The platform provides a complete online shopping experience with secure authentication, product browsing, shopping cart, wishlist, online payments, coupon management, wallet system, order management, product reviews, and an admin dashboard.

The application is deployed on **AWS EC2** using **Gunicorn and Nginx**, with **PostgreSQL** as the production database. The website is accessible through a custom domain.

## Live Website

🔗 https://nishad.site

---

# Features

## User Features

* User Registration and Authentication
* Product Listing
* Product Search
* Category Filtering
* Product Variants (Size & Color)
* Product Image Gallery
* Shopping Cart Management
* Wishlist Management
* Coupon System
* Wallet System
* Razorpay Payment Integration
* Cash on Delivery
* Order Placement
* Order Tracking
* Order Cancellation
* Product Return
* Product Reviews and Ratings
* User Profile Management
* Address Management

---

## Admin Features

* Admin Authentication
* Admin Dashboard
* Product Management
* Category Management
* Product Variant Management
* Order Management
* User Management
* Coupon Management
* Sales Reports
* Offer Management
* Review Management

---

# Technologies Used

## Backend

* Python
* Django

## Database

* PostgreSQL

## Frontend

* HTML
* CSS
* JavaScript

## Payment Gateway

* Razorpay API

---

# Installation

## Clone the Repository

```bash
git clone https://github.com/nishadnishu454-bit/style-hub.git
```

## Move into the Project Directory

```bash
cd STYLE-HUB
```

## Create Virtual Environment

```bash
python -m venv svenv
```

## Activate Virtual Environment

### Windows

```bash
svenv\Scripts\activate
```

### Linux / Mac

```bash
source svenv/bin/activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Apply Database Migrations

```bash
python manage.py migrate
```

## Create Superuser

```bash
python manage.py createsuperuser
```

## Run Development Server

```bash
python manage.py runserver
```

---

# Project Structure

```
STYLE-HUB/

│
├── admin_panel/
│   ├── adminauth
│   ├── admindashboard
│   ├── categorymanagement
│   ├── couponmanagement
│   ├── offermanagement
│   ├── ordermanagement
│   ├── productmanagement
│   ├── reviewmanagement
│   ├── usermanagement
│   └── variantmanagement
│
├── user/
│   ├── addresses
│   ├── authentication
│   ├── cart
│   ├── category
│   ├── checkout
│   ├── core
│   ├── orders
│   ├── products
│   ├── profile
│   ├── wallet
│   └── wishlist
│
├── media/
│
├── static/
│
├── templates/
│
├── manage.py
│
└── requirements.txt
```

---

# Deployment

The application is deployed on **AWS EC2** using:

* AWS EC2
* Gunicorn
* Nginx
* PostgreSQL
* Custom Domain

Live URL:

🔗 https://nishad.site

---

# Author

**Muhammed Nishad K**

Python Django Full Stack Developer
