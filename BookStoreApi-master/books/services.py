import logging

import jwt
import redis
from django.core.mail import EmailMultiAlternatives
from django.db import connection
from django.template.loader import render_to_string
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from myproject import settings
from myproject.settings import EMAIL_HOST_USER
redis = redis.StrictRedis(host=settings.REDIS_HOST,
                          port=settings.REDIS_PORT, db=0)

db = connection.cursor()

def get_uid(token):
    uid = redis.get(token)
    if uid is not None:
        uid = uid.decode('utf-8')
        return uid


def check_product(product_id,uid):
    db.execute("SELECT product_id FROM wishlist where user_id=%s", [uid])
    product = db.fetchall()
    if product_id not in str(product):
        return True
    return False

def get_product_price(product_id):
    db.execute("SELECT price FROM books WHERE id=%s", [product_id])
    product = db.fetchall()
    product = product[0][0]
    return product

def check_product_exists(product_id,uid):
    db.execute("SELECT product_id FROM cart where user_id=%s", [uid])
    product = db.fetchall()
    if product_id not in str(product):
        return False
    return True

def update_cart(product_id,uid,quantity):
    db.execute("UPDATE cart SET quantity=(quantity+%s) WHERE product_id=%s AND user_id=%s", [quantity, product_id, uid])
    db.close()

def get_price(product_id):
    db.execute("SELECT (cart.price*cart.quantity) AS total_price from cart WHERE product_id=%s", [product_id])
    total_sum = db.fetchall()
    total_sum = total_sum[0][0]
    return int(total_sum)

def get_products_from_cart(uid):
    db.execute("SELECT product_id FROM cart WHERE user_id=%s", [uid])
    products = db.fetchall()
    product = []
    for p in range(len(products)):
        product.append(products[p][0])
    return product


def get_order_number():
    db.execute("SELECT order_num FROM orders")
    order_no = db.fetchall()
    if len(order_no) == 0:
        order_no = 1000
    else:
        order_no = order_no[len(order_no) - 1][0]
    order_no = order_no+1
    return order_no

def calc_price(uid):
    db.execute("SELECT SUM(cart.price*cart.quantity) AS total_price from cart WHERE user_id=%s", [uid])
    total_sum = db.fetchall()
    total_sum = total_sum[0][0]
    return int(total_sum)

def get_quantity(product_id):
    db.execute("SELECT quantity FROM cart WHERE product_id=%s", [product_id])
    products = db.fetchall()
    quantity = []
    for p in range(len(products)):
        quantity.append(products[p][0])
    return quantity

def send_email(uid,total_amount,product_id,order_num):
    db.execute("SELECT username,email FROM user WHERE id=%s", [uid])
    user = db.fetchall()
    username = user[0][0]
    email = user[0][1]
    mail_response = []
    for product in product_id:
        db.execute("SELECT price, image, title, author FROM books where id=%s", [product])
        products = db.fetchall()
        price = products[0][0]
        image = products[0][1]
        title = products[0][2]
        author = products[0][3]
        db.execute("SELECT quantity FROM orders WHERE product_id=%s",[product])
        quantity = db.fetchall()
        quantity = quantity[0][0]
        product_info = {
            'title': title,
            'image': image,
            'price': price,
            'author': author,
            'quantity': quantity,
        }
        mail_response.append(product_info)
    try:
        mail_subject = "Message fom BookStore"
        mail_message = render_to_string('books/orders.html', {
            'user': username,
            'products': mail_response,
            'total_amount': total_amount,
            'order_num': order_num,
        })
        recipient_email = email
        subject, from_email, to = mail_subject, EMAIL_HOST_USER, recipient_email
        msg = EmailMultiAlternatives(subject, mail_message, from_email, [to])
        msg.attach_alternative(mail_message, "text/html")
        msg.send()
    except:
        logging.warning("Mail Could'not be sent.")

def check_productid(product_id):
    db.execute("SELECT count(*) from books")
    id = db.fetchall()
    id = id[0][0]
    if int(id) >= int(product_id):
        return True
    return False
