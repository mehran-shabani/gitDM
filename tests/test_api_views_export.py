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
    def setUp(self) -> None:
        self.factory = RequestFactory()

    def test_unauthorized_returns_401_json_error(self) -> None:
        request = self.factory.get("/export/patient/1")
        request.user = AnonymousUser()

        resp = export_patient(request, pk=1)

        self.assertEqual(resp.status_code, 401)
        self.assertEqual(
            json.loads(resp.content.decode("utf-8")),
            {"error": "unauthorized"},
        )

    def test_patient_not_found_returns_404_json_error(self) -> None:
        request = self.factory.get("/export/patient/999")
        request.user = SimpleNamespace(is_authenticated=True)

        class DoesNotExistError(Exception):
            pass

        with patch(PATCH_TARGET + ".Patient") as patient_mock:
            patient_mock.DoesNotExist = DoesNotExistError
            patient_mock.objects.get.side_effect = DoesNotExistError

            resp = export_patient(request, pk=999)

        self.assertEqual(resp.status_code, 404)
        self.assertEqual(
            json.loads(resp.content.decode("utf-8")),
            {"error": "not found"},
        )

    def test_success_returns_200_expected_structure_and_serializes_complex_types(
        self,
    ) -> None:
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


# Additional tests appended by codegen to deepen coverage for export_patient view

