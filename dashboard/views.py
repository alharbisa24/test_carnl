import json
import random
import re
from django.shortcuts import render,redirect
from django.http import HttpRequest
from . import forms,models
from home import models as HomeModels
from dotenv import load_dotenv
from datetime import timedelta
from django.utils.timezone import now
from .firebase_config import bucket
from django.utils import timezone
from django.utils.timezone import localtime
from urllib.parse import unquote, urlparse
from datetime import datetime
import google.generativeai as genai
import os
from django.core.paginator import Paginator
from django.db.models import Avg,Q,F
from django.contrib.auth import authenticate,login,logout
from django.db import IntegrityError
from django.contrib.auth.models import User

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=gemini_api_key)

model = genai.GenerativeModel('gemini-2.0-flash')


def dashboard_login_view(request:HttpRequest):

    if request.method == "POST":
        form = forms.LoginForm(request.POST)
        username = request.POST['username']
        password = request.POST['password']

        if form.is_valid():
            try:
                user = authenticate(request, username=username, password=password)
                if user and user.is_superuser:
                    login(request, user)
                    return redirect("dashboard:dashboard_home_view")
                
            except IntegrityError as e:
                    form.add_error('username', 'خطا في اسم السمتخدم او كلمة المرور')
                    print(e)

    else:
        form = forms.LoginForm()

    return render(request, 'dashboard/login.html', {
        "form": form,
    })


def dashboard_home_view(request:HttpRequest):
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('dashboard:dashboard_login_view')
    
    admin = request.user
    number_of_new_requests = HomeModels.Request.objects.filter(created_at__gte=now() - timedelta(days=2)).filter(status='waiting').count()
    total_events = models.Event.objects.count()
    total_active_events = models.Event.objects.filter(is_active=True).count()
    total_expired_events = models.Event.objects.filter(is_active=False).count()
    total_users= User.objects.filter(is_superuser=False).count()
    total_requests = HomeModels.Request.objects.count()
    total_admins= User.objects.filter(is_superuser=True).count()
    total_ratings= HomeModels.Rating.objects.count()    



    if request.POST:
        pass

    return render(request, 'dashboard/panel/home.html', {
        "admin": admin,
        "number_of_new_requests": number_of_new_requests,
        "total_events": total_events,
        "total_active_events" :total_active_events,
        "total_expired_events":total_expired_events,
        "total_users":total_users,
        "total_requests":total_requests,
        "total_admins":total_admins,
        "total_ratings":total_ratings
    })

def format_date(dt):
    local_dt = timezone.localtime(dt)

    months_ar = [
        "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
        "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"
    ]
    day = local_dt.day
    month = months_ar[local_dt.month - 1]
    year = local_dt.year

    hour = local_dt.hour
    minute = local_dt.minute
    period = "صباحاً" if hour < 12 else "مساءً"
    hour12 = hour if 1 <= hour <= 12 else abs(hour - 12) or 12

    time_str = f"{hour12}:{minute:02d} {period}"
    return f"{day} {month} {year} هـ - الساعة {time_str}"



def generateRandom(num: int):
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
    result = ''.join(random.choice(chars) for i in range(num))
    return result

def dashboard_events_view(request:HttpRequest):
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('dashboard:dashboard_login_view')
    
    success = False
    admin = request.user

    if request.method == "POST":
        form = forms.EventForm(request.POST, request.FILES)

        if form.is_valid():
            image = request.FILES['image']
            random_name = generateRandom(10)
            filename = f"uploads/{random_name}.jpg" 

            image_url = upload_image(image, filename)

                
            new_event = models.Event(
                    title=request.POST['title'],
                    description=request.POST['description'],
                    location = request.POST['location'],
                    available_seats= request.POST['available_seats'],
                    start_datetime = datetime.strptime(request.POST['start_datetime'], '%Y-%m-%dT%H:%M'),
                    end_datetime = datetime.strptime(request.POST['end_datetime'], '%Y-%m-%dT%H:%M'),
                    created_by = admin,
                    is_active = True if request.POST.get('is_active') == 'on' else False,
                    image_url = image_url,
                    created_at = now()
                    
                )
            new_event.save()
            success = True
            form = forms.EventForm() 

    else:
        form = forms.EventForm()

    if "search" in request.GET:
        events = models.Event.objects.filter(title__contains=request.GET["search"])
    else:
        events = models.Event.objects.all()

    for event in events:
        event.created_at_ar = format_date(event.created_at)
        event.startdate_ar = format_date(event.start_datetime)
        event.enddate_ar = format_date(event.end_datetime)
        event.available_seats_remaining = event.available_seats - event.event_requests.filter(status__in=["accepted", "attend", 'absent']).count()


    paginator = Paginator(events, 10) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    number_of_new_requests = HomeModels.Request.objects.filter(created_at__gte=now() - timedelta(days=2)).filter(status='waiting').count()
    return render(request, 'dashboard/panel/events.html',{
                "admin": admin,
                'events' : page_obj,
                'form': form,
                'success': success,
                "number_of_new_requests": number_of_new_requests

    })




