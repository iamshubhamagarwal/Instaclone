# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from custom_addon.models import BaseModel
from django.db import models

# Create your models here.
class UserModel(BaseModel):
    email=models.EmailField(null=False)
    name=models.CharField(max_length=120,unique=True,null=False)
    username=models.CharField(max_length=120)
    password=models.CharField(max_length=255)
    point_count = models.IntegerField(default=True)


class UserSession(BaseModel):
    user= models.ForeignKey(UserModel , on_delete=models.PROTECT)
    session_token=models.CharField(max_length=255)
    is_valid=models.BooleanField(default=True)

    def create_session_token(self):
        from uuid import uuid4
        self.session_token= uuid4()

class PostModel(BaseModel):
  user = models.ForeignKey(UserModel)
  image = models.FileField(upload_to='user_images')
  image_url = models.CharField(max_length=255)
  caption = models.CharField(max_length=240)
  brand = models.CharField(max_length=255)
  popularity = models.CharField(max_length=255)
  point_count=models.IntegerField(default=True)
  @property
  def like_count(self):
          return len(LikeModel.objects.filter(post=self))

  @property
  def comments(self):
      return CommentModel.objects.filter(post=self).order_by('-created_on')


class LikeModel(BaseModel):
    user = models.ForeignKey(UserModel)
    post = models.ForeignKey(PostModel)

class CommentModel(BaseModel):
  user = models.ForeignKey(UserModel)
  post = models.ForeignKey(PostModel)
  comment_text = models.CharField(max_length=555)




