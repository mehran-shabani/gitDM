import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../repo/patient_repository.dart';
import '../models/patient.dart';

/// \u0635\u0641\u062d\u0647\u0654 \u0644\u06cc\u0633\u062a \u0628\u06cc\u0645\u0627\u0631\u0627\u0646 (Read-only \u0627\u0648\u0644\u06cc\u0647)
class PatientListPage extends StatefulWidget {
  const PatientListPage({super.key});

  @override
  State<PatientListPage> createState() => _PatientListPageState();
}

class _PatientListPageState extends State<PatientListPage> {
  List<Patient> _items = [];
  bool _loading = true;
  String? _error;

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final repo = context.read<PatientRepository>();
      final data = await repo.listPatients();
      if (mounted) setState(() => _items = data);
    } catch (e) {
      if (mounted) {
        setState(() => _error = '\u062e\u0637\u0627 \u062f\u0631 \u062f\u0631\u06cc\u0627\u0641\u062a \u0644\u06cc\u0633\u062a \u0628\u06cc\u0645\u0627\u0631\u0627\u0646');
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('\u0628\u06cc\u0645\u0627\u0631\u0627\u0646')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!))
              : ListView.separated(
                  itemCount: _items.length,
                  separatorBuilder: (_, __) => const Divider(height: 1),
                  itemBuilder: (context, i) {
                    final p = _items[i];
                    return ListTile(
                      title: Text(p.fullName),
                      subtitle: Text('\u0634\u0646\u0627\u0633\u0647: ${p.id}'),
                    );
                  },
                ),
    );
  }
}
