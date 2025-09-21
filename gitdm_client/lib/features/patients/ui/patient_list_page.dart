import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:dio/dio.dart';
import '../repo/patient_repository.dart';
import '../models/patient.dart';

/// صفحهٔ لیست بیماران (Read-only اولیه)
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
        final code = (e is DioException) ? e.response?.statusCode : null;
        if (code == 401) {
          // توکن معتبر نیست؛ برگرد به لاگین
          Navigator.of(context).pushReplacementNamed('/');
          return;
        }
        setState(() => _error = 'خطا در دریافت لیست بیماران');
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
      appBar: AppBar(title: const Text('بیماران')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(_error!),
                      const SizedBox(height: 12),
                      ElevatedButton(
                        onPressed: _load,
                        child: const Text('تلاش مجدد'),
                      ),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _load,
                  child: _items.isEmpty
                      ? ListView(
                          children: const [
                            SizedBox(height: 160),
                            Center(child: Text('هنوز بیماری ثبت نشده')),
                          ],
                        )
                      : ListView.separated(
                          itemCount: _items.length,
                          separatorBuilder: (_, __) => const Divider(height: 1),
                          itemBuilder: (context, i) {
                            final p = _items[i];
                            return ListTile(
                              key: ValueKey(p.id),
                              title: Text(p.fullName),
                              subtitle: Text('شناسه: ${p.id}'),
                            );
                          },
                        ),
                ),
    );
  }
}