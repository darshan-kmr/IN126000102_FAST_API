from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional

app = FastAPI(title="Food Delivery")


foods = []
cart = []
orders = []

food_id_counter = 1
order_id_counter = 1



class Food(BaseModel):
    name: str = Field(..., min_length=2)
    price: float = Field(..., gt=0)
    category: str
    available: bool = True


class FoodUpdate(BaseModel):
    name: Optional[str]
    price: Optional[float]
    category: Optional[str]
    available: Optional[bool]


class CartItem(BaseModel):
    food_id: int
    quantity: int = Field(..., gt=0)


class Order(BaseModel):
    items: List[CartItem]
    total: float
    status: str = "Placed"

def find_food(food_id: int):
    for food in foods:
        if food["id"] == food_id:
            return food
    return None


def calculate_total(items: List[CartItem]):
    total = 0
    for item in items:
        food = find_food(item.food_id)
        if not food:
            raise HTTPException(status_code=404, detail="Food not found")
        total += food["price"] * item.quantity
    return total


def filter_foods(keyword=None):
    if keyword:
        return [f for f in foods if keyword.lower() in f["name"].lower()]
    return foods


@app.get("/")
def home():
    return {"message": "Welcome to Food Delivery API"}


@app.get("/foods")
def get_all_foods():
    return foods


@app.get("/foods/{food_id}")
def get_food(food_id: int):
    food = find_food(food_id)
    if not food:
        raise HTTPException(status_code=404, detail="Food not found")
    return food


@app.get("/foods/count")
def food_count():
    return {"total_foods": len(foods)}


@app.post("/foods", status_code=201)
def add_food(food: Food):
    global food_id_counter

    new_food = food.dict()
    new_food["id"] = food_id_counter

    foods.append(new_food)
    food_id_counter += 1

    return new_food


@app.put("/foods/{food_id}")
def update_food(food_id: int, updated: FoodUpdate):

    food = find_food(food_id)

    if not food:
        raise HTTPException(status_code=404, detail="Food not found")

    update_data = updated.dict(exclude_unset=True)

    for key, value in update_data.items():
        food[key] = value

    return food


@app.delete("/foods/{food_id}")
def delete_food(food_id: int):

    food = find_food(food_id)

    if not food:
        raise HTTPException(status_code=404, detail="Food not found")

    foods.remove(food)

    return {"message": "Food deleted"}


@app.post("/cart")
def add_to_cart(item: CartItem):

    food = find_food(item.food_id)

    if not food:
        raise HTTPException(status_code=404, detail="Food not found")

    cart.append(item)

    return {"message": "Added to cart", "cart": cart}


@app.get("/cart")
def view_cart():
    return cart


@app.delete("/cart")
def clear_cart():
    cart.clear()
    return {"message": "Cart cleared"}



@app.post("/orders")
def place_order():

    global order_id_counter

    if not cart:
        raise HTTPException(status_code=400, detail="Cart empty")

    total = calculate_total(cart)

    order = {
        "id": order_id_counter,
        "items": cart.copy(),
        "total": total,
        "status": "Placed"
    }

    orders.append(order)
    cart.clear()

    order_id_counter += 1

    return order


@app.get("/orders")
def get_orders():
    return orders


@app.put("/orders/{order_id}/deliver")
def mark_delivered(order_id: int):

    for order in orders:
        if order["id"] == order_id:
            order["status"] = "Delivered"
            return order

    raise HTTPException(status_code=404, detail="Order not found")


@app.get("/foods/search")
def search_food(keyword: Optional[str] = None):
    return filter_foods(keyword)


@app.get("/foods/browse")
def browse_foods(
    keyword: Optional[str] = None,
    sort_by: Optional[str] = Query(None),
    page: int = 1,
    limit: int = 5
):

    results = filter_foods(keyword)

    if sort_by == "price":
        results = sorted(results, key=lambda x: x["price"])

    start = (page - 1) * limit
    end = start + limit

    return {
        "page": page,
        "limit": limit,
        "results": results[start:end]
    }
