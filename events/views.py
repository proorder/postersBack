from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import user_passes_test
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser
from rest_framework.status import (
        HTTP_200_OK,
        HTTP_201_CREATED,
        HTTP_400_BAD_REQUEST,
        HTTP_401_UNAUTHORIZED,
        )
from .models import (
        Event,
        EventSerializer,
        UploadImagesForm,
        Infrastructure,
        InfrastructureSerializer,
        User,
        UserSerializer,
        )
import time, re, os


@csrf_exempt
@parser_classes((JSONParser,))
@api_view(["POST"])
def registration(request):
    data = request.data
    serializer = UserSerializer(data=data)
    if serializer.is_valid():
        user = User.objects.create_user(**data)
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'id': user.pk,
            'full_name': user.full_name,
            'is_superuser': 'admin' if user.is_superuser else 'manager' if user.is_staff else 'user'
        }, status=HTTP_201_CREATED)
    else:
        return Response({}, status=HTTP_400_BAD_REQUEST)


@csrf_exempt
@parser_classes((JSONParser,))
@api_view(["POST"])
def make_manager(request):
    data = request.data
    u = User.objects.get(id=data['id'])
    u.is_staff = True
    u.save()
    return Response({}, status=HTTP_200_OK)


@csrf_exempt
@parser_classes((JSONParser,))
@api_view(["POST"])
def change_name(request):
    data = request.data
    user = request.user
    user.full_name = data['name']
    user.save()
    return Response({}, status=HTTP_200_OK)


@csrf_exempt
@parser_classes((JSONParser,))
@api_view(["POST", "GET"])
@user_passes_test(lambda u: u.is_superuser, login_url='/permission-denied')
def users(request):
    if request.method == 'GET':
        return Response(UserSerializer(User.objects.all(), many=True).data, status=200)
    elif request.method == 'POST':
        return Response({}, status=200)


@csrf_exempt
@parser_classes((JSONParser,))
@api_view(["GET"])
def my_events(request):
    if request.method == 'GET':
        response = EventSerializer(Event.objects.filter(owner=request.user)
                .order_by('date'), many=True).data
        return Response(response, status=200)


@csrf_exempt
@parser_classes((JSONParser,))
@api_view(["POST", "GET", "DELETE", "PUT"])
def events(request):
    if request.method == 'GET':
        if not request.user.is_staff:
            response = ''
            if request.GET['search'] == '':
                response = EventSerializer(
                        Event.objects.order_by('date'), many=True
                        ).data
            else:
                response = EventSerializer(
                        Event.objects.filter(title__contains=request.GET['search'])
                        .order_by('date'), many=True).data
            return Response(response, status=200)
        else:
            response = EventSerializer(Event.objects.all(), many=True).data
            return Response(response, status=200)
    elif request.method == 'POST':
        data = request.POST
        serializer = EventSerializer(data=data)
        if serializer.is_valid():
            data = serializer.data.copy()
            del data['images']
            response = request.user.events.create(**data)
            if 'image' in request.FILES:
                f = UploadImagesForm(request.POST or None, request.FILES or None)
                if f.is_valid():
                    p = Event.objects.get(id=response.id)
                    p.images.create(image=f.cleaned_data['image'])
            return Response(EventSerializer(response).data, status=HTTP_201_CREATED)
        else:
            print(serializer.errors)
            return Response({}, status=HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        if request.user.is_staff:
            event = Event.objects.get(id=request.data['id'])
            if event:
                event.delete()
            return Response({}, status=HTTP_200_OK)
        else:
            event = Event.objects.get(id=request.data['id'])
            if event.owner == request.user:
                event.delete()
                return Response({}, status=HTTP_200_OK)
            return Response({}, status=HTTP_401_UNAUTHORIZED)
    elif request.method == 'PUT':
        data = request.data
        required_event = Event.objects.get(id=data['id'])
        if request.user.is_staff or required_event.owner == request.user:
            serializer = EventSerializer(data=data)
            if serializer.is_valid():
                for key in data:
                    if key != 'images' and key != 'id':
                        required_event.__setattr__(key, data[key])
                required_event.save()
                if 'image' in request.FILES:
                    f = UploadImagesForm(request.POST or None, request.FILES or None)
                    if f.is_valid():
                        try:
                            old_img = required_event.images.all()[0]
                            os.remove('media/' + str(old_img.image))
                            old_img.delete()
                        except IndexError:
                            pass
                        required_event.images.create(image=f.cleaned_data['image'])
                    else:
                        return Response({}, status=HTTP_400_BAD_REQUEST)
                return Response(EventSerializer(required_event).data, status=HTTP_200_OK)
        return Response({}, status=HTTP_400_BAD_REQUEST)


@csrf_exempt
@parser_classes((JSONParser,))
@api_view(["GET"])
def user_events(request):
    if request.method == 'GET':
        response = EventSerializer(Event.objects.filter(owner=request.user), many=True).data
        return Response(response, status=200)


@csrf_exempt
@parser_classes((JSONParser,))
@api_view(["POST", "GET", "DELETE", "PUT"])
def infrastructures(request):
    if request.method == 'GET':
        response = InfrastructureSerializer(
                Infrastructure.objects.filter(title__contains=request.GET['search']), many=True).data
        return Response(response, status=200)
    elif request.method == 'POST':
        if request.user.is_superuser:
            data = request.POST
            print(data)
            serializer = InfrastructureSerializer(data=data)
            if serializer.is_valid():
                data = serializer.data.copy()
                del data['images']
                response = request.user.infrastructures.create(**data)
                if 'image' in request.FILES:
                    f = UploadImagesForm(request.POST or None, request.FILES or None)
                    if f.is_valid():
                        p = Infrastructure.objects.get(id=response.id)
                        p.images.create(image=f.cleaned_data['image'])
                return Response(InfrastructureSerializer(response).data, status=HTTP_201_CREATED)
            else:
                return Response({}, status=HTTP_400_BAD_REQUEST)
        else:
            return Response({}, status=HTTP_401_UNAUTHORIZED)
    elif request.method == 'DELETE':
        if request.user.is_superuser:
            event = Infrastructure.objects.get(id=request.data['id'])
            if event:
                event.delete()
            return Response({}, status=HTTP_200_OK)
        else:
            return Response({}, status=HTTP_401_UNAUTHORIZED)
    elif request.method == 'PUT':
        data = request.data
        required = Infrastructure.objects.get(id=data['id'])
        if request.user.is_staff or required.owner == request.user:
            serializer = InfrastructureSerializer(data=data)
            if serializer.is_valid():
                for key in data:
                    if key != 'images' and key != 'id':
                        required.__setattr__(key, data[key])
                required.save()
                if 'image' in request.FILES:
                    f = UploadImagesForm(request.POST or None, request.FILES or None)
                    if f.is_valid():
                        try:
                            old_img = required.images.all()[0]
                            os.remove('media/' + str(old_img.image))
                            old_img.delete()
                        except IndexError:
                            pass
                        required.images.create(image=f.cleaned_data['image'])
                    else:
                        return Response({}, status=HTTP_400_BAD_REQUEST)
                return Response(InfrastructureSerializer(required).data, status=HTTP_200_OK)
        return Response({}, status=HTTP_400_BAD_REQUEST)

