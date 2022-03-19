from django.urls import path

from .views import get_all_books, get_book_by_name, sort_books_price, \
    add_wishlist, wishlist, remove_wishlist, add_cart, cart_view, remove_cart, order, view_order

urlpatterns = [
    path('books/', get_all_books, name='books'),
    path('books/title/', get_book_by_name, name='booktitle'),
    path('books/author/', get_book_by_name, name='bookauthor'),
    path('books/price/asc/', sort_books_price, name='priceasc'),
    path('books/price/desc/', sort_books_price, name='pricedesc'),
    path('books/wishlist/add/', add_wishlist, name='add_wishlist'),
    path('books/wishlist/', wishlist, name='wishlist'),
    path('books/wishlist/remove/', remove_wishlist, name='remove_wishlist'),
    path('cart/add/', add_cart, name='add_cart'),
    path('cart/', cart_view, name='cart'),
    path('cart/remove/', remove_cart, name='remove_cart'),
    path('order/', order, name='order'),
    path('order/view/',view_order, name='getorder')
]
