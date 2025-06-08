# RKC-FB-series-controller-python, a Python Library for FB100/400/900 Controllers

This Python library facilitates communication with the FB100/400/900 controllers using the RKC protocol over serial communication. It implements polling/selecting methods as defined in the ANSI X3.28-1976 standard, allowing for reading and writing data between a host computer and the controller.

## Features
- Polling data from the controller (e.g., Measured Value (M1))
- Setting values on the controller (e.g., Setpoint Value (S1))
- Block Check Character (BCC) validation for data integrity
- Handles communication control characters like STX, ETX, ACK, NAK, and EOT

For the details of RKC protocol related to FB series controller, refer to [RKC_protocol](RKC_protocol.md).


## Usage Example
``` python
from fb_controller.rkc_communication import RKCCommunication

# Automatically manage the opening and closing of the communication
with RKCCommunication(port="COM3", baudrate=19200, address="01") as comm:
    # Read process value (PV) using M1 command
    current_value = comm.read_value()
    if current_value is not None:
        print(f"Current Process Value (PV): {current_value}")

    # Set a new value for Set Value (SV) using S1 command
    new_value = 120.0  # Set new value as 120.0
    comm.set_value(new_value)
```

## Installation

```
pip install -e .
```

## API Usage

This project also provides a FastAPI application to expose the RKC controller functionality via a REST API.

### Running the API Server

To start the API server, navigate to the project root and run:

```bash
python -m src.rkc_controller_api.main
```
The API will be available at `http://localhost:8000` by default. You can access the interactive API documentation at `http://localhost:8000/docs`.

### API Endpoints

#### 1. Set Temperature

Sets the target temperature (Setpoint Value - SV) on the RKC controller.

- **URL:** `/controller/set_temperature`
- **Method:** `POST`
- **Request Body:**
```json
{
  "temperature": 10
}
```
- **Example using curl:**
```bash
curl -X POST "http://localhost:8000/controller/set_temperature" -H "Content-Type: application/json" -d '{"temperature": 150.5}'
```

#### 2. Get Controller Status

Gets the current status (current_temperature, target_temperature, output_value) from the RKC controller.

- **URL:** `/controller/status`
- **Method:** `GET`
- **Example using curl:**
```bash
curl -X GET "http://localhost:8000/controller/status"
```

#### 3. Get History Data

Retrieves historical logged data from the controller. This endpoint allows for flexible querying of records based on timestamp ranges and the number of entries.

- **URL:** `/controller/history`
- **Method:** `GET`
- **Query Parameters:**
  - `lines` (optional): An integer specifying the maximum number of historical records to return. If set to 0 or a negative value, all available records within the specified timestamp range (if any) will be returned.
    - Example: `?lines=10` (returns the last 10 records)
  - `from` (optional): An ISO 8601 formatted timestamp (`YYYY-MM-DDTHH:MM:SSZ`) to filter records that occurred on or after this time.
    - Example: `?from=2025-01-01T10:00:00Z` (records from January 1, 2025, 10:00:00 UTC onwards)
  - `to` (optional): An ISO 8601 formatted timestamp (`YYYY-MM-DDTHH:MM:SSZ`) to filter records that occurred on or before this time.
    - Example: `?to=2025-01-01T11:00:00Z` (records up to January 1, 2025, 11:00:00 UTC)

- **Response Format:**
  The endpoint returns a JSON array of historical data entries. Each entry typically includes a timestamp and the logged controller status (e.g., measured value, setpoint value, output value).
  ```json
  [
    {
      "timestamp": "2025-01-01T10:00:05L",
      "current_temperature": 25.1,
      "target_temperature": 50.0,
      "output_value": 0.5
    },
    {
      "timestamp": "2025-01-01T10:00:10L",
      "current_temperature": 25.5,
      "target_temperature": 50.0,
      "output_value": 0.5
    }
  ]
  ```

- **Usage Examples using `curl`:**

  1.  **Retrieve the last 50 historical records:**
      ```bash
      curl -X GET "http://localhost:8000/controller/history?lines=50"
      ```

  2.  **Retrieve all records from a specific start date and time:**
      ```bash
      curl -X GET "http://localhost:8000/controller/history?from=2025-01-01T00:00:00Z"
      ```

  3.  **Retrieve all records up to a specific end date and time:**
      ```bash
      curl -X GET "http://localhost:8000/controller/history?to=2025-01-01T23:59:59Z"
      ```

  4.  **Retrieve records within a specific timestamp range:**
      ```bash
      curl -X GET "http://localhost:8000/controller/history?from=2025-01-01T10:00:00Z&to=2025-01-01T11:00:00Z"
      ```

  5.  **Retrieve the last 10 records within a specific timestamp range:**
      ```bash
      curl -X GET "http://localhost:8000/controller/history?lines=10&from=2025-01-01T10:00:00Z&to=2025-01-01T11:00:00Z"
      ```
