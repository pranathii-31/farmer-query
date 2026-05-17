import 'dart:typed_data';

import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:image_picker/image_picker.dart';
import 'package:url_launcher/url_launcher.dart';

import '../services/api_service.dart';
import 'dart:convert';

// ─────────────────────────────────────────────────────────────────────────────
//  Design tokens
// ─────────────────────────────────────────────────────────────────────────────

const _kGreen      = Color(0xFF2E7D32);
const _kDarkGreen  = Color(0xFF1B5E20);
const _kLightGreen = Color(0xFFE8F5E9);
const _kBg         = Color(0xFFF0F4F0);
const _kWhite      = Colors.white;

// ─────────────────────────────────────────────────────────────────────────────
//  Conversation model
// ─────────────────────────────────────────────────────────────────────────────

class Conversation {
  final List<ChatMessage> messages;
  final DateTime createdAt;
  String get title {
    final first = messages.firstWhere(
      (m) => m.isUser && (m.text?.isNotEmpty ?? false),
      orElse: () => messages.first,
    );
    final t = first.text ?? 'New conversation';
    return t.length > 36 ? t.substring(0, 36) + '…' : t;
  }

  Conversation({required this.messages, required this.createdAt});
}

// ─────────────────────────────────────────────────────────────────────────────
//  ChatScreen
// ─────────────────────────────────────────────────────────────────────────────

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});
  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final List<Conversation> _conversations = [];
  int _currentIdx = 0;

  final TextEditingController _input = TextEditingController();
  final ScrollController _scroll = ScrollController();
  final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>();

  XFile?     _pendingImg;
  Uint8List? _pendingBytes;
  Position?  _pos;
  bool       _locAttached  = false;
  bool       _locLoading   = false;
  bool       _sending      = false;
  bool       _schemesShown = false; // show scheme card only once per convo

  final _picker = ImagePicker();

  List<ChatMessage> get _msgs => _conversations[_currentIdx].messages;

  @override
  void initState() {
    super.initState();
    _startNewChat();
  }

  // ── Conversation management ──────────────────────────────────────────────────
  void _startNewChat() {
    final greet = ChatMessage(
      isUser:    false,
      text:      _greetText,
      timestamp: DateTime.now(),
    );
    setState(() {
      _conversations.add(Conversation(
        messages:  [greet],
        createdAt: DateTime.now(),
      ));
      _currentIdx  = _conversations.length - 1;
      _schemesShown = false;
      _locAttached  = false;
      _pos          = null;
      _pendingImg   = null;
      _pendingBytes = null;
    });
    WidgetsBinding.instance.addPostFrameCallback((_) => _scrollBottom());
  }

  void _switchConv(int idx) {
    setState(() {
      _currentIdx   = idx;
      _schemesShown = false;
    });
    Navigator.pop(context);
    WidgetsBinding.instance.addPostFrameCallback((_) => _scrollBottom());
  }

  static const _greetText =
      'Namaste! I\'m **KrishiMitra**, your AI farming assistant.\n\n'
      'Ask me anything about:\n'
      '• Crop diseases, pests & treatments\n'
      '• Fertilizer & irrigation guidance\n'
      '• Weather-based farming advice\n'
      '• Government schemes & subsidies\n'
      '• Crop selection for any region\n'
      '• Organic & sustainable farming\n\n'
      'You can also attach a **crop photo** for disease detection, or share your **location** for local advice.';

  // ── Image picker ─────────────────────────────────────────────────────────────
  Future<void> _pickImg(ImageSource src) async {
    if (Navigator.canPop(context)) Navigator.pop(context);
    final img = await _picker.pickImage(source: src, imageQuality: 85, maxWidth: 1200);
    if (img != null) {
      final bytes = await img.readAsBytes();
      setState(() { _pendingImg = img; _pendingBytes = bytes; });
    }
  }

  void _showImgSheet() => showModalBottomSheet(
        context: context,
        shape: const RoundedRectangleBorder(
            borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
        backgroundColor: _kWhite,
        builder: (_) => SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              Container(width: 40, height: 4,
                  decoration: BoxDecoration(color: Colors.grey[300],
                      borderRadius: BorderRadius.circular(2))),
              const SizedBox(height: 16),
              const Text('Attach Crop Photo',
                  style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
              const SizedBox(height: 8),
              _SheetTile(Icons.camera_alt, 'Take Photo', () => _pickImg(kIsWeb ? ImageSource.gallery : ImageSource.camera)),
              _SheetTile(Icons.photo_library_outlined, 'Choose from Gallery', () => _pickImg(ImageSource.gallery)),
            ]),
          ),
        ),
      );

  // ── Location ─────────────────────────────────────────────────────────────────
  Future<void> _toggleLoc() async {
    if (_locAttached) {
      setState(() { _locAttached = false; _pos = null; });
      return;
    }
    setState(() => _locLoading = true);
    try {
      if (!await Geolocator.isLocationServiceEnabled()) {
        _snack('Enable location services on your device/browser.'); return;
      }
      var perm = await Geolocator.checkPermission();
      if (perm == LocationPermission.denied) perm = await Geolocator.requestPermission();
      if (perm == LocationPermission.denied || perm == LocationPermission.deniedForever) {
        _snack('Location permission denied. Allow location in browser settings.'); return;
      }
      // Use low accuracy for much faster response on web
      final pos = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.low,
        timeLimit: const Duration(seconds: 10),
      );
      setState(() { _pos = pos; _locAttached = true; });
      _snack('Location attached ✓ (${pos.latitude.toStringAsFixed(2)}, ${pos.longitude.toStringAsFixed(2)})');
    } on TimeoutException {
      _snack('Location timed out. Try again or check browser permissions.');
    } catch (e) {
      _snack('Location error: $e');
    } finally {
      setState(() => _locLoading = false);
    }
  }

  // ── Send ─────────────────────────────────────────────────────────────────────
  Future<void> _send() async {
    final txt   = _input.text.trim();
    if (_sending) return;
    if (txt.isEmpty && _pendingImg == null && !_locAttached) {
      _snack('Type a message, attach a photo, or share location.'); return;
    }

    final sText  = txt;
    final sImg   = _pendingImg;
    final sBytes = _pendingBytes;
    final sPos   = _pos;
    final sLoc   = _locAttached;

    setState(() {
      _sending = true; _pendingImg = null; _pendingBytes = null;
      _input.clear();
    });

    final userMsg = ChatMessage(
      isUser: true, text: sText.isEmpty ? null : sText,
      image: sImg, imageBytes: sBytes, timestamp: DateTime.now(),
    );
    final loadMsg = ChatMessage(isUser: false, timestamp: DateTime.now(), isLoading: true);

    setState(() { _msgs.add(userMsg); _msgs.add(loadMsg); });
    _scrollBottom();

    // Prepare history: convert last 10 messages (excluding the loading bubble)
    final historyList = _msgs
        .where((m) => !m.isLoading && (m.text != null && m.text!.isNotEmpty))
        .take(10)
        .map((m) => {
              'role': m.isUser ? 'user' : 'bot',
              'text': m.text,
            })
        .toList();
    final String historyJson = jsonEncode(historyList);

    final resp = await ApiService.sendQuery(
      query: sText, imageFile: sImg, history: historyJson,
      lat: sLoc ? sPos?.latitude : null,
      lon: sLoc ? sPos?.longitude : null,
    );

    // Track if schemes were returned so we only show card once
    final hasSchemes = resp.hasYojnas;
    if (hasSchemes && _schemesShown) {
      // strip yojnas so UI doesn't show duplicate
    }

    setState(() {
      _sending = false;
      final idx = _msgs.lastIndexWhere((m) => m.isLoading);
      if (idx != -1) {
        _msgs[idx] = ChatMessage(
          isUser: false, text: resp.aiResponse,
          response: _schemesShown ? _stripYojnas(resp) : resp,
          timestamp: DateTime.now(),
        );
        if (hasSchemes) _schemesShown = true;
      }
    });
    _scrollBottom();
  }

  AssistantResponse _stripYojnas(AssistantResponse r) => AssistantResponse(
    aiResponse: r.aiResponse, disease: r.disease, confidence: r.confidence,
    treatment: r.treatment, fertilizer: r.fertilizer, prevention: r.prevention,
    healthTips: r.healthTips, weather: r.weather, yojnas: const [],
    nearbyCenters: r.nearbyCenters,
  );

  void _scrollBottom() => WidgetsBinding.instance.addPostFrameCallback((_) {
    if (_scroll.hasClients) {
      _scroll.animateTo(_scroll.position.maxScrollExtent,
          duration: const Duration(milliseconds: 350), curve: Curves.easeOut);
    }
  });

  void _snack(String msg) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: Text(msg), behavior: SnackBarBehavior.floating,
      backgroundColor: _kGreen,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
    ));
  }

  // ── Drawer ───────────────────────────────────────────────────────────────────
  Widget _buildDrawer() => Drawer(
        backgroundColor: _kWhite,
        child: Column(children: [
          Container(
            width: double.infinity,
            padding: const EdgeInsets.fromLTRB(20, 56, 20, 20),
            decoration: const BoxDecoration(color: _kDarkGreen),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Container(
                width: 52, height: 52,
                decoration: BoxDecoration(
                    color: _kWhite.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(14)),
                child: const Icon(Icons.agriculture, size: 30, color: _kWhite),
              ),
              const SizedBox(height: 12),
              const Text('KrishiMitra', style: TextStyle(color: _kWhite,
                  fontSize: 22, fontWeight: FontWeight.w800)),
              const Text('AI Farming Assistant',
                  style: TextStyle(color: Colors.white60, fontSize: 13)),
            ]),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            child: ElevatedButton.icon(
              onPressed: _startNewChat,
              icon: const Icon(Icons.add, size: 18),
              label: const Text('New Conversation'),
              style: ElevatedButton.styleFrom(
                backgroundColor: _kGreen, foregroundColor: _kWhite,
                minimumSize: const Size(double.infinity, 44),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
          ),
          const Divider(height: 1),
          Expanded(
            child: _conversations.isEmpty
                ? const Center(child: Text('No conversations yet'))
                : ListView.builder(
                    padding: const EdgeInsets.symmetric(vertical: 4),
                    itemCount: _conversations.length,
                    itemBuilder: (_, i) {
                      final conv = _conversations[i];
                      final active = i == _currentIdx;
                      return ListTile(
                        leading: CircleAvatar(
                          radius: 18,
                          backgroundColor: active ? _kGreen : const Color(0xFFE8F5E9),
                          child: Icon(Icons.chat_bubble_outline,
                              size: 16, color: active ? _kWhite : _kGreen),
                        ),
                        title: Text(conv.title,
                            style: TextStyle(fontSize: 13,
                                fontWeight: active ? FontWeight.w700 : FontWeight.normal),
                            maxLines: 1, overflow: TextOverflow.ellipsis),
                        subtitle: Text(_fmtDate(conv.createdAt),
                            style: TextStyle(fontSize: 11, color: Colors.grey[500])),
                        selected: active,
                        selectedTileColor: _kLightGreen,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        onTap: () => _switchConv(i),
                      );
                    },
                  ),
          ),
        ]),
      );

  // ── App bar ──────────────────────────────────────────────────────────────────
  PreferredSizeWidget _buildAppBar() => AppBar(
        key: _scaffoldKey,
        backgroundColor: _kDarkGreen,
        foregroundColor: _kWhite,
        elevation: 0,
        leading: Builder(builder: (ctx) => IconButton(
          icon: const Icon(Icons.menu),
          onPressed: () => Scaffold.of(ctx).openDrawer(),
        )),
        title: const Row(children: [
          Icon(Icons.agriculture, size: 22, color: _kWhite),
          SizedBox(width: 8),
          Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('KrishiMitra',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: _kWhite)),
            Text('AI Farming Assistant',
                style: TextStyle(fontSize: 10, color: Colors.white60, height: 1.2)),
          ]),
        ]),
        actions: [
          IconButton(
            icon: const Icon(Icons.add_comment_outlined),
            tooltip: 'New chat',
            onPressed: _startNewChat,
          ),
        ],
      );

  // ── Build ─────────────────────────────────────────────────────────────────────
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _kBg,
      appBar: _buildAppBar(),
      drawer: _buildDrawer(),
      body: Column(children: [
        Expanded(
          child: ListView.builder(
            controller: _scroll,
            padding: const EdgeInsets.fromLTRB(12, 12, 12, 8),
            itemCount: _msgs.length,
            itemBuilder: (_, i) => _Bubble(msg: _msgs[i]),
          ),
        ),
        _AttachBar(img: _pendingBytes, pos: _pos, locOn: _locAttached,
          onRemoveImg: () => setState(() { _pendingImg = null; _pendingBytes = null; }),
          onRemoveLoc: () => setState(() { _locAttached = false; _pos = null; }),
        ),
        _InputBar(
          controller: _input,
          sending: _sending,
          locLoading: _locLoading,
          locActive: _locAttached,
          imgActive: _pendingImg != null,
          onCamera: _showImgSheet,
          onLocation: _toggleLoc,
          onSend: _send,
        ),
      ]),
    );
  }

  @override
  void dispose() {
    _input.dispose();
    _scroll.dispose();
    super.dispose();
  }
}