def dashboard_requests_view(request:HttpRequest):
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('dashboard:dashboard_login_view')
    events =  models.Event.objects.all()
    requests = HomeModels.Request.objects.all()

    search = request.GET.get("search", "").strip()
    status = request.GET.get("status", "").strip()
    event = request.GET.get("event", "").strip()

    if search:
        requests = requests.filter(user__first_name__contains=search)

    if status:
        requests = requests.filter(status=status)

    if event:
        requests = requests.filter(event__id=event)
    
    deleted = request.GET.get('deleted', "false")
    accepted = request.GET.get('accepted', "False")
    all_requests = HomeModels.Request.objects.all()
    data_summary = { 
        "all": all_requests.count(),
        "new": all_requests.filter(created_at__gte=now() - timedelta(days=2)).filter(status='waiting').count(),
        "accepted": all_requests.filter(status='accepted').count(),
        "rejected": all_requests.filter(status='rejected').count(),

    }
    for req in requests:
            req.event.startdate_ar = format_date(req.event.start_datetime)
            req.event.enddate_ar = format_date(req.event.end_datetime)

    if request.POST:
        pass
    admin = request.user
    number_of_new_requests = HomeModels.Request.objects.filter(created_at__gte=now() - timedelta(days=2)).filter(status='waiting').count()
    return render(request, "dashboard/panel/requests.html",{
                "admin": admin,
                "events":events,
                "requests":requests,
                "deleted":deleted,
                "accepted":accepted,
                "data_summary":data_summary,
                "number_of_new_requests": number_of_new_requests


    })



def dashboard_request_delete_view(request:HttpRequest,id:int):
    req = HomeModels.Request.objects.get(pk=id)

    if req:
        req.delete()
        redirect_url = request.META.get("HTTP_REFERER")
        sep = '&' if '?' in redirect_url else '?'
        return redirect(f'{redirect_url}{sep}deleted=True')



def dashboard_request_accept_view(request:HttpRequest, id:int):
    req = HomeModels.Request.objects.get(pk=id)
    if req:
        req.status='accepted'
        req.save()
        redirect_url = request.META.get("HTTP_REFERER")
        sep = '&' if '?' in redirect_url else '?'
        return redirect(f'{redirect_url}{sep}accepted=True')



def dashboard_request_reject_view(request:HttpRequest, id:int):
    req = HomeModels.Request.objects.get(pk=id)
    if req:
        req.status='rejected'
        req.save()
        redirect_url = request.META.get("HTTP_REFERER")
        sep = '&' if '?' in redirect_url else '?'
        return redirect(f'{redirect_url}{sep}rejected=True')


def dashboard_ratings_view(request:HttpRequest):
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('dashboard:dashboard_login_view')
    


def dashboard_users_view(request:HttpRequest):
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('dashboard:dashboard_login_view')
    success = False
 
    if "search" in request.GET and len(request.GET["search"]) >= 3:
        users = User.objects.filter(Q(first_name__contains=request.GET["search"]) and Q(is_superuser=False))
    else:
        try:
            users = User.objects.filter(is_superuser=False)
        except Exception as e:
            print(e)
            return redirect("dashboard:home_view")

    admin = request.user
    number_of_new_requests = HomeModels.Request.objects.filter(created_at__gte=now() - timedelta(days=2)).filter(status='waiting').count()
    deleted = request.GET.get('deleted', "false")
    return render(request, "dashboard/panel/users.html",{
        "users": users,
        "admin": admin,
        "deleted":deleted,
        "number_of_new_requests": number_of_new_requests
    })

def dashboard_users_delete_view(request:HttpRequest,id:int):
    user = User.objects.get(pk=id)

    if user:
        user.delete()
        return redirect('/dashboard/users/?deleted=True')


