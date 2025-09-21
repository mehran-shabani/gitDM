import 'package:meta/meta.dart';

/// مدل ساده‌ی توکن‌ها.
/// پاسخ /api/token/ معمولاً شامل access و refresh است.
/// Example:
/// { "access": "eyJhbGciOi...", "refresh": "eyJhbGciOi..." }
@immutable
class TokenPair {
  final String access;
  final String refresh;

  const TokenPair({required this.access, required this.refresh});

  factory TokenPair.fromJson(Map<String, dynamic> json) {
    return TokenPair(
      access: json['access'] as String? ?? '',
      refresh: json['refresh'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
    'access': access,
    'refresh': refresh,
  };

  TokenPair copyWith({String? access, String? refresh}) =>
      TokenPair(access: access ?? this.access, refresh: refresh ?? this.refresh);

  bool get isComplete => access.isNotEmpty && refresh.isNotEmpty;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is TokenPair &&
          runtimeType == other.runtimeType &&
          access == other.access &&
          refresh == other.refresh;

  @override
  int get hashCode => Object.hash(access, refresh);
}