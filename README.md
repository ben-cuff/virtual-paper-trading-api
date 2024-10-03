# virtual-paper-trading-api

API for virtual paper trading website

## Overview

This API allows users to simulate paper trading on a virtual platform. It is built using FastAPI, a modern, fast (high-performance), web framework for building APIs with Python. It uses PostgreSQL for its database and uses tables for storing user data, transactions, and portfolios.

## Features

- **User Authentication**: Secure user login and registration.
- **Portfolio Management**: Track and manage virtual portfolios.
- **Trade Execution**: Simulate buying and selling of stocks.
- **Performance Tracking**: Monitor the performance of virtual trades.

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/ben-cuff/virtual-paper-trading-api.git
    ```
2. Navigate to the project directory:
    ```bash
    cd virtual-paper-trading-api
    ```
3. Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1. Start the FastAPI server:
    ```bash
    uvicorn main:app --reload
    ```
2. Open your browser and navigate to `http://127.0.0.1:8000/docs` to access the interactive API documentation.

## License

This project is licensed under the MIT License.