// ─────────────────────────────────────────────────────────────────────────────
//  Sheet tile helper
// ─────────────────────────────────────────────────────────────────────────────

class _SheetTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;
  const _SheetTile(this.icon, this.label, this.onTap);
  @override
  Widget build(BuildContext context) => ListTile(
        leading: CircleAvatar(
          backgroundColor: _kLightGreen,
          child: Icon(icon, color: _kGreen, size: 20),
        ),
        title: Text(label, style: const TextStyle(fontWeight: FontWeight.w500)),
        onTap: onTap,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      );
}

// ─────────────────────────────────────────────────────────────────────────────
//  Attachment preview bar (above input)
// ─────────────────────────────────────────────────────────────────────────────

class _AttachBar extends StatelessWidget {
  final Uint8List? img;
  final Position? pos;
  final bool locOn;
  final VoidCallback onRemoveImg;
  final VoidCallback onRemoveLoc;
  const _AttachBar({required this.img, required this.pos, required this.locOn,
    required this.onRemoveImg, required this.onRemoveLoc});

  @override
  Widget build(BuildContext context) {
    if (img == null && !locOn) return const SizedBox.shrink();
    return Container(
      color: _kWhite,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      child: Row(children: [
        if (img != null)
          Stack(children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(10),
              child: Image.memory(img!, width: 54, height: 54, fit: BoxFit.cover),
            ),
            Positioned(top: -4, right: -4,
              child: GestureDetector(onTap: onRemoveImg,
                child: Container(
                  decoration: const BoxDecoration(color: _kWhite, shape: BoxShape.circle),
                  child: const Icon(Icons.cancel, size: 20, color: Colors.red),
                ))),
          ]),
        if (img != null) const SizedBox(width: 8),
        if (locOn)
          InputChip(
            avatar: const Icon(Icons.my_location, size: 14, color: _kGreen),
            label: Text(
              '${pos?.latitude.toStringAsFixed(3) ?? '—'}, ${pos?.longitude.toStringAsFixed(3) ?? '—'}',
              style: const TextStyle(fontSize: 11)),
            onDeleted: onRemoveLoc,
            backgroundColor: _kLightGreen,
            deleteIconColor: _kGreen,
            padding: EdgeInsets.zero,
          ),
      ]),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
//  Input bar
// ─────────────────────────────────────────────────────────────────────────────

class _InputBar extends StatelessWidget {
  final TextEditingController controller;
  final bool sending, locLoading, locActive, imgActive;
  final VoidCallback onCamera, onLocation, onSend;

