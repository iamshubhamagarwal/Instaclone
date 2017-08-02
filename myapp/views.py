# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.http import HttpResponse
from django.shortcuts import render,redirect
from form import SignUpForm,LoginForm,PostForm,LikeForm,CommentForm
from models import UserModel,UserSession,PostModel,LikeModel,CommentModel
from django.contrib.auth.hashers import make_password,check_password
from imgurpython import ImgurClient
from linkinpark.settings import BASE_DIR
from clarifai.rest import ClarifaiApp
import sendgrid
from sendgrid.helpers.mail import *


YOUR_CLIENT_ID='b4c26818f859c60'
YOUR_CLIENT_SECRET='db9db6664dfd40aced0d05d71309b1d53dc96591'
API_KEY='a08a3ac8121d442ba5a967eecdca029d'
SENDGRID_API_KEY="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"



# Create your views here.
def signup_view(request):
    import datetime
    date = datetime.datetime.now()
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            if len(username)>4:
                if len(password)>5:

                    user = UserModel(name=name, password=make_password(password), email=email, username=username)
                    user.save()

                    sg = sendgrid.SendGridAPIClient(apikey=SENDGRID_API_KEY)
                    from_email = Email("help@instaclone.com")
                    to_email = Email(email)
                    subject = "Sucessfully SIGNED UP!"
                    content = Content("text/plain", "Welcome to Instaclone application. Enjoy your experience :)!")
                    mail = Mail(from_email, subject, to_email, content)
                    response = sg.client.mail.send.post(request_body=mail.get())

                    if response.status_code==202:
                        message = "Email Send! :)"
                    else:
                        message="Unable to send Email! :("
                    return render(request, 'success.html',{'response': message})
                else:
                    print "Password should be of atleast 6 characters!"
            else:
                print "UserName should be of atleast 5 characters!"
    else:
        form = SignUpForm()

    return render(request, 'index.html', {'form':form , 'abhi_ka_time' : date})

def login_view(request):
    import datetime
    date = datetime.datetime.now()
    response_data = {}
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = UserModel.objects.filter(username=username).first()

            if user:
                if check_password(password, user.password):
                    token = UserSession(user=user)
                    token.create_session_token()
                    token.save()
                    response = redirect('feed/')
                    response.set_cookie(key='session_token', value=token.session_token)
                    return response
                else:
                    response_data['message'] = 'Incorrect Password! Please try again!'

    elif request.method == 'GET':
        form = LoginForm()

    response_data['form'] = form
    return render(request, 'login.html', response_data ,{'abhi_ka_time' : date})


def feed_view(request):
    user = check_validation(request)
    if user:
        posts = PostModel.objects.all().order_by('-created_on')
        for post in posts:
            existing_like = LikeModel.objects.filter(post_id=post.id, user=user).first()
            if existing_like:
                post.has_liked = True

        return render(request, 'feed.html', {'posts' : posts})
    else:
        return redirect('/login/')


def post_view(request):
    user = check_validation(request)
    try:
        if user:
          #if request.method=='GET':
          #  form =PostForm()
            if request.method == 'POST':
                form = PostForm(request.POST, request.FILES)
                if form.is_valid():
                    image = form.cleaned_data.get('image')
                    caption = form.cleaned_data.get('caption')
                    if image:
                        post = PostModel(user=user, image=image, caption=caption)
                        post.save()
                        path=str(BASE_DIR + "\\" + post.image.url)
                        client = ImgurClient(YOUR_CLIENT_ID, YOUR_CLIENT_SECRET)
                        post.image_url = client.upload_from_path(path, anon=True)['link']#rhs gives url of pic on imgur.
                        post.save()
                        url=post.image_url
                        app = ClarifaiApp(api_key=API_KEY)
                        model = app.models.get('Logo')
                        response = model.predict_by_url(url=url)
                        if response["status"]["code"] == 10000:
                            if response["outputs"]:
                                if response["outputs"][0]["data"]:
                                    if response["outputs"][0]["data"]["concepts"]:
                                        b_name=response["outputs"][0]["data"]['regions'][0]['data']["concepts"][0]["name"]
                                        post.brand = b_name

                                        popularity=response["outputs"][0]["data"]['regions'][0]['data']["concepts"][0]["value"]
                                        post.popularity = popularity

                                        count =1
                                        #result = PostModel(user=user,brand=b_name, popularity=popularity)
                                        post.point_count=count
                                        post = PostModel(user=user, image=image, caption=caption,image_url=url,brand=b_name,popularity=popularity,point_count=count)
                                        post.save()


                                    else:
                                        print "No Concepts List Error"
                                else:
                                    print "No Data List Error"
                            else:
                                print "No Outputs List Error"
                        else:
                            print "Response Code Error"

                        return redirect('/feed/' )
                    else:
                        message= "select a image"

                        return render(request, 'post.html', {'message': message})

            else:
                form = PostForm()
            return render(request, 'post.html', {'form' : form})
        else:
            return redirect('/login')
    except:
        ValueError

def check_validation(request):
    if request.COOKIES.get('session_token'):
        session = UserSession.objects.filter(session_token=request.COOKIES.get('session_token')).first()
        if session:
            return session.user
    else:
        return None

def like_view(request):
  user = check_validation(request)
  if user and request.method == 'POST':
    form=LikeForm(request.POST)
    if form.is_valid():
        post_id=form.cleaned_data.get('post').id
        existing_like = LikeModel.objects.filter(post_id=post_id, user=user).first()
        if not existing_like:
            LikeModel.objects.create(post_id=post_id, user=user)
            postget = PostModel.objects.filter(id=post_id).first()
            userid = postget.user_id
            user = UserModel.objects.filter(id=userid).first()
            email = user.email
            sg = sendgrid.SendGridAPIClient(apikey=SENDGRID_API_KEY)
            from_email = Email("help@instaclone.com")
            to_email = Email(email)
            subject = "InstaClone : SomeOne liked your post!"
            content = Content("text/plain", "You got a like on your post! check it out:)")
            mail = Mail(from_email, subject, to_email, content)
            response = sg.client.mail.send.post(request_body=mail.get())

        else:
            existing_like.delete()
        return redirect('/feed/')
  else:
    return redirect('/login/')


def comment_view(request):
    user = check_validation(request)
    if user and request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            post_id = form.cleaned_data.get('post').id
            comment_text = form.cleaned_data.get('comment_text')
            comment = CommentModel.objects.create(user=user, post_id=post_id, comment_text=comment_text)
            comment.save()
            postget=PostModel.objects.filter(id=post_id).first()
            userid=postget.user_id
            user=UserModel.objects.filter(id=userid).first()
            email=user.email
            sg = sendgrid.SendGridAPIClient(apikey=SENDGRID_API_KEY)
            from_email = Email("help@instaclone.com")
            to_email = Email(email)
            subject = "InstaClone : New comment on your post!"
            content = Content("text/plain", "Someone just commented on your post! check it out:)")
            mail = Mail(from_email, subject, to_email, content)
            response = sg.client.mail.send.post(request_body=mail.get())

            return redirect('/feed/')
        else:
            return redirect('/feed/')
    else:
        return redirect('/login')

