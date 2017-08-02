from django.db import models

class BaseModel(models.Model):
    """
    This is base model
    """
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        abstract=True