  const _InputBar({
    required this.controller, required this.sending, required this.locLoading,
    required this.locActive, required this.imgActive,
    required this.onCamera, required this.onLocation, required this.onSend,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: _kWhite,
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.08),
            blurRadius: 12, offset: const Offset(0, -2))],
      ),
      padding: EdgeInsets.only(
        left: 8, right: 8, top: 8,
        bottom: MediaQuery.of(context).viewInsets.bottom + 10,
      ),
      child: Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
        _IconBtn(icon: Icons.camera_alt_outlined, active: imgActive,
            tooltip: 'Attach crop photo', onTap: onCamera),
        locLoading
            ? const Padding(padding: EdgeInsets.all(10),
                child: SizedBox(width: 20, height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2, color: _kGreen)))
            : _IconBtn(icon: Icons.my_location, active: locActive,
                tooltip: locActive ? 'Remove location' : 'Share location',
                onTap: onLocation),
        const SizedBox(width: 6),
        Expanded(
          child: TextField(
            controller: controller,
            keyboardType: TextInputType.multiline,
            maxLines: 5, minLines: 1,
            textCapitalization: TextCapitalization.sentences,
            decoration: InputDecoration(
              hintText: 'Ask anything about farming…',
              hintStyle: TextStyle(color: Colors.grey[400], fontSize: 14),
              filled: true, fillColor: _kBg,
              border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(24),
                  borderSide: BorderSide.none),
              contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            ),
            onSubmitted: (_) => onSend(),
          ),
        ),
        const SizedBox(width: 8),
        sending
            ? const Padding(padding: EdgeInsets.all(10),
                child: SizedBox(width: 24, height: 24,
                    child: CircularProgressIndicator(strokeWidth: 2.5, color: _kGreen)))
            : GestureDetector(
                onTap: onSend,
                child: Container(
                  width: 46, height: 46,
                  decoration: const BoxDecoration(color: _kGreen, shape: BoxShape.circle),
                  child: const Icon(Icons.send_rounded, color: _kWhite, size: 20),
                ),
              ),
      ]),
    );
  }
}

