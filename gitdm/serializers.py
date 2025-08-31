from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import PatientProfile, User


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'


class PatientSerializer(serializers.ModelSerializer):
    primary_doctor_id = serializers.IntegerField(source='primary_doctor.id', read_only=True)

    class Meta:
        model = PatientProfile
        fields = ['id', 'user', 'national_id', 'full_name', 'dob', 'sex', 'primary_doctor', 'primary_doctor_id', 'created_at']
        read_only_fields = ['id', 'created_at', 'primary_doctor_id']

    def create(self, validated_data):
        if 'user' not in validated_data and self.context.get('request'):
            validated_data['user'] = self.context['request'].user
        return super().create(validated_data)