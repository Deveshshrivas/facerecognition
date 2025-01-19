from djongo import models

class Frame(models.Model):
    user_id = models.CharField(max_length=255)
    frames = models.JSONField()
    captured_at = models.DateTimeField(auto_now_add=True)