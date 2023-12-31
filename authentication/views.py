from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenViewBase
from .serializers import CustomTokenCreateSerializer,AdminTokenCreateSerializer
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView
from djoser.views import TokenCreateView
from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import AllowAny
from djoser import views as djoser_views
from djoser.conf import settings
from django.contrib.auth import authenticate, login
from rest_framework.views import APIView
from django.contrib.auth.decorators import login_required

# Create your views here.


class CustomTokenObtainPairView(TokenViewBase):
    """
    Takes a set of user credentials and returns an access and refresh JSON web
    token pair to prove the authentication of those credentials.
    """
    serializer_class = CustomTokenCreateSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        return Response(serializer.validated_data, status=status.HTTP_200_OK)
    

class FacebookLogin(SocialLoginView):
    adapter_class = FacebookOAuth2Adapter


class GoogleLogin(SocialLoginView):
    authentication_classes = []
    adapter_class = GoogleOAuth2Adapter
    callback_url = "http://localhost:3000/login"  # <--- make sure this line is correct!
    client_class = OAuth2Client


class AdminTokenCreateView(TokenCreateView):
    def create(self,request,*args,**kwargs):
        serializer=self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user=serializer.user
        print("before checking superuser")
        # Check if the user is a superuser
        if user.is_superuser:
            print("superuser is true")
            # Generate the token
            token, created = self.token_model.objects.get_or_create(user=user)
            if not created:
                # Update the created time of the token to keep it valid
                self.token_model.objects.filter(user=user).update(created=self.token_model.current_time)
            
            # Return the token
            return Response({'token': token.key})

        # If the user is not a superuser, return an error response
        return Response({"detail": "Superuser login required."}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['POST'])
@permission_classes([AllowAny])
def admin_login(request):
    # Get email and password from the request data
    email = request.data.get('email')
    password = request.data.get('password')

    # Check if a user with the given email and password exists and is a superuser
    user = authenticate(request=request, username=email, password=password)
    
    if user is not None and user.is_active and user.is_superuser:
        # User is a superuser, generate a token or perform any other desired action
        return Response({'auth_token': 'your_token_here', 'userRole': 'superuser'})

    # If authentication fails, return an error response
    return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class AdminLogin(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        # Authenticate the user
        user = authenticate(request, email=email, password=password)

        if user is not None and user.is_active and user.is_staff:
            # Log the user in
            login(request, user)
            return Response({'message': 'Admin logged in successfully', 'userRole': 'superuser'})

        return Response({'message': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    
@api_view(['GET'])
@login_required
def get_user_profile(request):
    user=request.user
    full_name=f"{user.first_name} {user.last_name}"
    user_data={
        'name':full_name
    }
    return Response(user_data)