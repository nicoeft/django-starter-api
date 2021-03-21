from django.db import models
from project.models import BaseModel


class DeniedToken(BaseModel):
    token = models.CharField(max_length=500, db_index=True)
    user = models.ForeignKey("users.User", related_name='denied_tokens', on_delete=models.CASCADE)

    class Meta:
        db_table = "denied_token"
