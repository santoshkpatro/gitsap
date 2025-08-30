from rest_framework import serializers

from gitsap.users.models import User


class LoginSerializer(serializers.Serializer):
    identity = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    remember = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        identity = attrs.pop("identity", "")

        if "@" in identity:
            attrs["email"] = identity
        else:
            attrs["username"] = identity

        return attrs


class LoggedInUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "full_name"]
