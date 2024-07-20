from django.contrib.auth.models import User
from django.db import models

ADMIN_TYPE_CHOICES = (
    ("reviewer", "Reviewer"), ("authorizer", "Authorizer"), ("admin", "Admin"), ("super_admin", "Super Admin")
)


class Role(models.Model):
    admin_type = models.CharField(max_length=100, choices=ADMIN_TYPE_CHOICES, default="reviewer")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.admin_type}"


class AdminUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    update_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user}: {self.role.admin_type}"
