# Bulq - Bulk Buying Organization Platform

A platform for organizing group purchases to reduce costs through bulk buying.

## Overview

Bulq enables friend groups to coordinate bulk purchases and track savings through organized group buying. The platform helps manage buying runs, calculate individual costs, and track purchase history across different stores.

## Tech Stack

- **Backend**: Python with FastAPI
- **Database**: PostgreSQL
- **Web Frontend**: React
- **Android App**: Native Kotlin

## Key Features

- Group buying run management
- Individual cost calculation and tracking
- Purchase history tracking
- Price comparison across stores
- Real-time order updates via WebSockets
- No in-app payments (manual settlement)

## Core Workflow

1. **Groups**: Users join friend groups for coordinated shopping
2. **Runs**: Groups create shopping runs targeting specific stores
3. **Bidding**: Users express interest and specify quantities for products
4. **Confirmation**: Products meeting thresholds are confirmed for purchase
5. **Shopping**: Designated group members execute the shopping list
6. **Settlement**: Costs calculated and settled manually among friends

## Architecture

- **Database Schema**: See [database_schema.md](database_schema.md) for detailed ER diagram
- **Monolithic Backend**: Single FastAPI application with PostgreSQL
- **Real-time Updates**: WebSocket connections for live bid tracking

## Target Users

Friend groups who trust each other and handle discussions/payments outside the app.

## Project Status

🚧 Project in initial planning phase