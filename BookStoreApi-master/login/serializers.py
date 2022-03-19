from rest_framework import serializers

class UserSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, max_length=20)
    password = serializers.CharField(required=True, max_length=20)


class OtpSerializer(serializers.Serializer):
    mobile_num = serializers.CharField(required=True, max_length=12)
    otp = serializers.CharField(required=True, max_length=6)
