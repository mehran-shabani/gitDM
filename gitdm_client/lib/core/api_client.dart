import 'package:dio/dio.dart';
import 'config.dart';
import 'token_storage.dart';

/// \u06a9\u0644\u0627\u06cc\u0646\u062a \u0627\u0635\u0644\u06cc Dio \u0628\u0627 \u0627\u06cc\u0646\u062a\u0631\u0633\u067e\u062a\u0648\u0631 \u0628\u0631\u0627\u06cc:
/// 1) \u0627\u0641\u0632\u0648\u062f\u0646 \u0647\u062f\u0631 Authorization \u0628\u0627 access token
/// 2) \u0647\u0646\u062f\u0644 401 \u2192 \u0631\u0641\u0631\u0634 \u062a\u0648\u06a9\u0646 \u0628\u0627 /api/token/refresh/ \u0648 \u062a\u06a9\u0631\u0627\u0631 \u0647\u0645\u0627\u0646 \u062f\u0631\u062e\u0648\u0627\u0633\u062a
class ApiClient {
  final Dio _dio;
  final TokenStorage _storage;

  ApiClient(this._storage)
      : _dio = Dio(BaseOptions(
          baseUrl: AppConfig.apiBaseUrl + AppConfig.apiPrefix, // \u0645\u062b\u0644: http://localhost:8000/api
          connectTimeout: const Duration(seconds: 15),
          receiveTimeout: const Duration(seconds: 20),
          headers: {'Accept': 'application/json'},
        )) {
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final access = await _storage.getAccess();
        if (access != null && access.isNotEmpty) {
          options.headers['Authorization'] = 'Bearer ' + access;
        }
        return handler.next(options);
      },
      onError: (e, handler) async {
        if (e.response?.statusCode == 401) {
          final refreshed = await _tryRefreshToken();
          if (refreshed) {
            final req = e.requestOptions;
            final access = await _storage.getAccess();
            req.headers['Authorization'] = 'Bearer ' + access!;
            try {
              final clone = await _dio.fetch(req);
              return handler.resolve(clone);
            } catch (e2) {
              return handler.reject(e2 as DioException);
            }
          }
        }
        return handler.next(e);
      },
    ));
  }

  Dio get dio => _dio;

  /// \u0641\u0631\u0627\u062e\u0648\u0627\u0646\u06cc /api/token/refresh/ \u0637\u0628\u0642 SimpleJWT
  Future<bool> _tryRefreshToken() async {
    final refresh = await _storage.getRefresh();
    if (refresh == null || refresh.isEmpty) return false;

    try {
      final resp = await _dio.post('/token/refresh/', data: {'refresh': refresh});
      final data = resp.data as Map<String, dynamic>;
      final newAccess = data['access'] as String?;
      final newRefresh = (data['refresh'] as String?) ?? refresh;

      if (newAccess != null && newAccess.isNotEmpty) {
        await _storage.saveTokens(access: newAccess, refresh: newRefresh);
        return true;
      }
      return false;
    } on DioException {
      await _storage.clear();
      return false;
    }
  }
}
