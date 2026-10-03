from flask import Flask, render_template, request, session, redirect
import mysql.connector

app = Flask(__name__)

# =========================
# FLASK SESSION
# =========================

app.secret_key = "cloud-food-secret-key"


# =========================
# DATABASE CONNECTION
# =========================

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="network@1233",
    database="cloud_food"
)


# =========================
# HOME PAGE
# =========================

@app.route("/")
def home():

    cursor = db.cursor(dictionary=True)

    query = """
    SELECT
        id,
        name,
        category,
        price,
        image,
        description
    FROM food
    ORDER BY id
    """

    cursor.execute(query)

    foods = cursor.fetchall()

    cursor.close()

    return render_template(
        "index.html",
        foods=foods
    )

# =========================
# CART PAGE
# =========================

@app.route("/cart")
def cart():

    return render_template("cart.html")


# =========================
# REGISTER
# =========================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        cursor = db.cursor(buffered=True)

        # Check if email already exists
        check_query = """
        SELECT id
        FROM users
        WHERE email = %s
        """

        cursor.execute(
            check_query,
            (email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:

            cursor.close()

            return "Email already registered!"

        # Insert new customer
        query = """
        INSERT INTO users
        (name, email, password, role)
        VALUES (%s, %s, %s, %s)
        """

        cursor.execute(
            query,
            (
                name,
                email,
                password,
                "customer"
            )
        )

        db.commit()

        cursor.close()

        return "Registration successful! You can now login."


    return render_template("register.html")


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        cursor = db.cursor(buffered=True)

        # First find the user by email
        query = """
        SELECT id, name, email, password, role
        FROM users
        WHERE email = %s
        """

        cursor.execute(
            query,
            (email,)
        )

        user = cursor.fetchone()

        cursor.close()


        # Check password in Python
        if user and user[3] == password:

            # Store logged-in user information
            session["user_id"] = user[0]
            session["user_name"] = user[1]
            session["role"] = user[4]

            return redirect("/")


        return "Invalid email or password!"


    return render_template("login.html")


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# =========================
# PLACE ORDER
# =========================

@app.route("/place_order", methods=["POST"])
def place_order():

    # Customer must be logged in
    if "user_id" not in session:

        return {
            "message": "Please login before placing an order."
        }, 401


    data = request.get_json()

    # IMPORTANT:
    # Get user ID from Flask session
    # NOT from JavaScript
    user_id = session["user_id"]

    total = data["total"]

    items = data["items"]

    delivery_address = data["delivery_address"]


    cursor = db.cursor()


    # =========================
    # SAVE ORDER
    # =========================

    query = """
    INSERT INTO orders
    (user_id, total, delivery_address, status)
    VALUES (%s, %s, %s, %s)
    """

    cursor.execute(
        query,
        (
            user_id,
            total,
            delivery_address,
            "Pending"
        )
    )


    order_id = cursor.lastrowid


    # =========================
    # SAVE ORDER ITEMS
    # =========================

    for item in items:

        query = """
        INSERT INTO order_items
        (order_id, food_id, quantity)
        VALUES (%s, %s, %s)
        """

        cursor.execute(
            query,
            (
                order_id,
                item["food_id"],
                item["quantity"]
            )
        )


    # Save database changes
    db.commit()

    cursor.close()


    return {
        "message": "Order placed successfully!"
    }


# =========================
# ORDER HISTORY
# =========================

@app.route("/orders")
def orders():

    # Customer must be logged in
    if "user_id" not in session:

        return redirect("/login")


    # Get actual logged-in user
    user_id = session["user_id"]


    cursor = db.cursor(dictionary=True)


    # =========================
    # GET CUSTOMER ORDERS
    # =========================

    query = """
    SELECT
        id,
        total,
        delivery_address,
        status,
        date
    FROM orders
    WHERE user_id = %s
    ORDER BY date DESC
    """

    cursor.execute(
        query,
        (user_id,)
    )

    orders = cursor.fetchall()


    # =========================
    # GET ORDER ITEMS
    # =========================

    for order in orders:

        item_query = """
        SELECT
            food.name,
            food.price,
            order_items.quantity
        FROM order_items
        JOIN food
            ON order_items.food_id = food.id
        WHERE order_items.order_id = %s
        """

        cursor.execute(
            item_query,
            (order["id"],)
        )

        order["items"] = cursor.fetchall()


    cursor.close()


    return render_template(
        "orders.html",
        orders=orders

    )
# =========================
# ADMIN DASHBOARD
# =========================

@app.route("/admin")
def admin_dashboard():

    # User must be logged in
    if "user_id" not in session:
        return redirect("/login")

    # Only admin can access
    if session.get("role") != "admin":
        return "Access denied! Admin only."

    cursor = db.cursor(dictionary=True)

    # Get all orders with customer information
    query = """
    SELECT
        orders.id,
        users.name,
        users.email,
        orders.total,
        orders.delivery_address,
        orders.status,
        orders.date
    FROM orders
    JOIN users
        ON orders.user_id = users.id
    ORDER BY orders.date DESC
    """

    cursor.execute(query)

    orders = cursor.fetchall()

    cursor.close()

    return render_template(
        "admin.html",
        orders=orders
    )
# =========================
# ADMIN UPDATE ORDER STATUS
# =========================

@app.route("/admin/update_status", methods=["POST"])
def update_status():

    # User must be logged in
    if "user_id" not in session:
        return redirect("/login")

    # Only admin can update orders
    if session.get("role") != "admin":
        return "Access denied! Admin only."

    order_id = request.form["order_id"]
    status = request.form["status"]

    cursor = db.cursor()

    query = """
    UPDATE orders
    SET status = %s
    WHERE id = %s
    """

    cursor.execute(
        query,
        (status, order_id)
    )

    db.commit()

    cursor.close()

    return redirect("/admin")
# =========================
# ADMIN ADD FOOD12
# =========================

@app.route("/admin/add_food", methods=["GET", "POST"])
def add_food():

    # User must be logged in
    if "user_id" not in session:
        return redirect("/login")

    # Only admin can add food
    if session.get("role") != "admin":
        return "Access denied! Admin only."

    if request.method == "POST":

        name = request.form["name"]
        category = request.form["category"]
        price = request.form["price"]
        image = request.form["image"]
        description = request.form["description"]

        cursor = db.cursor()

        query = """
        INSERT INTO food
        (name, category, price, image, description)
        VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(
            query,
            (
                name,
                category,
                price,
                image,
                description
            )
        )

        db.commit()
        cursor.close()

        return redirect("/admin")

    return render_template("add_food.html")

# =========================
# ADMIN EDIT FOOD
# =========================

@app.route("/admin/edit_food", methods=["GET", "POST"])
def edit_food():

    # User must be logged in
    if "user_id" not in session:
        return redirect("/login")

    # Only admin can edit food
    if session.get("role") != "admin":
        return "Access denied! Admin only."

    cursor = db.cursor(dictionary=True)

    # =========================
    # UPDATE FOOD
    # =========================

    if request.method == "POST":

        food_id = request.form["id"]
        name = request.form["name"]
        category = request.form["category"]
        price = request.form["price"]
        image = request.form["image"]
        description = request.form["description"]

        query = """
        UPDATE food
        SET
            name = %s,
            category = %s,
            price = %s,
            image = %s,
            description = %s
        WHERE id = %s
        """

        cursor.execute(
            query,
            (
                name,
                category,
                price,
                image,
                description,
                food_id
            )
        )

        db.commit()

        cursor.close()

        return redirect("/admin/edit_food")


    # =========================
    # GET ALL FOOD
    # =========================

    query = """
    SELECT
        id,
        name,
        category,
        price,
        image,
        description
    FROM food
    ORDER BY id
    """

    cursor.execute(query)

    foods = cursor.fetchall()

    cursor.close()

    return render_template(
        "edit_food.html",
        foods=foods
    )
# =========================
# START FLASK SERVER
# =========================

if __name__ == "__main__":

    app.run(debug=True)