import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../auth/repo/auth_repository.dart';

/// \u0635\u0641\u062d\u0647\u0654 \u0648\u0631\u0648\u062f \u0633\u0627\u062f\u0647:
/// - \u062f\u0648 \u0641\u06cc\u0644\u062f username/password
/// - \u0631\u0648\u06cc \u0645\u0648\u0641\u0642\u06cc\u062a\u060c \u0646\u0627\u0648\u0628\u0631\u06cc \u0628\u0647 \u0644\u06cc\u0633\u062a \u0628\u06cc\u0645\u0627\u0631\u0627\u0646
class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _userCtrl = TextEditingController();
  final _passCtrl = TextEditingController();
  bool _busy = false;
  String? _error;

  Future<void> _onLogin() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final authRepo = context.read<AuthRepository>();

      await authRepo.login(
        username: _userCtrl.text.trim(),
        password: _passCtrl.text,
      );

      if (!mounted) return;
      Navigator.of(context).pushReplacementNamed('/patients');
    } catch (e) {
      setState(() => _error = '\u0648\u0631\u0648\u062f \u0646\u0627\u0645\u0648\u0641\u0642. \u0644\u0637\u0641\u0627\u064b \u0627\u0637\u0644\u0627\u0639\u0627\u062a \u0631\u0627 \u0628\u0631\u0631\u0633\u06cc \u06a9\u0646\u06cc\u062f.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('\u0648\u0631\u0648\u062f')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(controller: _userCtrl, decoration: const InputDecoration(labelText: '\u0646\u0627\u0645 \u06a9\u0627\u0631\u0628\u0631\u06cc/\u0627\u06cc\u0645\u06cc\u0644')),
            const SizedBox(height: 8),
            TextField(controller: _passCtrl, decoration: const InputDecoration(labelText: '\u0631\u0645\u0632 \u0639\u0628\u0648\u0631'), obscureText: true),
            const SizedBox(height: 16),
            if (_error != null) Text(_error!, style: const TextStyle(color: Colors.red)),
            const SizedBox(height: 8),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _busy ? null : _onLogin,
                child: _busy ? const CircularProgressIndicator() : const Text('\u0648\u0631\u0648\u062f'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
