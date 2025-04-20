from flask import Flask, render_template,flash, request, redirect, url_for, session, jsonify
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import os
import random
from flask import send_file
import xlwt
from io import BytesIO

app = Flask(__name__)

app.config['MONGO_URI'] = 'mongodb+srv://cherifaswak:cherif**2019@renderproject1cluster.tc990wu.mongodb.net/?retryWrites=true&w=majority&appName=renderproject1Clustere'
app.config['SECRET_KEY'] = '1a2b3c'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
mongo = PyMongo(app)


# send_email 
# 🔹 Configure Flask-Mail with Gmail SMTP
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'cherifaswak@gmail.com'  # 🔹 Your Gmail
app.config['MAIL_PASSWORD'] = 'your-app-password'  # 🔹 Use App Password (not your real password)
app.config['MAIL_DEFAULT_SENDER'] = 'cherifaswak@gmail.com'

mail = Mail(app)

import os
import random

@app.route('/')
def index():
    uploads_path = os.path.join(app.static_folder, 'uploads')
    all_images = [img for img in os.listdir(uploads_path) if img.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
    random.shuffle(all_images)

    return render_template('Welcom.html', slideshow_images=all_images[:5])  # Pick 5 random

# Home Route
@app.route('/home')
def home():
    default_username = "khalfiabdelilah"
    default_password = "khalfi**aloe"
    default_role = "admin"

    products = []  # define fallback to avoid NameError

    try:
        existing_admin = mongo.db.users.find_one({"username": default_username})
        if not existing_admin:
            hashed_password = generate_password_hash(default_password)
            mongo.db.users.insert_one({
                "username": default_username,
                "password": hashed_password,
                "role": default_role
            })
        products = mongo.db.products.find()
    except Exception as e:
        print("MongoDB query failed:", e)

    return render_template('index.html', products=products)

@app.route('/send_email', methods=['GET', 'POST'])
def send_email():
    if request.method == 'POST':
        recipient = request.form['to']
        subject = request.form['subject']
        message_body = request.form['message']

        msg = Message(subject, recipients=[recipient], body=message_body)
        
        try:
            mail.send(msg)
            flash("Email sent successfully!", "success")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")

        return redirect(url_for('send_email'))

    return render_template('send_email.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    # If user is already logged in, redirect to login or homepage
    if 'user' in session:
        return render_template('register.html')
    if not  'user' in session:
        return render_template('login.html')

    if request.method == 'POST':
        username = request.form['username']
        existing_user = mongo.db.users.find_one({'username': username})

        if existing_user:
            return render_template('register.html', error="Username already exists. Try another.")

        password = generate_password_hash(request.form['password'])
        role = request.form['role']  # 'admin' or 'user'
        mongo.db.users.insert_one({'username': username, 'password': password, 'role': role})
        return redirect(url_for('login'))

    # If GET request, and user not logged in, show register page
    return render_template('register.html')


# Login User
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = mongo.db.users.find_one({'username': request.form['username']})
        if user and check_password_hash(user['password'], request.form['password']):
            session['user'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('home'))
    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.clear()  # Completely clear session
    flash("You have been logged out.", "success")
    return redirect(url_for('login'))

@app.after_request
def add_security_headers(response):
    """Add cache control headers to prevent caching."""
    response.cache_control.no_cache = True
    response.cache_control.no_store = True
    response.cache_control.must_revalidate = True
    return response

@app.route('/admin/users')
def manage_users():
    if 'user' in session and session['role'] == 'admin':
        users = mongo.db.users.find()
        return render_template('users.html', users=users)
    return redirect(url_for('login'))

@app.route('/admin/edit_user/<user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if 'user' in session and session['role'] == 'admin':
        user = mongo.db.users.find_one({'_id': ObjectId(user_id)})

        if request.method == 'POST':
            new_username = request.form['username']
            new_role = request.form['role']
            new_password = request.form['password']

            update_data = {'username': new_username, 'role': new_role}

            if new_password:  # If password is provided, update it
                hashed_password = generate_password_hash(new_password)
                update_data['password'] = hashed_password

            mongo.db.users.update_one({'_id': ObjectId(user_id)}, {'$set': update_data})
            return redirect(url_for('manage_users'))

        return render_template('edit_user.html', user=user)
    
    return redirect(url_for('login'))

@app.route('/admin/delete_user/<user_id>')
def delete_user(user_id):
    if 'user' in session and session['role'] == 'admin':
        mongo.db.users.delete_one({'_id': ObjectId(user_id)})
    return redirect(url_for('manage_users'))

# add pesonal info
@app.route('/personal_information', methods=['GET', 'POST'])
def save_personal_info():

    product_name = request.args.get('product')  # Get product name from URL
    if request.method == 'POST':
        full_name = request.form['full_name']
        phone = request.form['phone']
        email = request.form['email']
        address = request.form['address']
        product = request.form.get('product')  # hidden input
        # Check if customer already exists by phone
        existing_customer = mongo.db.personal_info.find_one({'phone': phone})

        if existing_customer:
            # Increment number_of_orders if customer exists
            # nb_order = existing_customer.get('nb_order', 0)
            mongo.db.personal_info.update_one(
                {'_id': existing_customer['_id']},
                {
                    '$set': {
                        'full_name': full_name,
                        'email': email,
                        'address': address,
                        'product': product,
                    },
                    '$inc': {'nb_order': 1}
                }
            )
        else:
            # Insert new customer with number_of_orders = 1
            mongo.db.personal_info.insert_one({
                'full_name': full_name,
                'phone': phone,
                'email': email,
                'address': address,
                'product': product,
                'nb_order': 1
            })

        return redirect(url_for('home'))  # Redirect to home page after saving

    return render_template('personal_information.html', product_name=product_name)

@app.route('/admin/costumers')
def manage_costumers():
    if 'user' in session and session['role'] == 'admin':
        costumers = mongo.db.personal_info.find()
        return render_template('costumers.html', costumers=costumers)
    else:
        return redirect(url_for('login'))


@app.route('/delete_customer/<personal_info_id>')
def delete_customer(personal_info_id):
    if 'user' in session and session['role'] == 'admin':
        # Make sure to convert string ID to ObjectId
        result = mongo.db.personal_info.delete_one({'_id': ObjectId(personal_info_id)})
        print("Deleted:", result.deleted_count)  # Optional debug log
        return redirect(url_for('manage_costumers'))
    return redirect(url_for('login'))


@app.route('/admin/add_product', methods=['GET', 'POST'])
def add_product():
    if 'user' in session and session['role'] == 'admin':
        if request.method == 'POST':
            name = request.form['name']
            price = request.form['price']
            description = request.form['description']
            image = request.files.get('image')
            upload_folder = app.config.get('UPLOAD_FOLDER', 'static/uploads')
            
            if image and image.filename:
                filename = secure_filename(image.filename)
                image_path = os.path.join(upload_folder, filename)
                image.save(image_path)
            else:
                image_path = ''
                
            mongo.db.products.insert_one({'name': name, 'price': price,'description': description,'image': image_path})
            return redirect(url_for('home'))
        return render_template('add_product.html')
    return redirect(url_for('home'))


@app.route('/admin/update_product/<product_id>', methods=['GET', 'POST'])
def update_product(product_id):
    if 'user' in session and session['role'] == 'admin':
        product = mongo.db.products.find_one({'_id': ObjectId(product_id)})

        if request.method == 'POST':
            name = request.form['name']
            price = request.form['price']
            description = request.form['description']
            image = request.files['image']

            if image and image.filename != '':
                filename = secure_filename(image.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(image_path)
                mongo.db.products.update_one(
                    {'_id': ObjectId(product_id)},
                    {'$set': {'name': name, 'price': price,'description': description, 'image': image_path}}
                )
            else:
                mongo.db.products.update_one(
                    {'_id': ObjectId(product_id)},
                    {'$set': {'name': name, 'price': price,'description': description}}
                )

            return redirect(url_for('home'))

        return render_template('update_product.html', product=product)
    return redirect(url_for('home'))


# Admin - Delete Product
@app.route('/admin/delete_product/<product_id>', methods=['GET'])
def delete_product(product_id):
    if 'user' in session and session['role'] == 'admin':
        product = mongo.db.products.find_one({'_id': ObjectId(product_id)})
        if product:
            # Delete the product image file if it exists
            if product.get('image') and os.path.exists(product['image']):
                os.remove(product['image'])

            # Delete product from database
            mongo.db.products.delete_one({'_id': ObjectId(product_id)})

    return redirect(url_for('home'))


# User - Buy Product
@app.route('/buy/<product_id>')
def buy_product(product_id):
    if 'user' in session and session['role'] == 'user':
        product = mongo.db.products.find_one({'_id': product_id})
        mongo.db.orders.insert_one({'username': session['user'], 'product': product})
        return redirect(url_for('home'))
    return redirect(url_for('login'))


#export data in xls
@app.route('/export_customers')
def export_customers():
    if 'user' in session and session['role'] == 'admin':
        #  Make sure to convert cursor to list
        customers = mongo.db.personal_info.find()

        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet('Customers')

        headers = ['Full Name', 'Phone', 'Email', 'Address']
        for idx, header in enumerate(headers):
            sheet.write(0, idx, header)

        # This will now loop through all customers
        for row_idx, customer in enumerate(customers, start=1):
            sheet.write(row_idx, 0, customer.get('full_name', ''))
            sheet.write(row_idx, 1, customer.get('phone', ''))
            sheet.write(row_idx, 2, customer.get('email', ''))
            sheet.write(row_idx, 3, customer.get('address', ''))

        output = BytesIO()
        workbook.save(output)
        output.seek(0)

        return send_file(
            output,
            as_attachment=True,
            download_name='customers.xls',
            mimetype='application/vnd.ms-excel'
        )
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
