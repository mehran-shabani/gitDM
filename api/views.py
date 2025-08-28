from rest_framework.decorators import api_view
from rest_framework.response import Response
from patients_core.models import Patient
from patients_core.serializers import PatientSerializer
from diab_encounters.serializers import EncounterSerializer
from diab_labs.serializers import LabSerializer
from diab_medications.serializers import MedicationSerializer

@api_view(['GET'])
def export_patient(request, patient_id):
    """Export all patient data"""
    try:
        patient = Patient.objects.get(id=patient_id)
        
        data = {
            'patient': PatientSerializer(patient).data,
            'encounters': EncounterSerializer(patient.encounters.all(), many=True).data,
            'labs': LabSerializer(patient.labs.all(), many=True).data,
            'medications': MedicationSerializer(patient.medications.all(), many=True).data,
            'ai_summaries': [{'id': str(s.id), 'content': s.content, 'created_at': s.created_at} for s in patient.ai_summaries.all()],
        }
        
        return Response(data)
    except Patient.DoesNotExist:
        return Response({'error': 'Patient not found'}, status=404)