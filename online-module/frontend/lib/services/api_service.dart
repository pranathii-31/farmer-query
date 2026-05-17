import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import 'package:image_picker/image_picker.dart';

// ─────────────────────────────────────────────────────────────────────────────
//  Data models
// ─────────────────────────────────────────────────────────────────────────────

class WeatherInfo {
  final String summary;
  final double? temperature;
  final int? humidity;
  final String description;
  final double? windSpeed;
  final double? rainMm;
  final String farmingAdvice;
  final String source;

  const WeatherInfo({
    required this.summary,
    this.temperature,
    this.humidity,
    required this.description,
    this.windSpeed,
    this.rainMm,
    required this.farmingAdvice,
    required this.source,
  });

  factory WeatherInfo.fromJson(Map<String, dynamic> j) => WeatherInfo(
        summary:       (j['summary']        as String?) ?? '',
        temperature:   (j['temperature']    as num?)?.toDouble(),
        humidity:      (j['humidity']       as num?)?.toInt(),
        description:   (j['description']    as String?) ?? '',
        windSpeed:     (j['wind_speed']     as num?)?.toDouble(),
        rainMm:        (j['rain_mm']        as num?)?.toDouble(),
        farmingAdvice: (j['farming_advice'] as String?) ?? '',
        source:        (j['source']         as String?) ?? '',
      );
}

class Yojna {
  final String name;
  final String description;
  final String link;

  const Yojna({required this.name, required this.description, required this.link});

  factory Yojna.fromJson(Map<String, dynamic> j) => Yojna(
        name:        (j['name']        as String?) ?? '',
        description: (j['description'] as String?) ?? '',
        link:        (j['link']        as String?) ?? '',
      );

  bool get hasLink => link.isNotEmpty;
}

class NearbyCenter {
  final String name;
  final double distanceKm;
  final String address;

  const NearbyCenter({
    required this.name,
    required this.distanceKm,
    required this.address,
  });

  factory NearbyCenter.fromJson(Map<String, dynamic> j) => NearbyCenter(
        name:       (j['name']        as String?) ?? 'Unknown Centre',
        distanceKm: (j['distance_km'] as num?)?.toDouble() ?? 0.0,
        address:    (j['address']     as String?) ?? '',
      );
}

class AssistantResponse {
  final String aiResponse;
  final String? disease;
  final double? confidence;
  final String? treatment;
  final String? fertilizer;
  final String? prevention;
  final String? healthTips;
  final WeatherInfo? weather;
  final List<Yojna> yojnas;
  final List<NearbyCenter> nearbyCenters;
  final List<String> inputSummary;
  final String? error;
  final int statusCode;

  const AssistantResponse({
    required this.aiResponse,
    this.disease,
    this.confidence,
    this.treatment,
    this.fertilizer,
    this.prevention,
    this.healthTips,
    this.weather,
    this.yojnas = const [],
    this.nearbyCenters = const [],
    this.inputSummary = const [],
    this.error,
    this.statusCode = 200,
  });

  bool get isSuccess => error == null;
  bool get hasDisease =>
      disease != null && disease!.isNotEmpty && disease != 'Unable to detect disease';
  bool get hasWeather => weather != null;
  bool get hasYojnas  => yojnas.isNotEmpty;
  bool get hasCenters => nearbyCenters.isNotEmpty;

  factory AssistantResponse.fromJson(Map<String, dynamic> json) {
    final data     = json['data'] as Map<String, dynamic>? ?? {};
    final apiError = json['error'] as String?;

    final rawYojnas = data['yojnas'];
    final yojnas = (rawYojnas is List)
        ? rawYojnas.whereType<Map<String, dynamic>>().map(Yojna.fromJson).toList()
        : <Yojna>[];

    final rawCenters = data['nearby_centers'];
    final centers = (rawCenters is List)
        ? rawCenters
            .whereType<Map<String, dynamic>>()
            .map(NearbyCenter.fromJson)
            .toList()
        : <NearbyCenter>[];

    final rawWeather = data['weather'];
    final weather = (rawWeather is Map<String, dynamic>)
        ? WeatherInfo.fromJson(rawWeather)
        : null;

    final rawInputs = data['input_summary'];
    final inputs = (rawInputs is List)
        ? rawInputs.map((e) => e.toString()).toList()
        : <String>[];

    return AssistantResponse(
      aiResponse:    (data['ai_response']  as String?) ?? '',
      disease:       data['disease']       as String?,
      confidence:    (data['confidence']   as num?)?.toDouble(),
      treatment:     data['treatment']     as String?,
      fertilizer:    data['fertilizer']    as String?,
      prevention:    data['prevention']    as String?,
      healthTips:    data['health_tips']   as String?,
      weather:       weather,
      yojnas:        yojnas,
      nearbyCenters: centers,
      inputSummary:  inputs,
      error:         apiError,
      statusCode:    (json['status'] as num?)?.toInt() ?? 200,
    );
  }

