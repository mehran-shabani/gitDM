import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'app.dart';
import 'core/config.dart';
import 'core/api_client.dart';
import 'core/token_storage.dart';
import 'features/auth/repo/auth_repository.dart';
import 'features/patients/repo/patient_repository.dart';

/// \u0646\u0642\u0637\u0647\u0654 \u0634\u0631\u0648\u0639 \u0627\u067e.
/// - \u0633\u0627\u062e\u062a \u0648 \u062a\u0632\u0631\u06cc\u0642 TokenStorage \u0648 ApiClient \u0628\u0627 Provider
/// - \u0686\u0627\u067e \u0622\u062f\u0631\u0633 \u0628\u06a9\u200c\u0627\u0646\u062f \u0628\u0631\u0627\u06cc \u0627\u0637\u0645\u06cc\u0646\u0627\u0646 \u0627\u0632 \u062f\u0631\u06cc\u0627\u0641\u062a dart-define
void main() {
  WidgetsFlutterBinding.ensureInitialized();
  final storage = TokenStorage();
  final api = ApiClient(storage);
  final authRepo = AuthRepository(api, storage);
  final patientRepo = PatientRepository(api);

  // \u0635\u0631\u0641\u0627\u064b \u0628\u0631\u0627\u06cc \u062f\u06cc\u0628\u0627\u06af: \u0646\u0645\u0627\u06cc\u0634 \u0622\u062f\u0631\u0633 \u0633\u0631\u0648\u0631 (\u0645\u06cc\u200c\u062a\u0648\u0627\u0646\u06cc\u062f \u062d\u0630\u0641 \u06a9\u0646\u06cc\u062f)
  // ignore: avoid_print
  print('API = ${AppConfig.apiBaseUrl}${AppConfig.apiPrefix}');

  runApp(
    MultiProvider(
      providers: [
        Provider<TokenStorage>.value(value: storage),
        Provider<ApiClient>.value(value: api),
        Provider<AuthRepository>.value(value: authRepo),
        Provider<PatientRepository>.value(value: patientRepo),
      ],
      child: const App(),
    ),
  );
}
