import 'package:dio/dio.dart';
import '../../../core/api_client.dart';
import '../../../core/token_storage.dart';
import '../models/token_pair.dart';

/// \u0631\u06cc\u067e\u0627\u0632\u06cc\u062a\u0648\u0631\u06cc \u0627\u062d\u0631\u0627\u0632 \u0647\u0648\u06cc\u062a:
/// - login: \u062f\u0631\u06cc\u0627\u0641\u062a access/refresh \u0627\u0632 /api/token/
/// - logout: \u067e\u0627\u06a9\u200c\u06a9\u0631\u062f\u0646 \u062a\u0648\u06a9\u0646\u200c\u0647\u0627
class AuthRepository {
  final ApiClient _client;
  final TokenStorage _storage;

  AuthRepository(this._client, this._storage);

  Future<void> login({required String username, required String password}) async {
    // \u062f\u0631 DRF SimpleJWT\u060c \u0641\u06cc\u0644\u062f\u0647\u0627 \u0645\u0645\u06a9\u0646 \u0627\u0633\u062a username/password \u06cc\u0627 email/password \u0628\u0627\u0634\u062f.
    final Response resp = await _client.dio.post('/token/', data: {
      'username': username,
      'password': password,
    });

    final pair = TokenPair.fromJson(resp.data as Map<String, dynamic>);
    if (pair.access.isEmpty || pair.refresh.isEmpty) {
      throw Exception('Invalid token response');
    }
    await _storage.saveTokens(access: pair.access, refresh: pair.refresh);
  }

  Future<void> logout() async {
    await _storage.clear();
  }
}
