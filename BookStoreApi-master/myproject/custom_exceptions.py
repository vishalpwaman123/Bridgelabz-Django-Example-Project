from rest_framework.exceptions import APIException

class ProductNotFound(APIException):
    status_code = 404
    default_detail = 'No product present with the product id'

class CartEmpty(APIException):
    status_code = 404
    default_detail = 'No products present in the Cart, Add products in cart to place order'

class ProductExist(APIException):
    status_code = 400
    default_detail = 'Product already exists in wishlist'

class BookStoreError(APIException):
    status_code = None
    default_detail = None
