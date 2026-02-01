from django.shortcuts import render,redirect
from django.http import HttpRequest
from dashboard.models import *
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import *
from django.utils import timezone
from . import forms
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from django.core.paginator import Paginator
from django.contrib import messages


def format_date(dt):
    local_dt = timezone.localtime(dt)
    months_ar = [
        "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
        "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"
    ]
    day = local_dt.day
    month = months_ar[local_dt.month - 1]
    year = local_dt.year

    return f"{day} {month} {year}"

def home_view(request:HttpRequest):
  

    events = Event.objects.all().order_by('-created_at')[:3]
    
    for event in events:
        event.startdate_ar = format_date(event.start_datetime)
        event.enddate_ar = format_date(event.end_datetime)
        event.dateperiod = f"{event.startdate_ar} - {event.enddate_ar}"
        event.timeperiod = f"{event.start_datetime.strftime('%I:%M %p').replace('AM', 'صباحا').replace('PM', 'مساء')} - {event.end_datetime.strftime('%I:%M %p').replace('AM', 'صباحا').replace('PM', 'مساء')}"


    return render(request,"home/home.html", {
        "events": events,
    })


def events_view(request:HttpRequest):
 
    events = Event.objects.all().order_by('-created_at')
    
    for event in events:
        event.startdate_ar = format_date(event.start_datetime)
        event.enddate_ar = format_date(event.end_datetime)
        event.dateperiod = f"{event.startdate_ar} - {event.enddate_ar}"
        event.timeperiod = f"{event.start_datetime.strftime('%I:%M %p').replace('AM', 'صباحا').replace('PM', 'مساء')} - {event.end_datetime.strftime('%I:%M %p').replace('AM', 'صباحا').replace('PM', 'مساء')}"

    paginator = Paginator(events, 5) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)


    return render(request,"home/allevents.html", {
             "events": events,
        "page_obj":page_obj
    })

def event_details_view(request:HttpRequest, id:int):
  
    try: 
        event = Event.objects.get(pk=id)
        event_ratings = event.event_ratings.filter(status=True)
        event.startdate_ar = format_date(event.start_datetime)
        event.enddate_ar = format_date(event.end_datetime)
        event.dateperiod = f"{event.startdate_ar} - {event.enddate_ar}"
        event.timeperiod = f"{event.start_datetime.strftime('%I:%M %p').replace('AM', 'صباحا').replace('PM', 'مساء')} - {event.end_datetime.strftime('%I:%M %p').replace('AM', 'صباحا').replace('PM', 'مساء')}"
        event.available_seats_remaining = event.available_seats - event.event_requests.filter(status__in=["accepted", "attend", 'absent']).count()
   
   
    except Event.DoesNotExist:
         return redirect('home:home_view')
    paginator = Paginator(event_ratings, 3) 
    success = request.GET.get('success', "false")
    error = request.GET.get('error', "error")
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.user.is_authenticated:
        user_has_request = Request.objects.filter(event=event, user=request.user).exists()
    else:
        user_has_request= False

    return render(request,"home/event_details.html",{
        "event":event,
        "event_ratings":event_ratings,
        "success": success,
        "error":error,
        'page_obj': page_obj,
        "user_has_request": user_has_request


    })


def login_view(request:HttpRequest):
    if request.method == "POST":
            form = forms.LoginForm(request.POST)
            username = request.POST['username']
            password = request.POST['password']

            if form.is_valid():
                try:
                    user = authenticate(request, username=username, password=password)

                    if user:
                        login(request, user)
                        return redirect("home:home_view")


                    else:
                        form.add_error('password', 'كلمة المرور غير صحيحة ')
                except User.DoesNotExist:
                        form.add_error('email', 'البريد الالكتروني غير موجود ')
 


    else:
        form = forms.LoginForm()
            
    return render(request,"home/login.html", {
         "form":form
    })

def register_view(request:HttpRequest):
    if request.method == "POST":
        form = forms.RegisterForm(request.POST)

        if form.is_valid():
            if request.POST['password'] != request.POST['confirm_password']:
                form.add_error('password', 'كلمات المرور غير متطابقة')
                form.add_error('confirm_password', 'كلمات المرور غير متطابقة')
                
            elif len(User.objects.filter(email=request.POST['email'])) > 0:
                form.add_error('email', 'البريد الالكتروني موجود مسبقا')


            elif len(User.objects.filter(username=request.POST['username'])) > 0:
                form.add_error('username', 'اسم المستخدم موجود مسبقا')

                
            else:
                new_user = User.objects.create_user(
                    first_name=request.POST['first_name'],
                    last_name=request.POST['last_name'],
                    username=request.POST['username'],
                    email=request.POST['email'],
                    password=request.POST['password']
                )
                new_user.save()
                form = forms.RegisterForm() 
                return redirect('/login?registered=True')

    else:
        form = forms.RegisterForm()

    return render(request,"home/register.html",{
        "form":form
    })


