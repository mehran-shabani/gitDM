# معماری فاز ۰۸ – Test Flow
- مسیر end-to-end: User → JWT → Patient → Encounter/Lab/Med → AI Summary → Versioning → Timeline → Export
- ابزار تست: pytest + DRF APIClient
- Mock برای OpenAI API
- پایگاه داده تمیز (pytest-django)