class _IconBtn extends StatelessWidget {
  final IconData icon;
  final bool active;
  final String tooltip;
  final VoidCallback onTap;
  const _IconBtn({required this.icon, required this.active,
      required this.tooltip, required this.onTap});

  @override
  Widget build(BuildContext context) => Tooltip(
        message: tooltip,
        child: GestureDetector(
          onTap: onTap,
          child: Container(
            width: 40, height: 40,
            margin: const EdgeInsets.only(bottom: 2),
            decoration: BoxDecoration(
              color: active ? _kGreen : _kLightGreen,
              shape: BoxShape.circle,
            ),
            child: Icon(icon, size: 20, color: active ? _kWhite : _kGreen),
          ),
        ),
      );
}

// ─────────────────────────────────────────────────────────────────────────────
//  Message bubble
// ─────────────────────────────────────────────────────────────────────────────

class _Bubble extends StatelessWidget {
  final ChatMessage msg;
  const _Bubble({required this.msg});

  @override
  Widget build(BuildContext context) {
    if (msg.isLoading) return _LoadingBubble();
    if (msg.isUser) return _UserBubble(msg: msg);
    return _BotBubble(msg: msg);
  }
}

// Loading
class _LoadingBubble extends StatelessWidget {
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 12),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          _Avatar(),
          const SizedBox(width: 8),
          Expanded(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
              decoration: BoxDecoration(
                color: _kWhite,
                borderRadius: const BorderRadius.only(
                    topRight: Radius.circular(18), bottomLeft: Radius.circular(18),
                    bottomRight: Radius.circular(18)),
                boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.06), blurRadius: 6)],
              ),
              child: Row(mainAxisSize: MainAxisSize.min, children: [
                const SizedBox(width: 18, height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2, color: _kGreen)),
                const SizedBox(width: 12),
                Text('KrishiMitra is thinking…',
                    style: TextStyle(color: Colors.grey[500], fontSize: 13)),
              ]),
            ),
          ),
          const SizedBox(width: 40),
        ]),
      );
}

