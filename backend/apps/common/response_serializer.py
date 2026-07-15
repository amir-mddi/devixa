from rest_framework import serializers


class ResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    code = serializers.CharField()
    message = serializers.CharField()
    status_code = serializers.IntegerField(write_only=True)
    data = serializers.DictField(default=[])
