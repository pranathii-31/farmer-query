import 'package:flutter/material.dart';
import 'package:farmer_query_frontend/screens/home_screen.dart';

void main() {
  runApp(const FarmerQueryApp());
}

class FarmerQueryApp extends StatelessWidget {
  const FarmerQueryApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Farmer Query Frontend',
      theme: ThemeData(
        primarySwatch: Colors.green,
      ),
      home: const HomeScreen(),
    );
  }
}
