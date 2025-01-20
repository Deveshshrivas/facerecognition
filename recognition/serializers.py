from rest_framework import serializers
from .models import User, Video

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = '__all__'

class ImageSerializer(serializers.Serializer):
    userID = serializers.CharField(max_length=100)
    imageID = serializers.CharField(max_length=100)
    image = serializers.ImageField()