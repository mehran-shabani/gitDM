import 'package:shared_preferences/shared_preferences.dart';

/// \u0646\u06af\u0647\u062f\u0627\u0631\u06cc \u062a\u0648\u06a9\u0646\u200c\u0647\u0627\u06cc JWT \u062f\u0631 \u06a9\u0644\u0627\u06cc\u0646\u062a.
/// \u0646\u06a9\u062a\u0647 \u0627\u0645\u0646\u06cc\u062a\u06cc: \u0628\u0631\u0627\u06cc \u0645\u062d\u0635\u0648\u0644 \u0646\u0647\u0627\u06cc\u06cc \u0628\u0647\u062a\u0631 \u0627\u0633\u062a \u0627\u0632 flutter_secure_storage \u0627\u0633\u062a\u0641\u0627\u062f\u0647 \u0634\u0648\u062f.
/// \u0627\u06cc\u0646\u062c\u0627 \u0628\u0631\u0627\u06cc \u0633\u0627\u062f\u06af\u06cc PoC \u0627\u0632 SharedPreferences \u0627\u0633\u062a\u0641\u0627\u062f\u0647 \u0645\u06cc\u200c\u06a9\u0646\u06cc\u0645.
class TokenStorage {
  static const _kAccess = 'access_token';
  static const _kRefresh = 'refresh_token';

  Future<void> saveTokens({required String access, required String refresh}) async {
    final sp = await SharedPreferences.getInstance();
    await sp.setString(_kAccess, access);
    await sp.setString(_kRefresh, refresh);
  }

  Future<String?> getAccess() async {
    final sp = await SharedPreferences.getInstance();
    return sp.getString(_kAccess);
  }

  Future<String?> getRefresh() async {
    final sp = await SharedPreferences.getInstance();
    return sp.getString(_kRefresh);
  }

  Future<void> clear() async {
    final sp = await SharedPreferences.getInstance();
    await sp.remove(_kAccess);
    await sp.remove(_kRefresh);
  }
}
