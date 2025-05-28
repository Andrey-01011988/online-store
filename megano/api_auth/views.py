import json

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema_view, extend_schema

from .models import Profile
from .serializers import SignInSerializer, SignUpSerializer



class SignInView(APIView):
    def post(self, request):
        serialized_data = list(request.POST.keys())[0]
        user_data = json.loads(serialized_data)
        username = user_data.get("username")
        password = user_data.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return Response(status=status.HTTP_201_CREATED) # статусы такие берутся от сюда from rest_framework import status
        
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

class SignUpView(APIView):
    def post(self, request):
        # print("request.body:", request.body)
        serialized_data = list(request.data.keys())[0]
        # print("serialized_data:", serialized_data)
        user_data = json.loads(serialized_data)
        # print("user_data:", user_data)
        name = user_data.get("name")
        # print("name:", name)
        username = user_data.get("username")
        # print("username:",username)
        password = user_data.get("password")
        # print("password:",password)

        try:
            user = User.objects.create_user(username=username, password=password,)
            profile = Profile.objects.create(user=user, fullName=name)
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
            return Response(status=status.HTTP_201_CREATED)
        
        except Exception as e:
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR) 
        

# def signOut(request):
#     logout(request)

#     return Response(status=status.HTTP_200_OK)

# class SignInView(APIView):
#     serializer_class = SignInSerializer
#     def post(self, request):
#         serializer = self.serializer_class(data=request.data)
#         if serializer.is_valid():
#             username = serializer.validated_data['username']
#             password = serializer.validated_data['password']
#             user = authenticate(request, username=username, password=password)
#             if user is not None:
#                 login(request, user)
#                 return Response(status=status.HTTP_200_OK)
#             return Response({'detail': 'Неверные учетные данные'}, status=status.HTTP_401_UNAUTHORIZED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class SignUpView(APIView):
#     serializer_class = SignUpSerializer
#     def post(self, request):
#         print("request.data:", request.data)
#         print("request.query_params:", request.query_params)
#         serializer = self.serializer_class(data=request.data)
#         if serializer.is_valid():
#             name = serializer.validated_data['name']
#             username = serializer.validated_data['username']
#             password = serializer.validated_data['password']
#             if User.objects.filter(username=username).exists():
#                 return Response({'detail': 'Пользователь с таким username уже существует'}, status=status.HTTP_400_BAD_REQUEST)
#             user = User.objects.create_user(username=username, password=password)
#             Profile.objects.create(user=user, first_name=name)
#             user = authenticate(request, username=username, password=password)
#             if user is not None:
#                 login(request, user)
#             return Response(status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema_view(
    post=extend_schema(
        description="Выход пользователя из системы",
        responses={200: None}
    )
)
class SignOutView(APIView):
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_200_OK)
