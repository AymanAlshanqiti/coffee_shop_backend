from decimal import Decimal

from rest_framework.generics import (
    ListAPIView,
    RetrieveAPIView,
    RetrieveUpdateAPIView,
    CreateAPIView,
    DestroyAPIView,
)

## Status Serializers ##
from .serializers import (
    StatusListSerializer,
)
## Product Serializers ##
from .serializers import (
	ProductListSerializer,
	ProductDetailSerializer,
)


## Order ##
from .serializers import (
    OrderListSerializer,
    OrderDetailSerializer,
    OrderCreateUpdateSerializer,
)

## OrderProduct serializers ##
from .serializers import (
    OrderProductSerializer,
    OrderProductCreateUpdateSerializer,
    OrderProductQuantityUpdateSerializer
)

## Permissions ##
from rest_framework.permissions import (
	AllowAny,
	IsAuthenticated,
	IsAdminUser
)

from rest_framework.filters import (SearchFilter, OrderingFilter)

## MODELS ##
from .models import Product
from .models import Status
from .models import Profile
from .models import Order
from .models import OrderProduct
from django.contrib.auth.models import User


from .serializers import (
    UserCreateSerializer,  
    ProfileDetailSerializer, 
    ProfileCreateUpdateSerializer
)


from rest_framework.views import APIView

from django.http import Http404
from rest_framework.response import Response
from rest_framework import status




class UserCreateAPIView(CreateAPIView):
    serializer_class = UserCreateSerializer


