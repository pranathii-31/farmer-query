import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:geolocator/geolocator.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:farmer_query_frontend/services/api_service.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  // ── Form ────────────────────────────────────────────────────────────────
  final _formKey = GlobalKey<FormState>();
  final _cropController  = TextEditingController();
  final _stateController = TextEditingController();

  // ── Image ────────────────────────────────────────────────────────────────
  XFile? _selectedImage;

  // ── Location ─────────────────────────────────────────────────────────────
  bool      _useLocation     = false;
  Position? _currentPosition;
  bool      _locationLoading = false;

  // ── Result ───────────────────────────────────────────────────────────────
  RecommendationResult? _result;
  bool _isLoading = false;

  @override
  void dispose() {
    _cropController.dispose();
    _stateController.dispose();
    super.dispose();
  }

  // ── Image picker ─────────────────────────────────────────────────────────
  Future<void> _pickImage() async {
    final picker = ImagePicker();
    final image  = await picker.pickImage(source: ImageSource.gallery);
    if (image != null) {
      setState(() { _selectedImage = image; _result = null; });
    }
  }

  // ── Location ─────────────────────────────────────────────────────────────
  Future<void> _fetchLocation() async {
    setState(() => _locationLoading = true);

    if (!await Geolocator.isLocationServiceEnabled()) {
      _showSnack('Location services are disabled.');
      setState(() => _locationLoading = false);
      return;
    }

    var permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }
    if (permission == LocationPermission.denied ||
        permission == LocationPermission.deniedForever) {
      _showSnack('Location permission denied.');
      setState(() => _locationLoading = false);
      return;
    }

    final pos = await Geolocator.getCurrentPosition();
    setState(() { _currentPosition = pos; _locationLoading = false; });
  }

  void _showSnack(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(msg), behavior: SnackBarBehavior.floating),
    );
  }

  // ── Submit ────────────────────────────────────────────────────────────────
  Future<void> _submit() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    if (_selectedImage == null) {
      _showSnack('Please select a crop image first.');
      return;
    }

    setState(() { _isLoading = true; _result = null; });

    double? lat, lon;
    if (_useLocation && _currentPosition != null) {
      lat = _currentPosition!.latitude;
      lon = _currentPosition!.longitude;
    }

    final result = await ApiService.submitFullRecommendation(
      imageFile: _selectedImage!,
      crop:  _cropController.text.trim(),
      state: _stateController.text.trim().isEmpty
          ? null
          : _stateController.text.trim(),
      lat: lat,
      lon: lon,
    );

    setState(() { _isLoading = false; _result = result; });
  }

  // ── Build ─────────────────────────────────────────────────────────────────
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Farmer Query Engine'),
        backgroundColor: Colors.green[700],
        foregroundColor: Colors.white,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _ImagePickerCard(selectedImage: _selectedImage, onPick: _pickImage),
            const SizedBox(height: 16),

            Form(
              key: _formKey,
              child: Column(children: [
                TextFormField(
                  controller: _cropController,
                  decoration: const InputDecoration(
                    labelText: 'Crop Name *',
                    hintText: 'e.g. wheat, pumpkin, tomato',
                    border: OutlineInputBorder(),
                    prefixIcon: Icon(Icons.grass),
                  ),
                  textInputAction: TextInputAction.next,
                  validator: validateCropName,
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _stateController,
                  decoration: const InputDecoration(
                    labelText: 'State (optional)',
                    hintText: 'e.g. Karnataka, Punjab',
                    border: OutlineInputBorder(),
                    prefixIcon: Icon(Icons.map_outlined),
                  ),
                  textInputAction: TextInputAction.done,
                  validator: validateStateName,
                ),
              ]),
            ),
            const SizedBox(height: 12),

            _LocationRow(
              useLocation:     _useLocation,
              locationLoading: _locationLoading,
              position:        _currentPosition,
              onChanged: (val) {
                setState(() { _useLocation = val; _result = null; });
                if (val) _fetchLocation();
              },
            ),
            const SizedBox(height: 20),

            ElevatedButton.icon(
              onPressed: _isLoading ? null : _submit,
              icon: _isLoading
                  ? const SizedBox(
                      width: 18, height: 18,
                      child: CircularProgressIndicator(
                          color: Colors.white, strokeWidth: 2))
                  : const Icon(Icons.search),
              label: Text(_isLoading ? 'Analysing…' : 'Get Recommendation'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.green[700],
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 14),
                textStyle: const TextStyle(fontSize: 16),
              ),
            ),
            const SizedBox(height: 24),

            if (_result != null) _ResultPanel(result: _result!),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
