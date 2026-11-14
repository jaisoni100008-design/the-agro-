# 🚀 ML Web Application: Streamlit & Flask Decoupled Architecture

A production-ready, decoupled Machine Learning web application built for scalability and ease of maintenance. This project separates the User Interface (Frontend) from the Machine Learning Inference Engine (Backend) to ensure optimal performance and resource management.

## 📖 Overview
This application allows users to input text and receive real-time predictions using a pre-trained Machine Learning model. By decoupling the frontend and backend, the ML model is loaded into memory only once on the backend server, preventing memory bloat and ensuring fast inference times for multiple concurrent users.

## 🏗️ Architecture
The project follows a decoupled microservices-like architecture:
