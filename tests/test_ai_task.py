import pytest
from ai_summarizer.tasks import summarize_record
from patients_core.models import Patient

@pytest.mark.django_db
def test_summarize_creates_summary(monkeypatch):
    p = Patient.objects.create(full_name="Ali Test", primary_doctor_id="00000000-0000-0000-0000-000000000010")

    class DummyResp:
        def __getitem__(self, k):
            return {"choices":[{"message":{"content":"خلاصه تست"}}]}[k]
    
    monkeypatch.setattr("openai.ChatCompletion.create", lambda **kwargs: {"choices":[{"message":{"content":"خلاصه تست"}}]})

    sid = summarize_record(p.id, 'Encounter', '1111', {"subjective":"x"})
    assert sid is not None