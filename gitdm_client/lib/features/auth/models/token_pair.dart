/// \u0645\u062f\u0644 \u0633\u0627\u062f\u0647\u0654 \u062a\u0648\u06a9\u0646\u200c\u0647\u0627.
/// \u067e\u0627\u0633\u062e /api/token/ \u0645\u0639\u0645\u0648\u0644\u0627\u064b \u0634\u0627\u0645\u0644 access \u0648 refresh \u0627\u0633\u062a.
class TokenPair {
  final String access;
  final String refresh;

  TokenPair({required this.access, required this.refresh});

  factory TokenPair.fromJson(Map<String, dynamic> json) {
    return TokenPair(
      access: json['access'] as String? ?? '',
      refresh: json['refresh'] as String? ?? '',
    );
  }
}