// User bubble
class _UserBubble extends StatelessWidget {
  final ChatMessage msg;
  const _UserBubble({required this.msg});
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 12, left: 52),
        child: Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
          if (msg.imageBytes != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 4),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(14),
                child: Image.memory(msg.imageBytes!,
                    width: 220, height: 150, fit: BoxFit.cover),
              ),
            ),
          if (msg.text != null && msg.text!.isNotEmpty)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 11),
              decoration: const BoxDecoration(
                color: _kGreen,
                borderRadius: BorderRadius.only(
                  topLeft: Radius.circular(18), topRight: Radius.circular(4),
                  bottomLeft: Radius.circular(18), bottomRight: Radius.circular(18),
                ),
              ),
              child: Text(msg.text!,
                  style: const TextStyle(color: _kWhite, fontSize: 14.5, height: 1.45)),
            ),
          Padding(
            padding: const EdgeInsets.only(top: 3),
            child: Text(_fmtTime(msg.timestamp),
                style: TextStyle(fontSize: 10, color: Colors.grey[500])),
          ),
        ]),
      );
}

// Bot bubble — THIS IS THE MAIN, PROMINENT BOT MESSAGE
class _BotBubble extends StatelessWidget {
  final ChatMessage msg;
  const _BotBubble({required this.msg});

