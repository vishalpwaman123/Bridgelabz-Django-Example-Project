import json
import logging
import jwt
from django.core.paginator import Paginator
from django.db import connection
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
import redis
from myproject import settings
from .services import check_product, get_uid, get_product_price, check_product_exists, update_cart, \
    get_products_from_cart, get_price, get_order_number, calc_price, get_quantity, send_email, check_productid
from myproject.custom_decorators import authenticate_user, check_product_wishlist

from myproject.custom_exceptions import ProductNotFound, CartEmpty

from myproject.custom_decorators import check_sql_exceptions

redis = redis.StrictRedis(host=settings.REDIS_HOST,
                          port=settings.REDIS_PORT, db=0)
logger = logging.getLogger('django')
with open('books/mymessages.json', 'r') as myfile:
    data = myfile.read()
obj = json.loads(data)
db = connection.cursor()

@check_sql_exceptions()
@api_view(('GET',))
def get_all_books(request):
    page_num = request.GET['page_num']
    db.execute("SELECT id,title,author,image,quantity,price,description FROM books")
    books = db.fetchall()
    count = len(books)
    paginator = Paginator(books,10)
    page_obj = paginator.get_page(page_num)
    logger.info(str(obj['book_success']))
    return render(request,'books/books.html',{'page_obj':page_obj, 'count': count})


@check_sql_exceptions()
@api_view(('GET',))
def get_book_by_name(request):
    current_url = request.resolver_match.url_name
    if current_url == 'booktitle':
        title = request.GET['title']
        db.execute("SELECT * FROM books WHERE title= %s", [title])
        books = db.fetchall()
        logger.info(str(obj['success_bookname']))
    if current_url == 'bookauthor':
        author = request.GET['author']
        db.execute("SELECT title,quantity,price FROM books WHERE author = %s", [author])
        books = db.fetchall()
        logger.info(str(obj['success_bookauthor']))
    if len(books) != 0:
        return Response(books)
    logger.warning(str(obj['no_books']))
    return Response(str(obj['no_books']), status=400)


@check_sql_exceptions()
@api_view(('GET',))
def sort_books_price(request):
    current_url = request.resolver_match.url_name
    page_num = request.GET['page_num']
    if current_url == 'priceasc':
        db.execute("SELECT title,author,image,quantity,price,description FROM books ORDER BY price ASC")
        books = db.fetchall()
        logger.info(str(obj['sorted_asc']))
    if current_url == 'pricedesc':
        db.execute("SELECT title,author,image,quantity,price,description FROM books ORDER BY price DESC")
        books = db.fetchall()
        logger.info(str(obj['sorted_desc']))
    if len(books) != 0:
        paginator = Paginator(books, 10)
        page_obj = paginator.get_page(page_num)
        return render(request,'books/books.html',{'page_obj':page_obj})
    logger.warning(str(obj['no_books']))
    return Response(str(obj['no_books']), status=400)

@api_view(('POST',))
@authenticate_user()
@check_product_wishlist()
@check_sql_exceptions()
def add_wishlist(request):
    token = request.headers.get('X-Token')
    product_id = request.GET['product_id']
    uid = get_uid(token)
    if not check_productid(product_id):
        raise ProductNotFound
    db.execute("INSERT INTO wishlist(user_id,product_id) values(%s,%s)", [uid, product_id])
    logger.info(str(obj['added_product']))
    return Response(str(obj['added_product']), status=200)


@authenticate_user()
@api_view(('GET',))
@check_sql_exceptions()
def wishlist(request):
    token = request.headers.get('X-Token')
    uid = get_uid(token)
    db.execute("SELECT product_id from wishlist WHERE user_id = %s", [uid])
    product_id = db.fetchall()
    db.execute("SELECT title,author,quantity,price from books WHERE id in %s", [product_id])
    wishlist = db.fetchall()
    logger.info(str(obj['success_wishlist']))
    return Response(wishlist)


@authenticate_user()
@api_view(('POST',))
@check_sql_exceptions()
def remove_wishlist(request):
    token = request.headers.get('X-Token')
    product_id = request.GET['product_id']
    uid = get_uid(token)
    if not check_product(product_id, uid):
        db.execute("DELETE FROM wishlist WHERE product_id=%s and user_id=%s", [product_id, uid])
        logger.info(str(obj['delete_success']))
        return Response(str(obj['delete_success']), status=200)
    else:
        logger.warning(str(obj['product_not_exist']))
        return Response(str(obj['product_not_exist']), status=400)


@authenticate_user()
@api_view(('POST',))
@check_sql_exceptions()
def add_cart(request):
    token = request.headers.get('X-Token')
    product_id = request.GET['product_id']
    quantity = request.GET['quantity']
    if not check_productid(product_id):
        raise ProductNotFound
    if not request.GET['quantity']:
        quantity = 1
    uid = get_uid(token)
    if check_product_exists(product_id, uid):
        update_cart(product_id, uid, quantity)
        logger.warning(str(obj['product_exist_cart']))
        return Response(str(obj['product_exist_cart']))
    else:
        price = get_product_price(product_id)
        db.execute("INSERT INTO cart(user_id,product_id,quantity,price) VALUES(%s,%s,%s,%s)",
                   [uid, product_id, quantity, price])
        logger.info(str(obj['added_product']))
        return Response(str(obj['added_product']), status=200)


@authenticate_user()
@api_view(('GET',))
@check_sql_exceptions()
def cart_view(request):
    token = request.headers.get('X-Token')
    uid = get_uid(token)
    db.execute("SELECT product_id,quantity,(cart.price*cart.quantity) AS price from cart WHERE user_id = %s", [uid])
    products = db.fetchall()
    logger.info(str(obj['success_cart']))
    return Response(products, status=200)


@authenticate_user()
@api_view(('POST',))
@check_sql_exceptions()
def remove_cart(request):
    token = request.headers.get('X-Token')
    product_id = request.GET['product_id']
    uid = get_uid(token)
    db.execute("DELETE FROM cart WHERE product_id=%s AND user_id=%s", [product_id, uid])
    logger.info(str(obj['delete_success']))
    return Response(str(obj['delete_success']), status=200)


@authenticate_user()
@api_view(('POST',))
@check_sql_exceptions()
def order(request):
    token = request.headers.get('X-Token')
    uid = get_uid(token)
    product_id = get_products_from_cart(uid)
    if len(product_id) == 0:
        raise CartEmpty
    order_number = get_order_number()
    total_price = calc_price(uid)
    for product in product_id:
        price = get_price(product)
        quantity = get_quantity(product)
        db.execute("INSERT INTO orders(user_id,order_num,product_id,quantity,total_price) VALUES(%s,%s,%s,%s,%s)",
                   [uid,order_number,product,quantity,price])
    send_email(uid,total_price,product_id,order_number)
    return Response(str(obj['order_placed']) % total_price)


@authenticate_user()
@api_view(('GET',))
@check_sql_exceptions()
def view_order(request):
    token = request.headers.get('X-Token')
    uid = get_uid(token)
    db.execute("SELECT order_num,product_id,quantity,total_price from orders WHERE user_id=%s",[uid])
    products = db.fetchall()
    if len(products) != 0:
        return Response(products)
    return Response(str(obj['no_orders']))
