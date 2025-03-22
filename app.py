from flask import Flask, render_template, request, redirect, url_for, session
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
import os

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://localhost:27017/milk_store'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
mongo = PyMongo(app)

# Home Route
@app.route('/')
def home():
    products = mongo.db.products.find()
    return render_template('index.html', products=products)

# Register User
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']  # 'admin' or 'user'
        mongo.db.users.insert_one({'username': username, 'password': password, 'role': role})
        return redirect(url_for('login'))
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
    session.clear()
    return redirect(url_for('home'))

@app.route('/admin/add_product', methods=['GET', 'POST'])
def add_product():
    if 'user' in session and session['role'] == 'admin':
        if request.method == 'POST':
            name = request.form['name']
            price = request.form['price']
            image = request.files.get('image')
            upload_folder = app.config.get('UPLOAD_FOLDER', 'static/uploads')
            
            if image and image.filename:
                filename = secure_filename(image.filename)
                image_path = os.path.join(upload_folder, filename)
                image.save(image_path)
            else:
                image_path = ''
                
            mongo.db.products.insert_one({'name': name, 'price': price, 'image': image_path})
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
            image = request.files['image']

            update_data = {'name': name, 'price': price}

            # If a new image is uploaded, update it; otherwise, keep the old image
            if image and image.filename:
                filename = secure_filename(image.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(image_path)
                update_data['image'] = image_path  # Update only if a new image is provided

            mongo.db.products.update_one({'_id': ObjectId(product_id)}, {'$set': update_data})
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

if __name__ == '__main__':
    app.run(debug=True)