//  Sub-widgets
// ─────────────────────────────────────────────────────────────────────────────

class _ImagePickerCard extends StatelessWidget {
  final XFile?      selectedImage;
  final VoidCallback onPick;
  const _ImagePickerCard({required this.selectedImage, required this.onPick});

  @override
  Widget build(BuildContext context) => Card(
        child: ListTile(
          leading: const Icon(Icons.photo_library, color: Colors.green),
          title: Text(
            selectedImage == null ? 'No image selected' : selectedImage!.name,
            overflow: TextOverflow.ellipsis,
          ),
          subtitle: selectedImage == null
              ? const Text('Tap to choose a crop photo')
              : null,
          trailing: TextButton(
            onPressed: onPick,
            child: Text(selectedImage == null ? 'Select' : 'Change'),
          ),
        ),
      );
}

class _LocationRow extends StatelessWidget {
  final bool        useLocation;
  final bool        locationLoading;
  final Position?   position;
  final ValueChanged<bool> onChanged;
  const _LocationRow({
    required this.useLocation,
    required this.locationLoading,
    required this.position,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: [
            Switch(
              value: useLocation,
              activeColor: Colors.green[700],
              onChanged: onChanged,
            ),
            const SizedBox(width: 8),
            const Text('Include my location'),
            if (locationLoading) ...[
              const SizedBox(width: 8),
              const SizedBox(
                width: 14, height: 14,
                child: CircularProgressIndicator(strokeWidth: 2),
              ),
            ],
          ]),
          if (useLocation && position != null)
            Padding(
              padding: const EdgeInsets.only(left: 16),
              child: Text(
                'Lat ${position!.latitude.toStringAsFixed(4)}, '
                'Lon ${position!.longitude.toStringAsFixed(4)}',
                style: TextStyle(fontSize: 12, color: Colors.grey[600]),
              ),
            ),
        ],
      );
}

// ── Results panel ─────────────────────────────────────────────────────────────

class _ResultPanel extends StatelessWidget {
  final RecommendationResult result;
  const _ResultPanel({required this.result});

  @override
  Widget build(BuildContext context) {
    if (!result.isSuccess) {
      return _ErrorBanner(message: result.error ?? 'Unknown error');
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // Disease detection
        _InfoCard(
          icon: Icons.bug_report,
          iconColor: Colors.red[700]!,
          title: 'Disease Detected',
          children: [
            _Row('Disease', result.disease ?? '—'),
            _Row(
              'Confidence',
              result.confidence != null
                  ? '${(result.confidence! * 100).toStringAsFixed(1)} %'
                  : '—',
            ),
          ],
        ),
        const SizedBox(height: 12),

        // Treatment advice
        _InfoCard(
          icon: Icons.medical_services_outlined,
          iconColor: Colors.orange[700]!,
          title: 'Treatment Advice',
          children: [
            _Block('Treatment',  result.treatment),
            _Block('Fertilizer', result.fertilizer),
            _Block('Prevention', result.prevention),
          ],
        ),
        const SizedBox(height: 12),

        // Health tips
        if (result.healthTips != null && result.healthTips!.isNotEmpty) ...[
          _InfoCard(
            icon: Icons.health_and_safety_outlined,
            iconColor: Colors.green[700]!,
            title: 'Crop Health Tips',
            children: [
              Text(result.healthTips!,
                  style: const TextStyle(fontSize: 13, height: 1.5)),
            ],
          ),
          const SizedBox(height: 12),
        ],

        // Government schemes — each with name, description, link
        _InfoCard(
          icon: Icons.account_balance_outlined,
          iconColor: Colors.blue[700]!,
          title: 'Applicable Government Schemes',
          children: result.yojnas.isEmpty
              ? [const Text('No schemes found for this crop / state.',
                    style: TextStyle(fontSize: 13))]
              : result.yojnas.map((y) => _YojnaItem(yojna: y)).toList(),
        ),
        const SizedBox(height: 12),

        // Nearby centres
        if (result.nearbyCenters.isNotEmpty) ...[
          _InfoCard(
            icon: Icons.location_on_outlined,
            iconColor: Colors.teal[700]!,
            title: 'Nearby Krishi Centers',
            children: result.nearbyCenters.map((c) => Padding(
              padding: const EdgeInsets.symmetric(vertical: 3),
              child: Row(children: [
                const Icon(Icons.store_outlined, size: 14, color: Colors.teal),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    '${c.name}  —  ${c.distanceKm.toStringAsFixed(1)} km',
                    style: const TextStyle(fontSize: 13),
                  ),
                ),
              ]),
            )).toList(),
          ),
          const SizedBox(height: 12),
        ],
      ],
    );
  }
}

