import 'package:dio/dio.dart';
import '../../../core/api_client.dart';
import '../models/patient.dart';

/// \u0631\u06cc\u067e\u0627\u0632\u06cc\u062a\u0648\u0631\u06cc \u0628\u06cc\u0645\u0627\u0631\u0627\u0646: \u06a9\u0627\u0631 \u0628\u0627 \u0627\u0646\u062f\u067e\u0648\u06cc\u0646\u062a\u200c\u0647\u0627\u06cc /api/patients/
/// \u0637\u0628\u0642 README: CRUD \u0628\u06cc\u0645\u0627\u0631\u0627\u0646 \u0627\u06cc\u0646 \u0645\u0633\u06cc\u0631 \u0631\u0627 \u062f\u0627\u0631\u062f.
class PatientRepository {
  final ApiClient _client;
  PatientRepository(this._client);

  Future<List<Patient>> listPatients() async {
    final Response resp = await _client.dio.get('/patients/');
    final data = resp.data;

    if (data is List) {
      return data.map((e) => Patient.fromJson(e as Map<String, dynamic>)).toList();
    }

    // \u0627\u06af\u0631 DRF \u0634\u0645\u0627 pagination \u062f\u0627\u0631\u062f (results \u062f\u0627\u062e\u0644 dict)\u060c \u0647\u0646\u062f\u0644 \u0645\u06cc\u200c\u06a9\u0646\u06cc\u0645:
    if (data is Map<String, dynamic> && data['results'] is List) {
      final list = data['results'] as List;
      return list.map((e) => Patient.fromJson(e as Map<String, dynamic>)).toList();
    }

    return [];
  }
}
