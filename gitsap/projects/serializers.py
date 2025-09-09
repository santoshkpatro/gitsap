from rest_framework import serializers


class ProjectVerifyAccessSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128)
    namespace = serializers.CharField(max_length=150)
    service = serializers.CharField(
        max_length=50
    )  # git-upload-pack[for fetch/clone] or git-receive-pack[for push]
