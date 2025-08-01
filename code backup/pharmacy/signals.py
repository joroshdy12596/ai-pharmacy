from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    # Only create a profile if one doesn't exist
    if created and not hasattr(instance, 'userprofile'):
        UserProfile.objects.create(
            user=instance,
            role='CASHIER'  # Default role
        )

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Only update existing profile, don't create new one
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()