def dashboard_admins_view(request: HttpRequest):
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('dashboard:dashboard_login_view')
    success = False
 
    if request.method == "POST":
        form = forms.AdminForm(request.POST)

        if form.is_valid():
            if request.POST['password'] != request.POST['confirm_password']:
                form.add_error('password', 'كلمات المرور غير متطابقة')
                form.add_error('confirm_password', 'كلمات المرور غير متطابقة')
                
            elif len(User.objects.filter(email=request.POST['email'])) > 0:
                form.add_error('email', 'البريد الالكتروني موجود مسبقا')

            elif len(User.objects.filter(username=request.POST['username'])) > 0:
                form.add_error('email', 'اسم المستخدم موجود مسبقا')

                
            else:
                new_admin = User.objects.create_superuser(
                    first_name=request.POST['first_name'],
                    last_name=request.POST['last_name'],
                    username=request.POST['username'],
                    email=request.POST['email'],
                    password=request.POST['password']
                )
                
                new_admin.save()
                success = True
                form = forms.AdminForm() 

    else:
        form = forms.AdminForm()

    if "search" in request.GET and len(request.GET["search"]) >= 3:
        admins = User.objects.filter(Q(first_name__contains=request.GET["search"]) and Q(is_superuser=True))
    else:
        try:
            admins = User.objects.filter(is_superuser=True)
        except User.DoesNotExist:
            print("error")

    admin = request.user
    number_of_new_requests = HomeModels.Request.objects.filter(created_at__gte=now() - timedelta(days=2)).filter(status='waiting').count()
    return render(request, "dashboard/panel/admins.html", {
        'admins' : admins,
        'form': form,
        'success': success,
        "admin": admin,
        "number_of_new_requests": number_of_new_requests

    })




def dashboard_event_delete_view(request:HttpRequest,id:int):
    event = models.Event.objects.get(pk=id)
    delete_image_from_firebase(event.image_url)

    if event:
        event.delete()
        return redirect('dashboard:dashboard_events_view')


def dashboard_event_edit_view(request:HttpRequest, id:int):
    try:
        event = models.Event.objects.get(pk=id)

        form = forms.EventForm()
        if event:
            admin = request.user
            number_of_new_requests = HomeModels.Request.objects.filter(created_at__gte=now() - timedelta(days=2)).filter(status='waiting').count()
            if request.method == "POST":
                    form = forms.EventForm(request.POST, request.FILES)
                    

                    if form.is_valid():
                        event.title = request.POST['title']
                        event.description = request.POST['description']
                        event.location = request.POST['location']
                        event.available_seats = request.POST['available_seats']
                        event.start_datetime = datetime.strptime(request.POST['start_datetime'], '%Y-%m-%dT%H:%M')
                        event.end_datetime = datetime.strptime(request.POST['end_datetime'], '%Y-%m-%dT%H:%M')
                        if request.FILES and event.image_url:
                            delete_image_from_firebase(event.image_url)

                            image = request.FILES['image']
                            random_name = generateRandom(10)
                            filename = f"uploads/{random_name}.jpg" 

                            image_url = upload_image(image, filename)

                            event.image_url = image_url
                        event.save()
                        return redirect('dashboard:dashboard_events_view')
     
            data = {
        "id" : id,
        'title': event.title,
        'description': event.description,
        'image_url': event.image_url,
        'location': event.location,
        'available_seats': event.available_seats,
        'start_datetime': localtime(event.start_datetime).strftime('%Y-%m-%dT%H:%M'),
        'end_datetime': localtime(event.end_datetime).strftime('%Y-%m-%dT%H:%M'),
        'is_active': event.is_active,
        'event_requests':event.event_requests.filter(status__in=['accepted','attend'])
            }
            return render(request, "dashboard/panel/edit_event.html", {
            'admin' : admin,
            "number_of_new_requests": number_of_new_requests,
            "data": data,
            "form": form,


                
            })
    except models.Event.DoesNotExist:
        return redirect('dashboard:dashboard_events_view')

