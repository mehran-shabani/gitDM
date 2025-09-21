import 'package:flutter/material.dart';
import 'features/auth/ui/login_page.dart';
import 'features/patients/ui/patient_list_page.dart';

/// \u0645\u0633\u06cc\u0631\u0628\u0646\u062f\u06cc \u0633\u0627\u062f\u0647\u0654 \u0627\u067e:
/// - '/' \u2192 \u0635\u0641\u062d\u0647\u0654 \u0648\u0631\u0648\u062f
/// - '/patients' \u2192 \u0644\u06cc\u0633\u062a \u0628\u06cc\u0645\u0627\u0631\u0627\u0646
class App extends StatelessWidget {
  const App({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'GitDM Client',
      theme: ThemeData(useMaterial3: true, colorSchemeSeed: const Color(0xFF00BB77)),
      initialRoute: '/',
      routes: {
        '/': (_) => const LoginPage(),
        '/patients': (_) => const PatientListPage(),
      },
    );
  }
}
