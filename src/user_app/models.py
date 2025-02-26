from django.contrib.auth.models import AbstractUser, User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    bio = models.CharField(max_length=100, blank=True)
    image = models.ImageField(upload_to="user_images", default="default.jpg")

    def save(self, *args, **kwargs):
        if not self.bio:
            self.bio = self.user.username
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return self.user.first_name + " " + self.user.last_name

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()
