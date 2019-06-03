from django.contrib import admin
from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from events.views import (
        events,
        infrastructures,
        registration,
        user_events,
        change_name,
        users,
        make_manager,
        my_events,
        )


class AuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'id': user.pk,
            'full_name': user.full_name,
            'is_superuser': 'admin' if user.is_superuser else 'manager' if user.is_staff else 'user'
        })


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth', AuthToken.as_view()),
    path('api/v1/registration', registration),
    path('api/v1/events', events),
    path('api/v1/my_events', my_events),
    path('api/v1/users', users),
    path('api/v1/user_events', user_events),
    path('api/v1/infrastructures', infrastructures),
    path('api/v1/profile/name', change_name),
    path('api/v1/make_manager', make_manager),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
