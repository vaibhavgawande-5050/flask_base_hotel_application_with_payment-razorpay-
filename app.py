from flask import Flask, render_template, request,session,jsonify
import razorpay
import json
from flask_session import Session
import secrets
import os
from flask_mysqldb import MySQL
from config import *

app = Flask(__name__)

#install MYSQL workbench and connect your code editor with it ..
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '911262'
app.config['MYSQL_DB'] = 'restro_data'

mysql = MySQL(app)


# Initialize Razorpay client
client = razorpay.Client(auth=(test_key,test_secret)) # your razorpay key and secret # use test key during testing
                                                       #also need to add key in pay.html file 
# Route for the index page
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin_login')
def admin_login():

    return render_template("admin_login.html")
@app.route('/admin-dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if request.method == 'POST':
        order_id = request.form['order_id']
        if order_id :
            try:
                cur = mysql.connection.cursor()
                cur.execute("DELETE FROM orders WHERE ID = %s", (order_id))
                mysql.connection.commit()
                cur.close()
                return "Order deleted successfully"
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        else:
            return "Please enter a valid ID and confirm the ID to delete.", 400
    return render_template('admin_dashboard.html')

@app.route('/orders')
def orders():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM orders")
    orders = cur.fetchall()
    cur.close()
    return render_template('orders_data.html', orders=orders)


app.secret_key = secrets.token_hex(16)  # Generate a secret key for session encryption 

app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sessions')
Session(app)

# Admin credentials (replace with your actual database or secure storage)
ADMIN_CREDENTIALS = {
    'admin': 'password'
    # Add more admin IDs and passwords
}

@app.route('/admin_check', methods=['GET', 'POST'])
def admin_check():
    if request.method == 'POST':
        admin_id = request.form['admin_id']
        password = request.form['password']

        # Check if the admin ID and password match
        if admin_id in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[admin_id] == password:
            session['admin_id'] = admin_id  # Store the admin_id in the session
            return  render_template("admin_dashboard.html")
        else:
            error = 'Invalid Admin ID or Password'
            return render_template('admin_login.html', error=error)

    return render_template('admin_login.html')

# Route for the menu page
@app.route('/menu', methods=['GET', 'POST'])
def menu():
    # Define your menu items as lists of dictionaries
    menu_special = [
        {'name': 'Paneer Butter Masala', 'price': 300},
        {'name': 'Palak Paneer', 'price': 270},
        {'name': 'Aloo Gobi', 'price': 220},
        {'name': 'Chana Masala', 'price': 230},
        {'name': 'Dal Tadka', 'price': 210}
    ]

    roti_special = [
        {'name': 'Roti Platter with Dips', 'price': 40},
        {'name': 'Roti Curry Combo', 'price': 80},
        {'name': 'Roti Basket', 'price': 60},
        {'name': 'Masala Roti', 'price': 30},
        {'name': 'Roti (Normal)', 'price': 1}
    ]

    if request.method == 'POST':
        # Get the selected items and quantities from the request
        selected_items = request.form.getlist('menu_item')
        quantities = {item: int(request.form.get(f'quantity[{item}]', 0)) for item in selected_items}

        # Calculate the total price
        total_price = calculate_total_price(selected_items, quantities)

        # Render the order page with the selected items and total price
        return render_template('order.html', selected_items=selected_items, quantities=quantities, total_price=total_price)

    return render_template('menu.html', menu_special=menu_special, roti_special=roti_special)

@app.route('/about')
def about():
    return render_template('about.html')



@app.route('/order', methods=['POST'])
def order():
    # Define the item_prices dictionary
    global order_details,total_price
    item_prices = {
        'Paneer Butter Masala': 300,
        'Palak Paneer': 270,
        'Aloo Gobi': 220,
        'Chana Masala': 230,
        'Dal Tadka': 210,
        'Roti Platter with Dips': 40,
        'Roti Curry Combo': 80,
        'Roti Basket': 60,
        'Masala Roti': 30,
        'Roti (Normal)': 1
    }

    # Get the selected menu items and quantities from the request
    selected_items = request.form.getlist('menu_item')
    quantities = {item: int(request.form.get(f'quantity[{item}]', 0)) for item in selected_items}

    # Calculate the total price based on the selected items and quantities
    total_price = calculate_total_price(selected_items, quantities)
    total_price = float(total_price)

    # Create a list of dictionaries containing item, quantity, and price
    order_details = []
    for item, quantity in quantities.items():
        if quantity > 0:
            price = item_prices.get(item, 0)
            order_details.append({'name': item, 'quantity': quantity, 'price': price})

    print(order_details)

    return render_template('order.html', order_details=order_details, total_price=total_price)




@app.route('/payment', methods=['GET'])
def payment():
    total_price = request.args.get('total_price', 0)
    # Render the payment template with the total price
    return render_template('payment.html', total_price=total_price)

# Function to calculate the total price
def calculate_total_price(selected_items, quantities):
    global  total_price 
    total_price=0
    # Assuming you have a dictionary of item prices
    item_prices = {
        'Paneer Butter Masala': float(300),
        'Palak Paneer':float(270),
        'Aloo Gobi': float(220),
        'Chana Masala': float(230),
        'Dal Tadka': float(210),
        'Roti Platter with Dips': float(40),
        'Roti Curry Combo': float(80),
        'Roti Basket': float(60),
        'Masala Roti': float(30),
        'Roti (Normal)': float(1)
    }

    for item, quantity in quantities.items():
        if quantity > 0:
            total_price += item_prices.get(item, 0) * quantity
    print(total_price)
    return total_price

@app.route("/next",methods=['POST'])
def next_function():

    return render_template("next.html",amount=total_price)

@app.route('/place_order', methods=['POST'])
def place_order():
    global customer_name ,customer_contact, email_id,amount
    if request.method == 'POST':
        customer_name=request.form['customer_name']
        customer_contact=request.form['contact_number']
        email_id=request.form['email_id']
        amount = total_price*100  

        # Create order
        data = {
            "amount": amount,
            "currency": "INR",
            "receipt": "#11",
            "partial_payment": False  # Disallow partial payments
        }
        payment = client.order.create(data=data)

        # Render the payment template with the order details
        order_id = payment['id']
        return render_template('pay.html', order_id=order_id, name=customer_name, email=email_id, contact=customer_contact, amount=amount)

@app.route('/payment_success', methods=['POST'])
def payment_success():
    value=amount
    value=(value/100)
    payment_data = request.get_json()

    
    razorpay_payment_id = payment_data['razorpay_payment_id']
    razorpay_order_id = payment_data['razorpay_order_id']
    razorpay_signature = payment_data['razorpay_signature']
    # Verify the payment signature
    try:
        client.utility.verify_payment_signature({
            'razorpay_signature': razorpay_signature,
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id
        })
    except Exception as e:
        print("Error verifying payment signature:", e)
        return "Payment verification failed", 400

    print("in a payment success function")
    cur=mysql.connection.cursor()
    # Insert the order details into the MySQL database
    order_details_json = json.dumps(order_details)

    
    query = "INSERT INTO orders (order_id, customer_name, customer_email, customer_contact, payment_id, razorpay_signature, total_amount, order_details) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    values = (razorpay_order_id, customer_name, email_id, customer_contact, razorpay_payment_id, razorpay_signature,value, order_details_json)
    cur.execute(query, values)
    mysql.connection.commit()
    print("data store in database successfully")
    cur.close()

    return "payment successfull"

@app.route('/final')
def final():
    
    return render_template('final.html',order_details=order_details,total_price=total_price)

@app.route('/fail')
def fail():
    return render_template('fail.html')


if __name__ == '__main__':
    app.run(debug=True)