// ── Yojna item ────────────────────────────────────────────────────────────────

class _YojnaItem extends StatelessWidget {
  final Yojna yojna;
  const _YojnaItem({required this.yojna});

  Future<void> _openLink(BuildContext context) async {
    final uri = Uri.tryParse(yojna.link);
    if (uri == null) return;
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    } else {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Could not open the link.')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: Colors.blue[50],
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.blue[100]!),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Scheme name
          Text(
            yojna.name,
            style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13),
          ),
          // Description
          if (yojna.description.isNotEmpty) ...[
            const SizedBox(height: 4),
            Text(
              yojna.description,
              style: TextStyle(fontSize: 12, color: Colors.grey[700], height: 1.4),
            ),
          ],
          // Link button
          if (yojna.hasLink) ...[
            const SizedBox(height: 6),
            GestureDetector(
              onTap: () => _openLink(context),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.open_in_new, size: 14, color: Colors.blue[700]),
                  const SizedBox(width: 4),
                  Text(
                    'Official Website',
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.blue[700],
                      decoration: TextDecoration.underline,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}

// ── Shared small widgets ──────────────────────────────────────────────────────

class _InfoCard extends StatelessWidget {
  final IconData     icon;
  final Color        iconColor;
  final String       title;
  final List<Widget> children;
  const _InfoCard({
    required this.icon,
    required this.iconColor,
    required this.title,
    required this.children,
  });

  @override
  Widget build(BuildContext context) => Card(
        elevation: 2,
        shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10)),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(children: [
                Icon(icon, color: iconColor, size: 20),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(title,
                      style: const TextStyle(
                          fontWeight: FontWeight.bold, fontSize: 15)),
                ),
              ]),
              const Divider(height: 16),
              ...children,
            ],
          ),
        ),
      );
}

class _Row extends StatelessWidget {
  final String label;
  final String value;
  const _Row(this.label, this.value);

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 4),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SizedBox(
              width: 100,
              child: Text('$label:',
                  style: const TextStyle(
                      fontWeight: FontWeight.w600, fontSize: 13)),
            ),
            Expanded(
                child: Text(value, style: const TextStyle(fontSize: 13))),
          ],
        ),
      );
}

class _Block extends StatelessWidget {
  final String  label;
  final String? value;
  const _Block(this.label, this.value);

  @override
  Widget build(BuildContext context) {
    if (value == null || value!.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('$label:',
              style: const TextStyle(
                  fontWeight: FontWeight.w600, fontSize: 13)),
          const SizedBox(height: 2),
          Text(value!,
              style: const TextStyle(fontSize: 13, height: 1.5)),
        ],
      ),
    );
  }
}

class _ErrorBanner extends StatelessWidget {
  final String message;
  const _ErrorBanner({required this.message});

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.red[50],
          border: Border.all(color: Colors.red[200]!),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.error_outline, color: Colors.red[700], size: 20),
            const SizedBox(width: 10),
            Expanded(
              child: Text(message,
                  style: TextStyle(
                      color: Colors.red[800], fontSize: 13)),
            ),
          ],
        ),
      );
}