  factory AssistantResponse.failure(String message, {int statusCode = 500}) =>
      AssistantResponse(
        aiResponse:  message,
        error:       message,
        statusCode:  statusCode,
      );
}

// Chat message model
class ChatMessage {
  final bool isUser;
  final String? text;
  final XFile? image;
  final Uint8List? imageBytes;   // web-safe: use Image.memory() with this
  final AssistantResponse? response;
  final DateTime timestamp;
  final bool isLoading;

  const ChatMessage({
    required this.isUser,
    this.text,
    this.image,
    this.imageBytes,
    this.response,
    required this.timestamp,
    this.isLoading = false,
  });

  ChatMessage copyWith({AssistantResponse? response, bool? isLoading}) =>
      ChatMessage(
        isUser:     isUser,
        text:       text,
        image:      image,
        imageBytes: imageBytes,
        response:   response ?? this.response,
        timestamp:  timestamp,
        isLoading:  isLoading ?? this.isLoading,
      );
}

// ─────────────────────────────────────────────────────────────────────────────
//  API Service
// ─────────────────────────────────────────────────────────────────────────────

class ApiService {
  /// Backend base URL.
  /// localhost:5000   → Flutter Web / desktop
  /// 10.0.2.2:5000    → Android emulator
  /// 192.168.x.x:5000 → Physical device on same LAN
  static const String backendUrl = 'http://localhost:5000';

  static MediaType _mimeType(String filename) {
    switch (filename.split('.').last.toLowerCase()) {
      case 'png':
        return MediaType('image', 'png');
      default:
        return MediaType('image', 'jpeg');
    }
  }

  /// Send a unified query to /assistant/query.
  static Future<AssistantResponse> sendQuery({
    String query = '',
    String history = '',
    XFile? imageFile,
    double? lat,
    double? lon,
    String? crop,
    String? state,
  }) async {
    if (query.isEmpty && imageFile == null && lat == null) {
      return AssistantResponse.failure(
        'Please enter a question, attach a crop photo, or share your location.',
        statusCode: 400,
      );
    }

    try {
      final uri     = Uri.parse('$backendUrl/assistant/query');
      final request = http.MultipartRequest('POST', uri);

      if (query.isNotEmpty)            request.fields['query'] = query;
      if (history.isNotEmpty)          request.fields['history'] = history;
      if (crop != null && crop.isNotEmpty)   request.fields['crop']  = crop;
      if (state != null && state.isNotEmpty) request.fields['state'] = state;
      if (lat != null && lon != null) {
        request.fields['lat'] = lat.toString();
        request.fields['lon'] = lon.toString();
      }

      if (imageFile != null) {
        final bytes = await imageFile.readAsBytes();
        request.files.add(
          http.MultipartFile.fromBytes(
            'image',
            bytes,
            filename:    imageFile.name,
            contentType: _mimeType(imageFile.name),
          ),
        );
      }

      final streamed  = await request.send();
      final response  = await http.Response.fromStream(streamed);

      late Map<String, dynamic> body;
      try {
        body = jsonDecode(response.body) as Map<String, dynamic>;
      } catch (_) {
        return AssistantResponse.failure(
          'Unexpected server response. Please retry.',
          statusCode: response.statusCode,
        );
      }

      if (response.statusCode == 200) return AssistantResponse.fromJson(body);

      final errMsg =
          (body['error'] as String?) ?? 'Server error (${response.statusCode})';
      return AssistantResponse.failure(errMsg, statusCode: response.statusCode);
    } on SocketException {
      return AssistantResponse.failure(
        'Cannot connect to the server. Is the backend running on $backendUrl?',
      );
    } catch (e) {
      return AssistantResponse.failure('Unexpected error: $e');
    }
  }
}