def home_logout_view(request:HttpRequest):
    logout(request)
    response = redirect("home:login_view")

    return response


@login_required(login_url="/login")
def book_event_request(request:HttpRequest,id:int):
     try:
          user = request.user
          event = Event.objects.get(pk=id)
          existing_request = Request.objects.filter(event=event, user=user).exists()
          if existing_request:
            return redirect(f'/event/{id}?error=exists')
          
          
   
          new_request = Request(event=event, user=user,status="waiting")
          new_request.save()
          return redirect(f'/event/{id}?success=True')
          


     except Event.DoesNotExist:
            return redirect('home:home_view')


def requests_view(request:HttpRequest):
    if not request.user.is_authenticated:
        messages.warning(request,"يجب تسجيل الدخول للوصول الى الملف الشخصي", "bg-orange-300")
        return redirect("home:login_view")

    user = request.user
    requests = user.user_requests.all()
    for req in requests:
        req.event.startdate_ar = format_date(req.event.start_datetime)
        req.event.enddate_ar = format_date(req.event.end_datetime)
        req.event.dateperiod = f"{req.event.startdate_ar} - {req.event.enddate_ar}"
        req.event.timeperiod = f"{req.event.start_datetime.strftime('%I:%M %p').replace('AM', 'صباحا').replace('PM', 'مساء')} - {req.event.end_datetime.strftime('%I:%M %p').replace('AM', 'صباحا').replace('PM', 'مساء')}"
   

    return render(request, "home/requests.html", {
         "user":user,
         "requests":requests
     })


def cancel_request_view(request:HttpRequest, id:int):
    req = Request.objects.get(pk=id)
    if req:
         req.status = 'canceled'
         req.save()
         return redirect('/requests/?canceled=True')
    
    else:
         return redirect("home:home_view")


def add_rating_for_event(request:HttpRequest, id:int):
    
    if request.POST:
        comment = request.POST['comment']
        rating = request.POST['rating']
        try:
            req = Request.objects.get(pk=id)
            event = Event.objects.get(pk=req.event.id)
            new_rating = Rating(request=req, event=event, stars=int(rating),status=False,comment=comment)
            new_rating.save()
            return redirect('/requests/?ratingadded=True')


        except Request.DoesNotExist as e:
            print(e) 




def profile_view(request:HttpRequest):
    user = request.user

    if not request.user.is_authenticated:
        messages.warning(request,"يجب تسجيل الدخول للوصول الى الملف الشخصي", "bg-orange-300")
        return redirect("home:login_view")

    if request.POST:
        email_exists = User.objects.filter(email=request.POST['email']).exclude(pk=user.id).exists()
        username_exists = User.objects.filter(username=request.POST['username']).exclude(pk=user.id).exists()
        if email_exists or username_exists:
            return redirect(f'/profile/?exists=True')

        else:
            user.first_name = request.POST['first_name']
            user.last_name = request.POST['last_name']
            user.username = request.POST['username']
            user.email = request.POST['email']
            user.save()
            return redirect(f'/profile/?updated=True')

    
    
        
        

    data = {
        "all_events": user.user_requests.count(),
        "accepted_events": user.user_requests.filter(status__in=['accepted', 'attend']).count(),
        "rejected_events": user.user_requests.filter(status='rejected').count(),
        "attended_events": user.user_requests.filter(status='attend').count(),
        "absent_events": user.user_requests.filter(status='absent').count(),
    }
    return render(request, "home/profile.html", {
         "user":user,
         "data":data
     })


def change_password(request:HttpRequest):
    if request.POST:
        user = User.objects.get(username=request.user.username)
        if not check_password(request.POST['current_password'], user.password):
            return redirect(f'/profile/?incorrect_pass=True')
        
        elif not request.POST['new_password'] == request.POST['confirm_password']:
            return redirect(f'/profile/?incoorect_passwords_equals=True')
        
        else:
            user.set_password(request.POST['new_password'])
            user.save()
            return redirect(f'/profile/?updated=True')

        

 
    

    return redirect(f'/profile')
