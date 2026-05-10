# Farmer Query Frontend

This is a Flutter frontend for the Farmer Query Engine backend.

## Features
- Select a crop image from gallery
- Enter crop name
- Optional: Use current location for nearby centers
- Submit to backend `/full-recommendation`
- Display the JSON response from the server

## Setup
1. Install Flutter: https://flutter.dev/docs/get-started/install
2. Open this folder in your editor
3. Run `flutter pub get` to install dependencies
4. For Android: Ensure you have Android SDK and emulator/device set up
5. For iOS: Ensure you have Xcode and iOS simulator/device set up
6. Run on a device or emulator with `flutter run`

## Requirements Added
- `http: ^0.13.6` - For API calls
- `image_picker: ^0.8.7+5` - For image selection
- `geolocator: ^9.0.2` - For current location
- Android permissions: INTERNET, ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION (in android/app/src/main/AndroidManifest.xml)
- iOS permissions: Add to ios/Runner/Info.plist:
  ```xml
  <key>NSLocationWhenInUseUsageDescription</key>
  <string>This app needs location access to find nearby agricultural centers.</string>
  <key>NSPhotoLibraryUsageDescription</key>
  <string>This app needs photo library access to select crop images.</string>
  ```

## Backend requirements
- Backend must be running at `http://127.0.0.1:5000`
- The `/full-recommendation` endpoint accepts optional lat/lon

## Testing Steps
1. Start the backend: `cd farmer_query_engine/backend && python app.py`
2. Run the Flutter app: `flutter run`
3. Select an image, enter crop name (e.g., "wheat"), optionally enable location
4. Tap "Get Recommendation" and verify JSON response

## Notes
- Location is optional; if not enabled, nearby centers won't be returned but other recommendations will work
- The UI currently shows raw JSON; you can enhance it later for better display
