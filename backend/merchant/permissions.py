from rest_framework.permissions import BasePermission
from merchant.models import Seller

from superadmin.models import AdminUser


class IsMerchant(BasePermission):
    """
    Allows access only to authenticated users.
    """

    def has_permission(self, request, view):
        try:
            seller = Seller.objects.filter(user=request.user)
        except (Seller.DoesNotExist, ):
            return False
        else:
            return bool(request.user and request.user.is_authenticated and seller is not None)


class IsReviewer(BasePermission):

    def has_permission(self, request, view):
        try:
            admin_user = AdminUser.objects.get(user=request.user)
        except AdminUser.DoesNotExist:
            return False
        if admin_user.role.admin_type == "reviewer":
            return True
        else:
            return


class IsAuthorizer(BasePermission):

    def has_permission(self, request, view):
        try:
            admin_user = AdminUser.objects.get(user=request.user)
        except AdminUser.DoesNotExist:
            return False
        if admin_user.role.admin_type == "authorizer":
            return True
        else:
            return


class IsAdmin(BasePermission):

    def has_permission(self, request, view):
        try:
            admin_user = AdminUser.objects.get(user=request.user)
        except AdminUser.DoesNotExist:
            return False
        if admin_user.role.admin_type == "admin":
            return True
        else:
            return


class IsSuperAdmin(BasePermission):

    def has_permission(self, request, view):
        try:
            admin_user = AdminUser.objects.get(user=request.user)
        except AdminUser.DoesNotExist:
            return False
        if admin_user.role.admin_type == "super_admin" or request.user.is_superuser:
            return True
        else:
            return






