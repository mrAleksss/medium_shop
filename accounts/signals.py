from .models import UserProfile, Account
from django.dispatch import receiver
from django.db.models.signals import post_save


@receiver(post_save, sender=Account)
def create_profile(sender, instance, created, **kwargs):
    print(sender)
    print(instance)
    print(created)
    if created:
        UserProfile.objects.create(user=instance)