def dashboard_event_requests_view(request:HttpRequest, id:int):
    try:
        event = models.Event.objects.get(pk=id)
        admin = request.user
        number_of_new_requests = HomeModels.Request.objects.filter(created_at__gte=now() - timedelta(days=2)).filter(status='waiting').count()
        event.startdate_ar = format_date(event.start_datetime)
        event.enddate_ar = format_date(event.end_datetime)
        
        data_summary = { 
        "all": event.event_requests.count(),
        "new": event.event_requests.filter(created_at__gte=now() - timedelta(days=2)).filter(status='waiting').count(),
        "accepted": event.event_requests.filter(status='accepted').count(),
        "rejected": event.event_requests.filter(status='rejected').count(),

        
        }
        event_requests = event.event_requests.filter(status__in=["accepted", "attend", 'absent'])
        search = request.GET.get("search", "").strip()
        if search:
                event_requests = event_requests.filter(user__first_name__contains=search)

        return render(request, "dashboard/panel/event_requests.html", {
            'admin' : admin,
            "number_of_new_requests": number_of_new_requests,
            "event":event,
            "data_summary":data_summary,
            "event_requests":event_requests


                
            })

    except models.Event.DoesNotExist:
        return redirect('dashboard:dashboard_events_view')


def dashboard_user_requests_view(request:HttpRequest, id:int):
    try:
        user = User.objects.get(pk=id)
        admin = request.user
        number_of_new_requests = HomeModels.Request.objects.filter(created_at__gte=now() - timedelta(days=2)).filter(status='waiting').count()
        
        user_requests = user.user_requests.all()

        search = request.GET.get("search", "").strip()
        if search:
            user_requests = user_requests.filter(event__title__contains=search)

        data_summary = { 
        "all": user.user_requests.count(),
        "new": user.user_requests.filter(created_at__gte=now() - timedelta(days=2)).filter(status='waiting').count(),
        "accepted": user.user_requests.filter(status='accepted').count(),
        "rejected": user.user_requests.filter(status='rejected').count(),
        }
        
        for req in user_requests: 
            req.event.startdate_ar = format_date(req.event.start_datetime)
            req.event.enddate_ar = format_date(req.event.end_datetime)
            

        return render(request, "dashboard/panel/user_requests.html", {
            'admin' : admin,
            "number_of_new_requests": number_of_new_requests,
            "user_requests":user_requests,
            "data_summary":data_summary


                
            })

    except User.DoesNotExist:
        return redirect('dashboard:dashboard_users_view')



def upload_image(uploadedFile, filename):

    blob = bucket.blob(filename) 

    blob.upload_from_string(uploadedFile.read(), content_type=uploadedFile.content_type)

    blob.make_public()

    return blob.public_url

def delete_image_from_firebase(image_url):
    try:
        path = urlparse(image_url).path
        encoded_path = path.split("/o/")[1].split("?")[0]
        file_path = unquote(encoded_path)  

        blob = bucket.blob(file_path)
        blob.delete()

    except Exception as e:
        print(" فشل حذف الصورة:", e)

def dashboard_admin_delete_view(request:HttpRequest,id:int):
    admin = User.objects.get(pk=id)
    if admin:
        admin.delete()
        return redirect('dashboard:dashboard_admins_view')





def dashboard_logout_view(request:HttpRequest):
    logout(request)
    return redirect("home:login_view")



def dashboard_event_request_status_view(request:HttpRequest, id:int):
    event = models.Event.objects.get(pk=id)
    if event:
        event.is_active = not event.is_active
        event.save()
        redirect_url = request.META.get("HTTP_REFERER", "/").split("?")[0]
        sep = '&' if '?' in redirect_url else '?'
        return redirect(f"{redirect_url}{sep}success=True")



def dashboard_attend_request_view(request: HttpRequest):
    if request.method == 'POST':
        for key, value in request.POST.items():
            if key.startswith('attendence_'):
                try:
                    request_id = int(key.replace('attendence_', ''))
                    event_request = HomeModels.Request.objects.get(id=request_id)
                    event = event_request.event
                    event.is_active = False
                    event.save()
                    
                    
                    if value == 'present':
                        event_request.status = 'attend'
                    else:
                        event_request.status = 'absent'

                    event_request.save()

                except HomeModels.Request.DoesNotExist as e:
                    print(e)

        redirect_url = request.META.get("HTTP_REFERER", "/").split("?")[0]
        return redirect(f"{redirect_url}?success=True")

    redirect_url = request.META.get("HTTP_REFERER", "/").split("?")[0]
    return redirect(redirect_url)

