"""Unit tests for export_patient view.

Testing library/framework: Django's unittest TestCase with RequestFactory
(works under pytest-django as well).

Scope: View behavior only (no direct model/serializer tests).
External model access is treated as a service and mocked.
"""

import json
import uuid
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser

from doc.phase7.should_coding_code import export_patient

PATCH_TARGET = "doc.phase7.should_coding_code"  # module path to patch

class ExportPatientViewTests(TestCase):
    def setUp(self):
        """
        یک RequestFactory جدید را برای استفاده در هر تست مقداردهی اولیه می‌کند.
        
        این متد که پیش از اجرای هر مورد آزمون فراخوانی می‌شود، یک نمونه RequestFactory در self.factory ایجاد می‌کند تا درخواست‌های شبیه‌سازی‌شده (GET/POST و غیره) در تست‌های view قابل ساخت و ارسال باشند.
        """
        self.factory = RequestFactory()

    def test_unauthorized_returns_401_json_error(self):
        request = self.factory.get("/export/patient/1")
        request.user = AnonymousUser()

        resp = export_patient(request, pk=1)

        self.assertEqual(resp.status_code, 401)
        self.assertEqual(
            json.loads(resp.content.decode("utf-8")),
            {"error": "unauthorized"},
        )

    def test_patient_not_found_returns_404_json_error(self):
        request = self.factory.get("/export/patient/999")
        request.user = SimpleNamespace(is_authenticated=True)

        class _DoesNotExist(Exception):
            pass

        with patch(PATCH_TARGET + ".Patient") as patient_mock:
            patient_mock.DoesNotExist = _DoesNotExist
            patient_mock.objects.get.side_effect = _DoesNotExist

            resp = export_patient(request, pk=999)

        self.assertEqual(resp.status_code, 404)
        self.assertEqual(
            json.loads(resp.content.decode("utf-8")),
            {"error": "not found"},
        )

    def test_success_returns_200_expected_structure_and_serializes_complex_types(self):
        request = self.factory.get("/export/patient/42")
        request.user = SimpleNamespace(is_authenticated=True)

        # Prepare complex types to validate DjangoJSONEncoder behavior
        pt_uuid = uuid.uuid4()
        collected_at = datetime(2023, 1, 2, 3, 4, 5)
        lab_uuid = uuid.uuid4()

        patient_obj = SimpleNamespace(id=pt_uuid, full_name="John Doe")

        # Encounters
        encounters_list = [
            {"id": 1, "type": "visit", "notes": "routine"},
        ]
        enc_qs = MagicMock()
        enc_qs.values.return_value = encounters_list

        # Labs with datetime and UUID to ensure serialization
        labs_list = [
            {
                "id": 10,
                "collected_at": collected_at,
                "result_uuid": lab_uuid,
                "value": "A1C 6.1",
            },
        ]
        labs_qs = MagicMock()
        labs_qs.values.return_value = labs_list

        # Medications
        meds_list = [
            {"id": 20, "drug": "Metformin", "dose": "500mg"},
        ]
        meds_qs = MagicMock()
        meds_qs.values.return_value = meds_list

        # AI Summaries
        sums_list = [
            {"id": 30, "summary": "Stable"},
        ]
        sums_qs = MagicMock()
        sums_qs.values.return_value = sums_list

        with (
            patch(PATCH_TARGET + ".Patient") as patient_mock,
            patch(PATCH_TARGET + ".Encounter") as enc_mock,
            patch(PATCH_TARGET + ".LabResult") as lab_mock,
            patch(PATCH_TARGET + ".MedicationOrder") as med_mock,
            patch(PATCH_TARGET + ".AISummary") as sum_mock,
        ):
            patient_mock.objects.get.return_value = patient_obj

            enc_mock.objects.filter.return_value = enc_qs
            lab_mock.objects.filter.return_value = labs_qs
            med_mock.objects.filter.return_value = meds_qs
            sum_mock.objects.filter.return_value = sums_qs

            resp = export_patient(request, pk=42)

            # Validate the service/model calls
            patient_mock.objects.get.assert_called_once_with(pk=42)
            enc_mock.objects.filter.assert_called_once_with(patient=patient_obj)
            lab_mock.objects.filter.assert_called_once_with(patient=patient_obj)
            med_mock.objects.filter.assert_called_once_with(patient=patient_obj)
            sum_mock.objects.filter.assert_called_once_with(patient=patient_obj)

            # Ensure .values() used on each queryset
            enc_qs.values.assert_called_once_with()
            labs_qs.values.assert_called_once_with()
            meds_qs.values.assert_called_once_with()
            sums_qs.values.assert_called_once_with()

        self.assertEqual(resp.status_code, 200)
        payload = json.loads(resp.content.decode("utf-8"))

        # Patient section correct and id coerced to string
        self.assertEqual(
            payload["patient"],
            {"id": str(pt_uuid), "name": "John Doe"},
        )

        # Collections present and correct
        self.assertEqual(payload["encounters"], encounters_list)
        # Datetime and UUID should be serialized to strings by DjangoJSONEncoder
        self.assertEqual(
            payload["labs"][0]["collected_at"],
            collected_at.isoformat(),
        )
        self.assertEqual(
            payload["labs"][0]["result_uuid"],
            str(lab_uuid),
        )
        self.assertEqual(payload["medications"], meds_list)
        self.assertEqual(payload["summaries"], sums_list)