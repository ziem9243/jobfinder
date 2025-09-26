from django.db import models
from djago.contrib.auth.models import Group, Permission

# Roles
moderators = Group.objects.create(name="Moderators")
admins = Group.objects.create(name="Admins")

# Permissions
perm = Permission.objects.get(codename='change_user')
admins.permissions.add(perm)

user.groups.add(admins)