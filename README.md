# STYLE-HUB

STYLE-HUB is an e-commerce web application built using Django.

## Features

* User Authentication
* Product Listing
* Category Listing
* Variant Management
* Cart & Wishlist
* Coupon System
* Wallet System
* Order Management
* Razorpay Payment Integration
* Order Cancellation & Product Return
* Product Reviews
* Admin Dashboard

## Technologies Used

* Python
* Django
* SQLite / PostgreSQL
* HTML
* CSS
* Bootstrap
* JavaScript
* Razorpay API

## Installation

```bash
git clone <repository-url>
cd project-name
```

Create virtual environment:

```bash
python -m venv env
```

Activate virtual environment:

```bash
source env/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run migrations:

```bash
python manage.py migrate
```

Run server:

```bash
python manage.py runserver
```

## Admin Credentials

Create superuser:

```bash
python manage.py createsuperuser
```

## Project Structure

### user/

The `user` folder contains all user-side applications:

* auth
* product
* category
* wishlist
* cart
* orders
* address
* checkout
* core
* profile

### admin_panel/

The `admin_panel` folder contains all admin-side applications:

* adminauth
* admindashboard
* productmanagement
* categorymanagement
* ordermanagement
* usermanagement
* couponmanagement

## Author

Muhammed Nishad
