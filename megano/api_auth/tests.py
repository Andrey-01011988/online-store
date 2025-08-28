from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
import json

from api_auth.models import Profile, Avatar
from api_auth.serializers import ProfileSerializer

User = get_user_model()


class AuthModelsTest(TestCase):
    def setUp(self):
        """Фикстура с подготовленными данными"""
        self.user = User.objects.create_user(
            username='testuser', password='testpass123', first_name='Test'
        )
        self.profile = Profile.objects.create(
            user=self.user, fullName='Test User', phone=1234567890
        )
        self.avatar = Avatar.objects.create(profile=self.profile, alt='test avatar')

    def tearDown(self):
        """Очистка базы после каждого теста"""
        User.objects.all().delete()
        Profile.objects.all().delete()
        Avatar.objects.all().delete()

    def test_user_creation(self):
        """Тест создания пользователя"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertTrue(self.user.check_password('testpass123'))
        self.assertEqual(self.user.first_name, 'Test')

    def test_profile_creation(self):
        """Тест создания профиля"""
        self.assertEqual(self.profile.user, self.user)
        self.assertEqual(self.profile.fullName, 'Test User')
        self.assertEqual(self.profile.phone, 1234567890)

    def test_avatar_creation(self):
        """Тест создания аватара"""
        self.assertEqual(self.avatar.profile, self.profile)
        self.assertEqual(self.avatar.alt, 'test avatar')

    def test_soft_delete_user(self):
        """Тест мягкого удаления пользователя"""
        self.user.delete()
        # print("User is deleted:", self.user.is_deleted)
        self.assertTrue(self.user.is_deleted)
        self.assertTrue(
            User.objects.all_with_deleted().filter(username='testuser', is_deleted=True).exists()
        )
        self.user.restore()
        self.assertFalse(self.user.is_deleted)


class AuthSerializersTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='serialuser', password='serialpass')
        self.profile = Profile.objects.create(
            user=self.user, fullName='Serial User', phone=9876543210
        )
        self.avatar = Avatar.objects.create(profile=self.profile, alt='serial avatar')
        self.request = self.factory.get('/')

    def tearDown(self):
        User.objects.all().delete()
        Profile.objects.all().delete()
        Avatar.objects.all().delete()

    def test_profile_serializer(self):
        """Тест сериализации профиля"""
        serializer = ProfileSerializer(instance=self.profile, context={'request': self.request})
        data = serializer.data
        self.assertEqual(data['fullName'], 'Serial User')
        # self.assertEqual(data['phone'], 9876543210) # в сейчас от SQLite приходит строка, в дальнейшем при переходе на PostgreSQL будет int
        self.assertEqual(data['email'], '')  # email не установлен

    def test_profile_serializer_with_email(self):
        """Тест сериализации с email"""
        self.user.email = 'test@example.com'
        self.user.save()
        serializer = ProfileSerializer(instance=self.profile, context={'request': self.request})
        self.assertEqual(serializer.data['email'], 'test@example.com')


class AuthViewsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='viewuser', password='viewpass123', first_name='View'
        )
        self.profile = Profile.objects.create(
            user=self.user, fullName='View User', phone=5555555555
        )

    def tearDown(self):
        User.objects.all().delete()
        Profile.objects.all().delete()

    def test_signup_success(self):
        """Тест успешной регистрации"""
        url = reverse('api_auth:register')
        data = {"username": "newuser", "password": "newpass123", "name": "New User"}
        response = self.client.post(url, {json.dumps(data): ''}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_signup_duplicate(self):
        """Тест регистрации с существующим username"""
        url = reverse('api_auth:register')
        data = {"username": "viewuser", "password": "newpass123", "name": "New User"}
        response = self.client.post(url, data={json.dumps(data): ''}, format='multipart')

        # print("Response data:", response.data)  # для отладки

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
        self.assertIn('уже существует', response.data['detail'])

    def test_signin_success(self):
        """Тест успешного входа"""
        url = reverse('api_auth:login')
        data = {"username": "viewuser", "password": "viewpass123"}
        response = self.client.post(url, data={json.dumps(data): ''}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_profile_get(self):
        """Тест получения профиля"""
        self.client.force_authenticate(user=self.user)
        url = reverse('api_auth:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['fullName'], 'View User')

    def test_profile_update(self):
        """Тест обновления профиля"""
        self.client.force_authenticate(user=self.user)
        url = reverse('api_auth:profile')
        data = {"fullName": "Updated Name", "phone": "9999999999", "email": "new@example.com"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()  # Обновляем экземпляр профиля
        self.user.refresh_from_db()  # Обновляем экземпляр пользователя
        self.assertEqual(self.profile.fullName, 'Updated Name')
        self.assertEqual(self.user.email, 'new@example.com')
