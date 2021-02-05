from django.db import models
import uuid
from datetime import date

from django.urls import reverse

from sitewide.models import ZappyUser


class Invite(models.Model):
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    end_date = models.DateField()
    sender = models.ForeignKey(ZappyUser, on_delete=models.CASCADE, null=True, blank=True, related_name='invites_sent')
    receiver = models.ForeignKey(ZappyUser, on_delete=models.CASCADE, null=True, blank=True,
                                 related_name='invites_used')

    def __str__(self):
        if self.sender:
            return f'{self.sender.username} - {self.token}'
        else:
            return f'No Sender - {self.token}'

    def get_absolute_url(self):
        return reverse('invites:invite_landing_page', kwargs={'token': self.token})

    # method to check if user has got active invite.
    # if yes return expiration date, if not return None
    @staticmethod
    def has_invite(user):
        for invite in Invite.objects.filter(receiver_id=user.id):
            if not invite.is_expired():
                return invite.end_date
        return None

    def is_expired(self):
        return date.today() > self.end_date

    def days_left(self):
        return (self.end_date - date.today()).days