  @override
  Widget build(BuildContext context) {
    final resp = msg.response;
    return Padding(
      padding: const EdgeInsets.only(bottom: 16, right: 16),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        _Avatar(),
        const SizedBox(width: 8),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            // Bot name label
            Padding(
              padding: const EdgeInsets.only(bottom: 4, left: 2),
              child: Text('KrishiMitra',
                  style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700,
                      color: _kDarkGreen, letterSpacing: 0.3)),
            ),

            // Main text card — full width, prominent
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: _kWhite,
                borderRadius: const BorderRadius.only(
                  topRight: Radius.circular(18), bottomLeft: Radius.circular(18),
                  bottomRight: Radius.circular(18),
                ),
                border: const Border(left: BorderSide(color: _kGreen, width: 3)),
                boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.07),
                    blurRadius: 8, offset: const Offset(0, 2))],
              ),
              child: _RichText(text: msg.text ?? ''),
            ),

            // Disease card
            if (resp != null && resp.hasDisease)
              _DiseaseCard(r: resp),

            // Weather card
            if (resp != null && resp.hasWeather)
              _WeatherCard(w: resp.weather!),

            // Yojna card
            if (resp != null && resp.hasYojnas)
              _YojnaCard(yojnas: resp.yojnas),

            // Nearby centers
            if (resp != null && resp.hasCenters)
              _CenterCard(centers: resp.nearbyCenters),

            Padding(
              padding: const EdgeInsets.only(top: 4, left: 2),
              child: Text(_fmtTime(msg.timestamp),
                  style: TextStyle(fontSize: 10, color: Colors.grey[500])),
            ),
          ]),
        ),
      ]),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
//  Avatar widget
// ─────────────────────────────────────────────────────────────────────────────

class _Avatar extends StatelessWidget {
  @override
  Widget build(BuildContext context) => Container(
        width: 34, height: 34,
        decoration: const BoxDecoration(color: _kDarkGreen, shape: BoxShape.circle),
        child: const Icon(Icons.agriculture, size: 18, color: _kWhite),
      );
}

// ─────────────────────────────────────────────────────────────────────────────
//  Rich text renderer (bold** markers + bullets)
// ─────────────────────────────────────────────────────────────────────────────

class _RichText extends StatelessWidget {
  final String text;
  const _RichText({required this.text});

  @override
  Widget build(BuildContext context) {
    final lines = text.split('\n');
    return Column(crossAxisAlignment: CrossAxisAlignment.start,
        children: lines.asMap().entries.map((e) {
          final i = e.key;
          final line = e.value;
          Widget w;
          if (line.startsWith('• ') || line.startsWith('- ')) {
            w = Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text('• ', style: TextStyle(fontSize: 14, height: 1.5, color: _kGreen)),
              Expanded(child: _inline(line.length > 2 ? line.substring(2) : '')),
            ]);
          } else {
            final m = RegExp(r'^(\d+)\.\s').firstMatch(line);
            if (m != null) {
              w = Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('${m.group(1)}. ', style: const TextStyle(fontSize: 14, height: 1.5,
                    fontWeight: FontWeight.w700)),
                Expanded(child: _inline(line.substring(m.end))),
              ]);
            } else {
              w = _inline(line);
            }
          }
          return Padding(
            padding: EdgeInsets.only(top: i == 0 ? 0 : 2),
            child: w,
          );
        }).toList());
  }

  Widget _inline(String line) {
    final spans = <TextSpan>[];
    final pattern = RegExp(r'\*\*(.+?)\*\*');
    int last = 0;
    for (final m in pattern.allMatches(line)) {
      if (m.start > last) spans.add(TextSpan(
        text: line.substring(last, m.start),
        style: const TextStyle(fontSize: 14, height: 1.55, color: Colors.black87),
      ));
      spans.add(TextSpan(
        text: m.group(1),
        style: const TextStyle(fontSize: 14, height: 1.55,
            fontWeight: FontWeight.w700, color: Colors.black87),
      ));
      last = m.end;
    }
    if (last < line.length) spans.add(TextSpan(
      text: line.substring(last),
      style: const TextStyle(fontSize: 14, height: 1.55, color: Colors.black87),
    ));
    return Text.rich(TextSpan(children: spans));
  }
}

// ─────────────────────────────────────────────────────────────────────────────
//  Info section card (base)
// ─────────────────────────────────────────────────────────────────────────────

