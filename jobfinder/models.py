from django.db import models
from django.contrib.auth.models import User

#jobpost model
class JobPost(models.Model):
    title = models.CharField()
    description = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=True)

    def__str__(self):
        return self.title