def dashboard_ratings_view(request:HttpRequest):
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('dashboard:dashboard_login_view')
    
 
 
    if "search" in request.GET and len(request.GET["search"]) >= 3:
        ratings = HomeModels.Rating.objects.filter(request__user__first_name__contains=request.GET["search"])
    else:
        try:
            ratings = HomeModels.Rating.objects.all()

        except HomeModels.Rating.DoesNotExist:
            print("error")
            
    for rating in ratings:
        rating.event.startdate_ar = format_date(rating.event.start_datetime)
        rating.event.enddate_ar = format_date(rating.event.end_datetime)


    admin = request.user
    number_of_new_requests = HomeModels.Request.objects.filter(created_at__gte=now() - timedelta(days=2)).filter(status='waiting').count()
    return render(request, "dashboard/panel/ratings.html", {
        'ratings' : ratings,
        "admin": admin,
        "number_of_new_requests": number_of_new_requests

    })


def dashboard_ratings_delete_view(request:HttpRequest, id:int):
    rating = HomeModels.Rating.objects.get(pk=id)

    if rating:
        rating.delete()
        redirect_url = request.META.get("HTTP_REFERER")
        return redirect(f'{redirect_url}?deleted=True')




def dashboard_ratings_update_status_view(request:HttpRequest,id:int):
    rating = HomeModels.Rating.objects.get(pk=id)
    if rating:
        rating.status = not rating.status
        rating.save()
        redirect_url = request.META.get("HTTP_REFERER", "/").split("?")[0]
        return redirect(f"{redirect_url}?success=True")
    


def ai_recommendations_view(request:HttpRequest):
    admin = request.user
    number_of_new_requests = HomeModels.Request.objects.filter(created_at__gte=now() - timedelta(days=2)).filter(status='waiting').count()
    total_events = HomeModels.Event.objects.count()
    total_requests = HomeModels.Request.objects.count()
    avg_rating = HomeModels.Rating.objects.aggregate(avg=Avg('stars'))['avg'] or 0
    avg_rating = round(avg_rating, 1)

    attended = HomeModels.Request.objects.filter(status='attend').count()
    attendance_rate = round((attended / total_requests) * 100) if total_requests > 0 else 0

    event_titles = list(HomeModels.Event.objects.values_list('title', flat=True))

    recommendations = []
    ai_summary = ""
    user_data = {}
    content_ideas = []
    
    try:
        titles_text = "\n".join(event_titles)
        prompt = f"""
            You are an AI advisor for an Arabic event management platform. our platform has:
            - {total_events} total events
            - {total_requests} registration requests
            - {attendance_rate}% attendance rate
            - {avg_rating}/5 average rating
            
            events titles: {titles_text}
            
            Generate the following in arabic language:
            1. analyze events titles and generate best 4-6 categories based on events titles

            1. A summary paragraph analyzing overall platform performance (3-4 sentences)
            
            2. three detailed recommendations with these fields:
               - title: A short title
               - description: A detailed explanation (2-3 sentences)
               - importance: "high" or "medium"
            
            3. user behavior analysis with:
               - active_percentage: Percentage of active users (between 40-80)
               - engagement_analysis: A sentence explaining user engagement
               - popular_times: Array of 3 objects with day_name (like "الاحد") and time (like "5:30 مساءً")
               - time_analysis: A sentence about optimal scheduling
            
            4. two content ideas with:
               - title: Content title
               - category: Content type (like "ورشة عمل" or "محاضرة")
               - description: Brief description
            
            Format your response as valid JSON with these 5 keys:
            - categories : array contains categories title and each title contain (category,count)
            - ai_summary
            - recommendations (array)
            - user_data (object)
            - content_ideas (array)
            
            Only respond with valid JSON, no other text.
            """
            
        response = model.generate_content(prompt)
        text = response.candidates[0].content.parts[0].text

        clean_text = re.sub(r"^```json\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)

        data = json.loads(clean_text)
        categories = data.get('categories', [])
        ai_summary = data.get('ai_summary', '')
        recommendations = data.get('recommendations', [])
        user_data = data.get('user_data', {})
        content_ideas = data.get('content_ideas', [])
    except Exception as e:
        print(e)
        return redirect('/dashboard')
  
            


    return render(request, "dashboard/panel/ai_recommendations.html",{
        'total_events': total_events,
        'ai_summary': ai_summary,
        'total_requests': total_requests,
        "attendance_rate":attendance_rate,
        'categories': categories,
        'avg_rating': round(avg_rating, 1),
        'recommendations': recommendations,
        'user_data': user_data,
        'content_ideas': content_ideas,
        "admin": admin,
        "number_of_new_requests": number_of_new_requests
    })