class ProfileDetailView(RetrieveAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileDetailSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'profile_id'

class ProfileDetailDetailView(RetrieveAPIView):

    permission_classes = [IsAuthenticated, ]
    def get(self, request, format=None):
        print("=======ProfileDetailDetailView=======")
        print("customer => request.user: ", request.user)

        profile = Profile.objects.get(customer=request.user)

        print("profile: ", profile)

        serializer = ProfileDetailSerializer(profile, context= {"request": request})
        return Response(serializer.data)


### Old profile update API ###
class ProfileUpdateView(APIView):
    def get_object(self, pk):
        try:
            return Profile.objects.get(pk=pk)
        except Profile.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        profile = self.get_object(pk)
        serializer = ProfileDetailSerializer(profile)
        return Response(serializer.data)


    def put(self, request, pk, format=None):
        profile = self.get_object(pk)

        print("========Profile Update========")
        print(request.data)
        print("========Profile Update========")

        data= {"image": request.data['image']} if request.data.get('image') else {"image": None}
        serializer = ProfileCreateUpdateSerializer(profile, data=data)
        user= profile.customer
        # user.update(**request.data['customer'])
        
        user.first_name= request.data['customer']['first_name']
        user.last_name= request.data['customer']['last_name']
        user.save()

        if serializer.is_valid():
            serializer.save()
            return Response(ProfileDetailSerializer(profile).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileUpdateUpdateView(APIView):
    def get_object(self, user):
        try:
            return Profile.objects.get(customer=user)
        except Profile.DoesNotExist:
            raise Http404

    def get(self, request, user, format=None):
        profile = self.get_object(request.user)
        serializer = ProfileDetailSerializer(profile)
        return Response(serializer.data)


    def put(self, request):
        profile = self.get_object(request.user)

        data= {"image": request.data['image']} if request.data.get('image') else {"image": None}
        serializer = ProfileCreateUpdateSerializer(profile, data=data)
        user= profile.customer
        
        user.first_name= request.data['customer']['first_name']
        user.last_name= request.data['customer']['last_name']
        user.save()

        if serializer.is_valid():
            serializer.save()
            return Response(ProfileDetailSerializer(profile).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# No need for listing 
class StatusListView(ListAPIView):
    queryset = Status.objects.filter(is_active=True)
    serializer_class = StatusListSerializer

    
class ProductListView(ListAPIView):
	queryset = Product.objects.all()
	serializer_class = ProductListSerializer
	permission_classes = [AllowAny, ]
	search_fields = ['name',]
	filter_backends = [OrderingFilter, SearchFilter]


# only need list API view 
class ProductDetailView(RetrieveAPIView):
	queryset = Product.objects.all()
	serializer_class = ProductDetailSerializer
	lookup_field = 'id'
	lookup_url_kwarg = 'product_id'
	permission_classes = [AllowAny, ]


## Order APIs views ##
## this's might be not needed, check profile detail order list. 
class OrderListView(ListAPIView):
    serializer_class = OrderListSerializer
    permission_classes = [IsAuthenticated, ]

    def get_queryset(self):
        return Order.objects.filter(ordered_by=self.request.user.profile)


class OrderDetailView(RetrieveAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderDetailSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'order_id'
    permission_classes = [IsAuthenticated, ]


class OrderCreateView(CreateAPIView):
    serializer_class = OrderCreateUpdateSerializer
    permission_classes =[IsAuthenticated, ]

    def perform_create(self, serializer):
      serializer.save(ordered_by=self.request.user.profile)

class OrderStatusUpdateView(RetrieveUpdateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderCreateUpdateSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'order_id'
    permission_classes = [IsAuthenticated, ]

## Order Products APIs views

# Creating an orderProduct
class OrderProductCreateView(CreateAPIView):
    serializer_class= OrderProductCreateUpdateSerializer
    permission_classes =[IsAuthenticated, ]

    def post(self, request):
        print("========OrderProductCreateView========")
        print("self: ", self.serializer_class)
        print("request: ", request.data)
        
        order_id = request.data['order']
        product_id = request.data['product']
        quantity = request.data['quantity']

        order_obj = Order.objects.get(id=order_id)
        product_obj = Product.objects.get(id=product_id)
        
        new_order_prod, created = order_obj.order_products.get_or_create(product=product_obj)

        print("=========get_or_create========")
        print("new_order_prod: ", vars(new_order_prod))
        print("created: ", created)

        if created:
            new_order_prod.total_price = product_obj.price * Decimal(quantity)
            new_order_prod.quantity = quantity
        else:
            print("int(quantity): ", int(quantity))
            print("new_order_prod.quantity: ", new_order_prod.quantity)
            new_order_prod.quantity += int(quantity)
            new_order_prod.total_price += product_obj.price * Decimal(quantity)
            print("new_order_prod: ", vars(new_order_prod))

        new_data = {
            'order': order_id,
            'product': product_id,
            'quantity': new_order_prod.quantity
        }


        # new_order_prod.save()

        serializer = self.serializer_class(new_order_prod, data=new_data)

        print("=========Serializer========")
        print("serializer: ", serializer)
        print("vars(serializer): ", vars(serializer))
        print("=========END Serializer END========")

        if serializer.is_valid():
            serializer.save()
            return Response(OrderProductSerializer(new_order_prod).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# maybe we can use the same serializer as the create API view
class OrderProductQuantityUpdateView(RetrieveUpdateAPIView):
    queryset = OrderProduct.objects.all()
    serializer_class = OrderProductQuantityUpdateSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'orderproduct_id'
    permission_classes = [IsAuthenticated, ]

    def perform_update(self, serializer):
        print("=========OrderProductQuantityUpdateView========")
        print("serializer: ", serializer)
        print("vars(serializer): ", vars(serializer))

        print("serializer.instance: ", serializer.instance)
        quantity = serializer.validated_data['quantity']
        order_prod = serializer.instance
        # prod_obj = Product.objects.get(id= order_prod.product.id)
        prod_obj = order_prod.product

        print("prod_obj: ", prod_obj)
        print("order_prod.product: ", order_prod.product)

        order_prod.total_price = prod_obj.price * Decimal(quantity)

        print("order_prod.total_price: ", order_prod.total_price)
        # print("dir(self): ", dir(self))
        # print("vars(self): ", vars(self))
        # print("queryset: ", self.get_queryset())
        

        # print("quantity: ", data['quantity'])

        print("=========END OrderProductQuantityUpdateView END========")
        serializer.save()

# No need for this view AT ALL
class OrderProductDetailView(RetrieveAPIView):
    queryset = OrderProduct.objects.all()
    serializer_class = OrderProductSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'orderproduct_id'
    permission_classes = [IsAuthenticated, ] 

class OrderProductDeleteView(DestroyAPIView):
    queryset = OrderProduct.objects.all()
    lookup_field = 'id'
    lookup_url_kwarg = 'orderproduct_id'
    permission_classes = [IsAuthenticated, ] 