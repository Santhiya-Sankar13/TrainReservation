# 🚆 Train Ticket Reservation System

## 📌 Project Title
Advanced Train Ticket Reservation System with Segment-Based Seat Availability

## 📖 Project Description
The Train Ticket Reservation System is a web-based DBMS application developed using Python Flask and PostgreSQL.

It allows users to search trains, enter passenger details, select available seats, and confirm train ticket bookings.

## ⭐ Main Feature
The main feature of this project is **Segment-Based Seat Availability**.

Example route:

Chennai → Salem → Erode → Coimbatore

A seat booked from Chennai to Erode can be available for Erode to Coimbatore because the two journey segments do not overlap.

## 🛠 Technologies Used

- Python
- Flask
- PostgreSQL
- pgAdmin
- HTML
- CSS

## 🔄 System Flow

User
→ Web Interface
→ Flask Backend
→ PostgreSQL Database
→ Seat Availability Check
→ Seat Selection
→ Booking Confirmation
→ PNR Generation

## ✨ Features

- Train Search
- Source and Destination Selection
- Journey Date Selection
- Passenger Details
- Segment-Based Seat Availability
- Seat Selection
- PNR Generation
- Payment Record
- Booking Confirmation
- Cancellation Record

## 📂 Project Structure

```text
TrainReservation/
│
├── app.py
├── database.sql
├── requirements.txt
├── README.md
│
├── templates/
│   ├── index.html
│   ├── booking.html
│   └── seat_selection.html
│
└── static/
    └── style.css