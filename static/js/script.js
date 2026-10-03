let cart = JSON.parse(localStorage.getItem("cart")) || [];


// =========================
// ADD TO CART
// =========================

function addToCart(food_id, name, price) {

    const existingItem = cart.find(item => item.food_id === food_id);

    if (existingItem) {
        existingItem.quantity++;
    } else {
        cart.push({
            food_id: food_id,
            name: name,
            price: price,
            quantity: 1
        });
    }

    localStorage.setItem("cart", JSON.stringify(cart));

    alert(name + " added to cart!");
}


// =========================
// DISPLAY CART
// =========================

function displayCart() {

    const cartItems = document.getElementById("cart-items");
    const cartTotal = document.getElementById("cart-total");

    if (!cartItems) {
        return;
    }

    cartItems.innerHTML = "";

    let total = 0;

    cart.forEach((item, index) => {

        const itemTotal = item.price * item.quantity;

        total += itemTotal;

        cartItems.innerHTML += `
            <div class="cart-item">

                <h3>${item.name}</h3>

                <p>Price: ₹${item.price}</p>

                <button onclick="decreaseQuantity(${index})">
                    ➖
                </button>

                <strong>${item.quantity}</strong>

                <button onclick="increaseQuantity(${index})">
                    ➕
                </button>

                <p>Item Total: ₹${itemTotal}</p>

                <button onclick="removeItem(${index})">
                    🗑️ Remove
                </button>

            </div>
        `;
    });

    cartTotal.innerText = "Total: ₹" + total;
}


// =========================
// INCREASE QUANTITY
// =========================

function increaseQuantity(index) {

    cart[index].quantity++;

    localStorage.setItem("cart", JSON.stringify(cart));

    displayCart();
}


// =========================
// DECREASE QUANTITY
// =========================

function decreaseQuantity(index) {

    if (cart[index].quantity > 1) {
        cart[index].quantity--;
    }

    localStorage.setItem("cart", JSON.stringify(cart));

    displayCart();
}


// =========================
// REMOVE ITEM
// =========================

function removeItem(index) {

    cart.splice(index, 1);

    localStorage.setItem("cart", JSON.stringify(cart));

    displayCart();
}


// =========================
// PLACE ORDER
// =========================

async function placeOrder() {

    // Check cart
    if (cart.length === 0) {

        alert("Your cart is empty!");

        return;
    }


    // Get delivery address
    const deliveryAddress =
        document.getElementById("delivery-address").value.trim();


    // Check delivery address
    if (deliveryAddress === "") {

        alert("Please enter your delivery address!");

        return;
    }


    // Temporary user ID
    // Later we will connect this to the logged-in user
    let user_id = 1;


    // Calculate total
    let total = 0;

    cart.forEach(item => {

        total += item.price * item.quantity;

    });


    try {

        const response = await fetch("/place_order", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                user_id: user_id,

                total: total,

                items: cart,

                delivery_address: deliveryAddress

            })

        });


        // Check server response
        if (!response.ok) {

            throw new Error(
                "Server error: " + response.status
            );

        }


        const result = await response.json();


        alert(result.message);


        // Clear cart after successful order
        cart = [];

        localStorage.removeItem("cart");

        displayCart();


    } catch (error) {

        console.error(error);

        alert(
            "Order could not be placed. Check the Flask terminal for the error."
        );

    }
}


// =========================
// LOAD CART
// =========================

displayCart();