class _SecCard extends StatelessWidget {
  final IconData icon;
  final Color iconColor;
  final String title;
  final List<Widget> children;
  final Color? bg;
  const _SecCard({required this.icon, required this.iconColor,
      required this.title, required this.children, this.bg});

  @override
  Widget build(BuildContext context) => Container(
        margin: const EdgeInsets.only(top: 8),
        decoration: BoxDecoration(
          color: bg ?? _kWhite,
          borderRadius: BorderRadius.circular(14),
          border: Border(left: BorderSide(color: iconColor, width: 3)),
          boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 6)],
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 10, 12, 4),
            child: Row(children: [
              Icon(icon, size: 16, color: iconColor),
              const SizedBox(width: 6),
              Text(title, style: TextStyle(fontWeight: FontWeight.w700,
                  fontSize: 12.5, color: iconColor)),
            ]),
          ),
          const Divider(height: 1),
          Padding(padding: const EdgeInsets.all(12),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: children)),
        ]),
      );
}

// Disease card
class _DiseaseCard extends StatelessWidget {
  final AssistantResponse r;
  const _DiseaseCard({required this.r});
  @override
  Widget build(BuildContext context) {
    final conf = r.confidence;
    final confPct = conf != null ? '${(conf * 100).toStringAsFixed(1)}%' : null;
    final cc = (conf ?? 0) >= 0.7 ? Colors.red[700]! : (conf ?? 0) >= 0.4 ? Colors.orange[700]! : Colors.amber[700]!;
    return _SecCard(
      icon: Icons.bug_report_outlined, iconColor: Colors.red[700]!,
      title: 'Disease Analysis',
      children: [
        _Row2('Detected', r.disease ?? '—'),
        if (confPct != null) ...[
          const SizedBox(height: 4),
          Row(children: [
            SizedBox(width: 80, child: Text('Confidence:', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600))),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(confPct, style: TextStyle(color: cc, fontSize: 12, fontWeight: FontWeight.bold)),
              const SizedBox(height: 3),
              ClipRRect(borderRadius: BorderRadius.circular(4),
                child: LinearProgressIndicator(value: conf, color: cc,
                    backgroundColor: Colors.grey[200], minHeight: 5)),
            ])),
          ]),
        ],
        if (r.treatment != null) ...[
          const SizedBox(height: 8),
          _Block('Treatment', r.treatment!),
          if (r.fertilizer?.isNotEmpty ?? false) _Block('Fertilizer', r.fertilizer!),
          if (r.prevention?.isNotEmpty ?? false) _Block('Prevention', r.prevention!),
        ],
      ],
    );
  }
}

// Weather card
class _WeatherCard extends StatelessWidget {
  final WeatherInfo w;
  const _WeatherCard({required this.w});
  @override
  Widget build(BuildContext context) => _SecCard(
    icon: Icons.wb_sunny_outlined, iconColor: Colors.orange[700]!,
    title: 'Current Weather', bg: const Color(0xFFFFFDE7),
    children: [
      Wrap(spacing: 8, runSpacing: 6, children: [
        if (w.temperature != null) _WChip(Icons.thermostat, '${w.temperature!.toStringAsFixed(1)}°C', Colors.deepOrange),
        if (w.humidity != null) _WChip(Icons.water_drop_outlined, '${w.humidity}%', Colors.blue),
        if (w.windSpeed != null) _WChip(Icons.air, '${w.windSpeed!.toStringAsFixed(1)} m/s', Colors.teal),
        if (w.description.isNotEmpty) _WChip(Icons.cloud_outlined, w.description, Colors.blueGrey),
      ]),
      if (w.farmingAdvice.isNotEmpty) ...[
        const SizedBox(height: 8),
        Text(w.farmingAdvice, style: const TextStyle(fontSize: 12.5, height: 1.45)),
      ],
    ],
  );
}

class _WChip extends StatelessWidget {
  final IconData icon; final String label; final Color color;
  const _WChip(this.icon, this.label, this.color);
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
    decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withOpacity(0.3))),
    child: Row(mainAxisSize: MainAxisSize.min, children: [
      Icon(icon, size: 13, color: color),
      const SizedBox(width: 4),
      Text(label, style: TextStyle(fontSize: 11.5, color: color, fontWeight: FontWeight.w600)),
    ]),
  );
}