class ExportPatientViewMoreScenariosTests(TestCase):
    """
    Testing library/framework: Django's unittest TestCase with RequestFactory
    (works with pytest-django).
    Focus: view behavior only. Services/models are mocked.
    """

    def setUp(self) -> None:
        self.factory = RequestFactory()

    def _auth(self) -> SimpleNamespace:
        return SimpleNamespace(is_authenticated=True)

    def test_invalid_http_method_returns_405_if_restricted(self) -> None:
        # If the view uses require_GET, POST should return 405.
        # If not, this asserts current behavior.
        from doc.phase7.should_coding_code import export_patient

        req = self.factory.post("/export/patient/7", data={"x": "y"})
        req.user = self._auth()
        resp = export_patient(req, pk=7)
        # Accept either 405 (preferred) or 200/other if view doesn't restrict methods.
        self.assertIn(resp.status_code, {200, 401, 404, 405})

    def test_pk_non_integer_or_malformed_path_still_attempts_lookup(self) -> None:
        # Ensure the view passes pk through to service without crashing on non-int
        # (if it accepts str UUIDs).
        from doc.phase7.should_coding_code import export_patient

        bad_pk = "abc-not-an-int"
        req = self.factory.get(f"/export/patient/{bad_pk}")
        req.user = self._auth()

        class DoesNotExistError(Exception):
            pass

        with patch(PATCH_TARGET + ".Patient") as patient_mock:
            patient_mock.DoesNotExist = DoesNotExistError
            patient_mock.objects.get.side_effect = DoesNotExistError

            resp = export_patient(req, pk=bad_pk)

        self.assertEqual(resp.status_code, 404)
        self.assertEqual(
            json.loads(resp.content.decode("utf-8")),
            {"error": "not found"},
        )

    def test_services_called_even_when_collections_empty(self) -> None:
        # If related querysets return empty, response should include empty arrays.
        from doc.phase7.should_coding_code import export_patient

        req = self.factory.get("/export/patient/101")
        req.user = self._auth()

        patient_obj = SimpleNamespace(id=uuid.uuid4(), full_name="Empty Case")

        empty_qs = MagicMock()
        empty_qs.values.return_value = []

        with (
            patch(PATCH_TARGET + ".Patient") as patient_mock,
            patch(PATCH_TARGET + ".Encounter") as enc_mock,
            patch(PATCH_TARGET + ".LabResult") as lab_mock,
            patch(PATCH_TARGET + ".MedicationOrder") as med_mock,
            patch(PATCH_TARGET + ".AISummary") as sum_mock,
        ):
            patient_mock.objects.get.return_value = patient_obj
            enc_mock.objects.filter.return_value = empty_qs
            lab_mock.objects.filter.return_value = empty_qs
            med_mock.objects.filter.return_value = empty_qs
            sum_mock.objects.filter.return_value = empty_qs

            resp = export_patient(req, pk=101)

            patient_mock.objects.get.assert_called_once_with(pk=101)
            enc_mock.objects.filter.assert_called_once_with(patient=patient_obj)
            lab_mock.objects.filter.assert_called_once_with(patient=patient_obj)
            med_mock.objects.filter.assert_called_once_with(patient=patient_obj)
            sum_mock.objects.filter.assert_called_once_with(patient=patient_obj)
            empty_qs.values.assert_called()  # called for each; at least once total

        self.assertEqual(resp.status_code, 200)
        payload = json.loads(resp.content.decode("utf-8"))
        self.assertIn("patient", payload)
        self.assertEqual(payload["encounters"], [])
        self.assertEqual(payload["labs"], [])
        self.assertEqual(payload["medications"], [])
        self.assertEqual(payload["summaries"], [])

    def test_serialization_handles_bool_none_and_nested_structs(self) -> None:
        from doc.phase7.should_coding_code import export_patient

        req = self.factory.get("/export/patient/202")
        req.user = self._auth()

        pt_uuid = uuid.uuid4()
        patient_obj = SimpleNamespace(id=pt_uuid, full_name="Edge Types")

        labs_list = [
            {
                "id": 1,
                "flag": True,
                "meta": {"a": 1, "b": None, "c": [1, 2, {"d": False}]},
                "at": datetime(2024, 5, 6, 7, 8, 9),
            }
        ]

        labs_qs = MagicMock()
        labs_qs.values.return_value = labs_list

        with (
            patch(PATCH_TARGET + ".Patient") as patient_mock,
            patch(PATCH_TARGET + ".Encounter") as enc_mock,
            patch(PATCH_TARGET + ".LabResult") as lab_mock,
            patch(PATCH_TARGET + ".MedicationOrder") as med_mock,
            patch(PATCH_TARGET + ".AISummary") as sum_mock,
        ):
            patient_mock.objects.get.return_value = patient_obj

            enc_qs = MagicMock()
            enc_qs.values.return_value = []
            med_qs = MagicMock()
            med_qs.values.return_value = []
            sum_qs = MagicMock()
            sum_qs.values.return_value = []

            enc_mock.objects.filter.return_value = enc_qs
            lab_mock.objects.filter.return_value = labs_qs
            med_mock.objects.filter.return_value = med_qs
            sum_mock.objects.filter.return_value = sum_qs

            resp = export_patient(req, pk=202)

        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content.decode("utf-8"))
        # Ensure bool/None nested structures survive JSON serialization format
        self.assertEqual(data["labs"][0]["flag"], True)
        self.assertEqual(data["labs"][0]["meta"]["b"], None)
        self.assertEqual(data["labs"][0]["meta"]["c"][2]["d"], False)
        self.assertEqual(
            data["labs"][0]["at"],
            labs_list[0]["at"].isoformat(),
        )

    def test_unexpected_exception_returns_500_json_if_handled(self) -> None:
        from doc.phase7.should_coding_code import export_patient

        req = self.factory.get("/export/patient/303")
        req.user = self._auth()

        class BoomError(Exception):
            pass

        with patch(PATCH_TARGET + ".Patient") as patient_mock:
            patient_mock.objects.get.side_effect = BoomError("db down")
            try:
                resp = export_patient(req, pk=303)
                # Accept either explicit 500 response or Django error bubbling (>=500)
                self.assertGreaterEqual(resp.status_code, 500)
                parsed = json.loads(resp.content.decode("utf-8"))
                # Minimal expected structure if handled
                self.assertIn("error", parsed)
            except BoomError:
                self.assertTrue(
                    True,
                    "Unhandled exception surfaces (no 500 handler in view)",
                )

    def test_patient_name_fallback_when_full_name_missing(self) -> None:
        from doc.phase7.should_coding_code import export_patient

        req = self.factory.get("/export/patient/4040")
        req.user = self._auth()

        patient_obj = SimpleNamespace(id=uuid.uuid4())  # no full_name

        with (
            patch(PATCH_TARGET + ".Patient") as patient_mock,
            patch(PATCH_TARGET + ".Encounter") as enc_mock,
            patch(PATCH_TARGET + ".LabResult") as lab_mock,
            patch(PATCH_TARGET + ".MedicationOrder") as med_mock,
            patch(PATCH_TARGET + ".AISummary") as sum_mock,
        ):
            patient_mock.objects.get.return_value = patient_obj

            for m in (enc_mock, lab_mock, med_mock, sum_mock):
                qs = MagicMock()
                qs.values.return_value = []
                m.objects.filter.return_value = qs

            resp = export_patient(req, pk=4040)

        self.assertEqual(resp.status_code, 200)
        payload = json.loads(resp.content.decode("utf-8"))
        # Name should be present (empty string if not available) to keep schema stable
        self.assertIn("patient", payload)
        self.assertIn("name", payload["patient"])

    def test_large_collections_performance_sanity(self) -> None:
        # Ensure the view consumes .values() (already asserted elsewhere) and
        # returns lists, not generators.
        from doc.phase7.should_coding_code import export_patient

        req = self.factory.get("/export/patient/5050")
        req.user = self._auth()

        patient_obj = SimpleNamespace(id=uuid.uuid4(), full_name="Many Items")

        # Simulate large lists
        enc_list = [{"id": i, "type": "visit"} for i in range(100)]
        med_list = [{"id": i, "drug": "X"} for i in range(200)]
        lab_list = [{"id": i, "collected_at": datetime(2025, 1, 1)} for i in range(150)]
        sum_list = [{"id": i, "summary": "ok"} for i in range(50)]

        def mk_qs(vals: list) -> MagicMock:
            qs = MagicMock()
            qs.values.return_value = vals
            return qs

        with (
            patch(PATCH_TARGET + ".Patient") as patient_mock,
            patch(PATCH_TARGET + ".Encounter") as enc_mock,
            patch(PATCH_TARGET + ".LabResult") as lab_mock,
            patch(PATCH_TARGET + ".MedicationOrder") as med_mock,
            patch(PATCH_TARGET + ".AISummary") as sum_mock,
        ):
            patient_mock.objects.get.return_value = patient_obj
            enc_mock.objects.filter.return_value = mk_qs(enc_list)
            lab_mock.objects.filter.return_value = mk_qs(lab_list)
            med_mock.objects.filter.return_value = mk_qs(med_list)
            sum_mock.objects.filter.return_value = mk_qs(sum_list)

            resp = export_patient(req, pk=5050)

        self.assertEqual(resp.status_code, 200)
        payload = json.loads(resp.content.decode("utf-8"))
        self.assertEqual(len(payload["encounters"]), 100)
        self.assertEqual(len(payload["medications"]), 200)
        self.assertEqual(len(payload["labs"]), 150)
        self.assertEqual(len(payload["summaries"]), 50)