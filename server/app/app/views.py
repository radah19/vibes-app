import json
from django.http import JsonResponse
from django.http import HttpResponse
from app.models import *
from django.db import connection
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token
from django.shortcuts import redirect

def dictfetchall(cursor):
    """
    Return all rows from a cursor as a dict.
    Assume the column names are unique.
    """
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def vibe_rooms(request):

    if request.method == "POST":
        data = json.loads(request.body)
        username = data['username']
        title = data['title']
        font = data['font']
        color_gradient = data['color_gradient']

        print(username, title, font)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO vibe_rooms (created_by, title, color_gradient, font)
                VALUES (%s, %s, %s, %s)
            """, [username, title, color_gradient, font])

        return HttpResponse("Room created", status=201)

    else:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    user,
                    title,
                    color_gradient,
                    font
                FROM vibe_rooms
            """, [])

            response_data = {}
            response_data['result'] = dictfetchall(cursor)

        return HttpResponse(json.dumps(response_data), content_type='application/json')

def vibe_room_user_id(request, username):
    print('\nREQUEST: ', request, '\n')
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                id,
                created_by as user,
                title,
                color_gradient,
                font
            FROM vibe_rooms
            WHERE created_by = %s
        """, [username])
    
        response_data = {}
        response_data['result'] = dictfetchall(cursor)

    return HttpResponse(json.dumps(response_data), content_type='application/json')

def vibe_room_room_id(request, room_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                id,
                created_by as user,
                title,
                color_gradient,
                font
            FROM vibe_rooms
            WHERE id = %s
        """, [room_id])

        response_data = {}
        response_data['result'] = dictfetchall(cursor)

    return HttpResponse(json.dumps(response_data), content_type='application/json')

def vibe_room_update_room_id(request, room_id):
    data = json.loads(request.body)
    title = data['title']
    font = data['font']
    color_gradient = data['color_gradient']

    print(data, title, font, color_gradient, room_id)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE vibe_rooms
            SET title = %s, color_gradient = %s, font = %s
            WHERE id = %s
        """, [title, color_gradient, font, room_id])
    
    return HttpResponse("Room updated", status=201)

def song(request, room_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT *
            FROM song_links
            WHERE vibe_room_id = %s
        """, [room_id])

        response_data = {}
        response_data['result'] = dictfetchall(cursor)

    return HttpResponse(json.dumps(response_data), content_type='application/json')

def media(request, room_id):
    if request.method == "POST":
        data = json.loads(request.body)
        img_link = data['img_link']
        txt = data['txt']
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO media (vibe_room_id, img_link, txt)
                VALUES (%s, %s, %s)
                returning id
            """, [room_id, img_link, txt])

            response_data = {}
            response_data['result'] = dictfetchall(cursor)
        
        return HttpResponse(json.dumps(response_data), content_type='application/json', status=201)
    
    if request.method == "DELETE":
        print(room_id)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM media
                WHERE id = %s
                returning id
            """, [room_id]) # media_id is passed in to room_id

            response_data = {}
            response_data['result'] = dictfetchall(cursor)

        return HttpResponse(json.dumps(response_data), content_type='application/json', status=200)
    
    else:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM media 
                WHERE vibe_room_id = %s
            """, [room_id])

            response_data = {}
            response_data['result'] = dictfetchall(cursor)

        return HttpResponse(json.dumps(response_data), content_type='application/json')
    
def edit_media(request, media_id):
    data = json.loads(request.body)
    img_link = data['img_link']
    txt = data['txt']
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE media
            SET img_link = %s, txt = %s
            WHERE id = %s
            returning id
        """, [img_link, txt, media_id])

        response_data = {}
        response_data['result'] = dictfetchall(cursor)
    
    return HttpResponse(json.dumps(response_data), content_type='application/json', status=201)

@csrf_exempt 
def auth(request):
    request_data = json.loads(request.body)
    user = authenticate(username=request_data.get('username', ''), password=request_data.get('password', ''))
    if user is not None:
        csrf_token = get_token(request)

        # Sign in User! Celebrations!
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM users 
                WHERE username = %s
            """, [user.username])

            user_info = dictfetchall(cursor)

        return HttpResponse(json.dumps({
            'username': user.username,
            'email': user.email,
            'f_name': user_info[0]['f_name'],
            'l_name': user_info[0]['l_name'],
            'csrftoken': csrf_token
        }), content_type='application/json')
    else:
        # Oopsy!
        return HttpResponse(json.dumps('Oopsy!'), content_type='application/json')
    
    
    