// Yojna card
class _YojnaCard extends StatelessWidget {
  final List<Yojna> yojnas;
  const _YojnaCard({required this.yojnas});
  @override
  Widget build(BuildContext context) => _SecCard(
    icon: Icons.account_balance_outlined, iconColor: Colors.blue[700]!,
    title: 'Applicable Government Schemes',
    children: yojnas.take(6).map((y) => _YojnaItem(y: y)).toList(),
  );
}

class _YojnaItem extends StatelessWidget {
  final Yojna y;
  const _YojnaItem({required this.y});
  Future<void> _open() async {
    final uri = Uri.tryParse(y.link);
    if (uri != null && await canLaunchUrl(uri)) await launchUrl(uri, mode: LaunchMode.externalApplication);
  }
  @override
  Widget build(BuildContext context) => Container(
    margin: const EdgeInsets.only(bottom: 6),
    padding: const EdgeInsets.all(9),
    decoration: BoxDecoration(color: Colors.blue[50], borderRadius: BorderRadius.circular(9),
        border: Border.all(color: Colors.blue[100]!)),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(y.name, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 12.5)),
      if (y.description.isNotEmpty) ...[
        const SizedBox(height: 2),
        Text(y.description, style: TextStyle(fontSize: 11.5, color: Colors.grey[700], height: 1.4)),
      ],
      if (y.hasLink) ...[
        const SizedBox(height: 5),
        GestureDetector(onTap: _open,
          child: Row(mainAxisSize: MainAxisSize.min, children: [
            Icon(Icons.open_in_new, size: 12, color: Colors.blue[700]),
            const SizedBox(width: 4),
            Text('Official Website', style: TextStyle(fontSize: 11.5, color: Colors.blue[700],
                decoration: TextDecoration.underline)),
          ])),
      ],
    ]),
  );
}

// Center card
class _CenterCard extends StatelessWidget {
  final List<NearbyCenter> centers;
  const _CenterCard({required this.centers});
  @override
  Widget build(BuildContext context) => _SecCard(
    icon: Icons.location_on_outlined, iconColor: Colors.teal[700]!,
    title: 'Nearby Krishi Vigyan Kendras',
    children: centers.take(5).map((c) => Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(children: [
        Icon(Icons.store_outlined, size: 14, color: Colors.teal[600]),
        const SizedBox(width: 6),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(c.name, style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w600)),
          if (c.address.isNotEmpty) Text(c.address,
              style: TextStyle(fontSize: 11, color: Colors.grey[600])),
        ])),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
          decoration: BoxDecoration(color: Colors.teal[50], borderRadius: BorderRadius.circular(8),
              border: Border.all(color: Colors.teal[200]!)),
          child: Text('${c.distanceKm.toStringAsFixed(1)} km',
              style: TextStyle(fontSize: 11, color: Colors.teal[700], fontWeight: FontWeight.w600)),
        ),
      ]),
    )).toList(),
  );
}

// ─────────────────────────────────────────────────────────────────────────────
//  Helper widgets
// ─────────────────────────────────────────────────────────────────────────────

class _Row2 extends StatelessWidget {
  final String label, value;
  const _Row2(this.label, this.value);
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 4),
    child: Row(children: [
      SizedBox(width: 78, child: Text('$label:', style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 12.5))),
      Expanded(child: Text(value, style: const TextStyle(fontSize: 12.5))),
    ]),
  );
}

class _Block extends StatelessWidget {
  final String label, value;
  const _Block(this.label, this.value);
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 6),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(label, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 12.5)),
      const SizedBox(height: 2),
      Text(value, style: const TextStyle(fontSize: 12.5, height: 1.5)),
    ]),
  );
}

// ─────────────────────────────────────────────────────────────────────────────
//  Utility
// ─────────────────────────────────────────────────────────────────────────────

String _fmtTime(DateTime d) {
  final h = d.hour > 12 ? d.hour - 12 : (d.hour == 0 ? 12 : d.hour);
  return '$h:${d.minute.toString().padLeft(2, '0')} ${d.hour >= 12 ? 'PM' : 'AM'}';
}

String _fmtDate(DateTime d) {
  final months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  return '${d.day} ${months[d.month - 1]}, ${_fmtTime(d)}';
}

// Placeholder to satisfy Dart analysis (geolocator TimeoutException)
class TimeoutException implements Exception {
  final String message;
  const TimeoutException(this.message);
}
