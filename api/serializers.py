from rest_framework import serializers
from clinical_refs.models import ClinicalReference

class ClinicalReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicalReference
        fields = '__all__'