from __future__ import annotations

from rest_framework import serializers


class BotSettingsUpdateSerializer(serializers.Serializer):
    settings = serializers.DictField(child=serializers.JSONField(), allow_empty=True)
    write_to_database = serializers.BooleanField(required=False, default=True)
    write_to_env = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        if attrs.get("write_to_env"):
            raise serializers.ValidationError("Writing bot settings to .env is disabled. Use database runtime settings only.")
        if not attrs.get("write_to_database"):
            raise serializers.ValidationError("Runtime bot settings must be saved to the database.")
        return attrs
