import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import 'package:image_picker/image_picker.dart';

// ──────────────────────────────────────────────────────────────────────────────
//  Typed response models
// ──────────────────────────────────────────────────────────────────────────────

class NearbyCenter {
  final String name;
  final double distanceKm;

  const NearbyCenter({required this.name, required this.distanceKm});

  factory NearbyCenter.fromJson(Map<String, dynamic> json) => NearbyCenter(
        name: (json['name'] as String?) ?? 'Unknown',
        distanceKm: (json['distance_km'] as num?)?.toDouble() ?? 0.0,
      );
}

/// A government scheme (yojna) with name, description and official link.
class Yojna {
  final String name;
  final String description;
  final String link; // official scheme URL (may be empty string if not available)

  const Yojna({
    required this.name,
    required this.description,
    required this.link,
  });

  factory Yojna.fromJson(Map<String, dynamic> json) => Yojna(
        name:        (json['name']        as String?) ?? '',
        description: (json['description'] as String?) ?? '',
        link:        (json['link']        as String?) ?? '',
      );

  bool get hasLink => link.isNotEmpty;
}

/// Result returned by [ApiService.submitFullRecommendation].
/// On success [error] is null; on failure [error] carries the message.
class RecommendationResult {
  // ── Disease info ──────────────────────────────
  final String? disease;
  final double? confidence;

  // ── Advice ────────────────────────────────────
  final String? treatment;
  final String? fertilizer;
  final String? prevention;

  // ── Extra info ────────────────────────────────
  final String? healthTips;
  final List<Yojna> yojnas;
  final List<NearbyCenter> nearbyCenters;

  // ── Error / meta ──────────────────────────────
  final String? error;
  final int statusCode;

  const RecommendationResult({
    this.disease,
    this.confidence,
    this.treatment,
    this.fertilizer,
    this.prevention,
    this.healthTips,
    this.yojnas = const [],
    this.nearbyCenters = const [],
    this.error,
    this.statusCode = 200,
  });

  bool get isSuccess => error == null;

  factory RecommendationResult.fromJson(Map<String, dynamic> json) {
    final data     = json['data'] as Map<String, dynamic>? ?? {};
    final apiError = json['error'] as String?;

    // yojna is now always a List<Map> from the backend
    final rawYojna = data['yojna'];
    final List<Yojna> yojnas;
    if (rawYojna is List) {
      yojnas = rawYojna
          .whereType<Map<String, dynamic>>()
          .map(Yojna.fromJson)
          .toList();
    } else {
      yojnas = [];
    }

    final rawCenters = data['nearby_centers'];
    final List<NearbyCenter> centers;
    if (rawCenters is List) {
      centers = rawCenters
          .whereType<Map<String, dynamic>>()
          .map(NearbyCenter.fromJson)
          .toList();
    } else {
      centers = [];
    }

    return RecommendationResult(
      disease:       data['disease']    as String?,
      confidence:    (data['confidence'] as num?)?.toDouble(),
      treatment:     data['treatment']  as String?,
      fertilizer:    data['fertilizer'] as String?,
      prevention:    data['prevention'] as String?,
      healthTips:    data['health_tips'] as String?,
      yojnas:        yojnas,
      nearbyCenters: centers,
      error:         apiError,
      statusCode:    (json['status'] as num?)?.toInt() ?? 200,
    );
  }

  factory RecommendationResult.failure(String message,
          {int statusCode = 500}) =>
      RecommendationResult(error: message, statusCode: statusCode);
}

// ──────────────────────────────────────────────────────────────────────────────
//  Input-validation helpers (client-side)
// ──────────────────────────────────────────────────────────────────────────────

String? validateCropName(String? value) {
  if (value == null || value.trim().isEmpty) {
    return 'Crop name is required.';
  }
  final trimmed = value.trim();
  if (trimmed.length < 2) return 'Crop name must be at least 2 characters.';
  if (trimmed.length > 60) return 'Crop name is too long (max 60 characters).';
  if (!RegExp(r'^[a-zA-Z\s\-]+$').hasMatch(trimmed)) {
    return 'Crop name may only contain letters, spaces or hyphens.';
  }
  return null;
}

String? validateStateName(String? value) {
  if (value == null || value.trim().isEmpty) return null; // optional
  final trimmed = value.trim();
  if (trimmed.length > 60) return 'State name is too long.';
  if (!RegExp(r'^[a-zA-Z\s\-]+$').hasMatch(trimmed)) {
    return 'State name may only contain letters, spaces or hyphens.';
  }
  return null;
}

// ──────────────────────────────────────────────────────────────────────────────
//  API service
// ──────────────────────────────────────────────────────────────────────────────

class ApiService {
  // ── Base URL ──────────────────────────────────────────────────────────────
  // localhost:5000   → Flutter Web (Chrome)
  // 10.0.2.2:5000    → Android emulator
  // 192.168.x.x:5000 → physical device on the same LAN
  static const String backendUrl = 'http://localhost:5000';

  static MediaType _mediaMime(String filename) {
    switch (filename.split('.').last.toLowerCase()) {
      case 'png':
        return MediaType('image', 'png');
      case 'jpg':
      case 'jpeg':
      default:
        return MediaType('image', 'jpeg');
    }
  }

  /// Submit a full crop-recommendation request.
  /// Always returns a [RecommendationResult] — check [isSuccess] for outcome.
  static Future<RecommendationResult> submitFullRecommendation({
    required XFile imageFile,
    required String crop,
    String? state,
    double? lat,
    double? lon,
  }) async {
    // Client-side validation
    final cropError  = validateCropName(crop);
    if (cropError  != null) return RecommendationResult.failure(cropError,  statusCode: 400);
    final stateError = validateStateName(state);
    if (stateError != null) return RecommendationResult.failure(stateError, statusCode: 400);

    try {
      final uri     = Uri.parse('$backendUrl/full-recommendation');
      final request = http.MultipartRequest('POST', uri);

      request.fields['crop'] = crop.trim();
      if (state != null && state.trim().isNotEmpty) {
        request.fields['state'] = state.trim();
      }
      if (lat != null && lon != null) {
        request.fields['lat'] = lat.toString();
        request.fields['lon'] = lon.toString();
      }

      final bytes = await imageFile.readAsBytes();
      request.files.add(
        http.MultipartFile.fromBytes(
          'image',
          bytes,
          filename: imageFile.name,
          contentType: _mediaMime(imageFile.name),
        ),
      );

      final streamedResponse = await request.send();
      final response         = await http.Response.fromStream(streamedResponse);

      final Map<String, dynamic> body;
      try {
        body = jsonDecode(response.body) as Map<String, dynamic>;
      } catch (_) {
        return RecommendationResult.failure(
          'Unexpected server response (non-JSON).',
          statusCode: response.statusCode,
        );
      }

      if (response.statusCode == 200) return RecommendationResult.fromJson(body);

      final errMsg = (body['error'] as String?) ??
          'Server error (HTTP ${response.statusCode})';
      return RecommendationResult.failure(errMsg, statusCode: response.statusCode);
    } on SocketException {
      return RecommendationResult.failure(
          'Cannot reach the backend. Is it running on $backendUrl?');
    } on HttpException catch (e) {
      return RecommendationResult.failure('HTTP error: $e');
    } catch (e) {
      return RecommendationResult.failure('Unexpected error: $e');
    }
  }
}
