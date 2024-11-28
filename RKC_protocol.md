The FB100/400/900 (hereafter, called controller) uses the Polling/Selecting method to establish a data link. The basic procedure is followed ANSI X3.28-1976 subcategories 2.5 and A4 basic mode data transmission control procedure (Fast selecting is the selecting method used in this controller).
- The Polling/Selecting procedures are a centralized control method where the host computer controls the entire process. The host computer initiates all communication so the controller responds according to queries and commands from the host.
- The code use in communication is 7-bit ASCII code including transmission control characters.
The transmission control characters are EOT (04H), ENQ (05H), ACK (06H), NAK (15H), STX (02H) and ETX (03H). The figures in the parenthesis indicate the corresponding hexadecimal number.

# Polling
Polling is the action where the host computer requests one of the connected controllers to transmit data. 
## Polling procedures
(1) Data link initialization
Host computer sends EOT to the controllers to initiate data link before polling sequence.
(2) Data sent from host computer - Polling sequence
The host computer sends the polling sequence in the following formats: [Address (2 digits)] [Memory area number (Optional, 2 digits, starting with K, from K0 to K8)] [Identifier (2 digits)] [ENQ]
Example: 01 M1 [ENQ]
The identifier specifies the type of data that is requested from the controller. The ENQ is the transmission control character that indicates the end of the polling sequence. List of identifier is provided in the the last section.
The ENQ must be attached to the end of the identifier. The host computer then must wait for a response from the controller
(3) Data sent from the controller
If the polling sequence is received correctly, the controller sends data in the following format:
[STX] [Identifier] [Data] [ETX] [BCC]
1. STX
STX is the transmission control character which indicates the start of the text transmission (identifier and data).
2. Identifier (2 digits)
The identifier indicates the type of data (measured value, status and set value) sent to the host computer.
3. Data (7 digits)
Data which is indicated by an identifier of the controller. It is expressed in decimal ASCII code including a minus sign (-) and a decimal point. Data is not zero-suppressed.
Only Model codes (ID), the number of data digits (length) is 32 digits.
4. ETX
ETX is a transmission control character used to indicate the end of text transmission.
5. BCC
BCC (Block Check Character) detects error by using horizontal parity (even number).
Calculation method of BCC: Exclusive OR all data and characters from STX through ETX, not including STX.
Example:
[STX]M100100.0[EXT][STX]
BCC＝4DH XOR 31H XOR 30H XOR 30H XOR 31H XOR 30H XOR 30H XOR 2EH XOR 30H XOR 03H＝50H 
Value of BCC becomes 50H.
(4) EOT sent from the controller (Ending data transmission from the controller)
In the following cases, the controller sends EOT to terminate the data link:
- When the specified identifier is invalid
- When there is an error in the data type
- When data is not sent from the host computer even if the data link is initialized
- When all the data has been sent
(5) No response from the controller
The controller will not respond if the polling address is not received correctly. It may be necessary for the host computer to take corrective action such as a time-out.
(6) ACK (Acknowledgment)
An acknowledgment ACK is sent by the host computer when data received is correct. When the controller receives ACK from the host computer, the controller will send any remaining data of the next identifier without additional action from the host computer.
When host computer determines to terminate the data link, EOT is sent from the host computer.
(7) NAK (Negative acknowledge)
If the host computer does not receive correct data from the controller, it sends a negative acknowledgment NAK to the controller. The controller will re-send the same data when NAK is received. This cycle will go on continuously until either recovery is achieved or the data link is corrected at the host computer.
(8) No response from host computer
When the host computer does not respond within approximately three seconds after the controller sends data, the controller sends EOT to terminate the data link. (Time out: 3 seconds)
(9) Indefinite response from host computer
The controller sends EOT to terminate the data link when the host computer response is indefinite.
(10) EOT (Data link termination)
The host computer sends EOT message when it is necessary to suspend communication with the controller or to terminate the data link due lack of response from the controller.
## Polling procedure example
### (1) When the monitored items is polled
[Example: Measured value (PV) monitor, Identifier: M1]
#### Normal transmission
Host: [EOT]01M1[ENQ]
Controller: [STX]M100100.0[ETX][BCC]
Host: [EOT]
#### Normal transmission with next data (M3)
Host: [EOT]01M1[ENQ]
Controller: [STX]M100100.0[ETX][BCC]
Host: [ACK]
Controller: [STX]M300030.0[ETX][BCC]
Host: [EOT]
#### Error transmission
Host: [EOT]01M1[ENQ]
Controller: [STX]M100100.0[ETX][BCC(wrong)]
Host: [NAK]
Controller: [STX]M100100.0[ETX][BCC]
Host: [EOT]

# Selecting
Selecting is the action where the host computer requests one of the connected controllers to receive data.
## Selecting procedures
(1) Data link initialization
Host computer sends EOT to the controllers to initiate data link before selecting sequence.
(2) Sending selecting address from the host computer
Host computer sends selecting address for the selecting sequence.
(3) Data sent from the host computer
The host computer sends data for the selecting sequence with the following format:
[STX] [Memoery area number (optional)] [Identifier (2 digits)] [Data (7 digits)] [ETX] [BCC]
(4) ACK (Acknowledgment)
An acknowledgment ACK is sent by the controller when data received is correct. When the host computer receives ACK from the controller, the host computer will send any remaining data. If there is no more data to be sent to the controller, the host computer sends EOT to terminate the data link.
(5) NAK (Negative acknowledge)
If the controller does not receive correct data from the host computer, it sends a negative acknowledgment NAK to the host computer. Corrections, such as re-send, must be made at the host computer.
(6) No response from controller
The controller does not respond when it can not receive the selecting address, STX, ETX or BCC.
(7) EOT (Data link termination)
The host computer sends EOT when there is no more data to be sent from the host computer or there is
no response from the controller.

## Selecting procedure example
### (1) When the items corresponding to the Control area is selected [Example: Set value (SV) S1]
#### Normal transmission
Host: [EOT]01[STX]S100100.0[ETX][BCC]
Controller: [ACK]
Host: [EOT]

# Specification
Default Communication speed: 19200 bps
Default Device address: 1
Data bit configuration: Start bit: 1
Default Data bit: 8, without Parity bit
Error control: Vertical parity (With parity bit selected)
Horizontal parity (BCC check)
Communication code: ASCII 7-bit code

# List of Commonly Used Identifiers
The following is the list of the identifiers. A ★ in the name indicates that [Memory area number] can be used with it. Arrtibute indicates if the value is capable of read-write (R/W, host can send data to controller) or read-only (RO)

| No. | Name                                              | Identifier | Attribute |
|-----|---------------------------------------------------|------------|-----------|
| 1   | Model codes                                       | ID         | RO        |
| 2   | Measured value (PV)                               | M1         | RO        |
| 3   | Current transformer 1 (CT1) input value monitor   | M3         | RO        |
| 4   | Current transformer 2 (CT2) input value monitor   | M4         | RO        |
| 5   | Set value (SV) monitor                            | MS         | RO        |
| 6   | Remote setting (RS) input value monitor           | S2         | RO        |
| 7   | Burnout state monitor of feedback resistance      | B1         | RO        |
| 8   | Burnout state monitor of feedback resistance      | B2         | RO        |
| 9   | Event 1 state monitor                             | AA         | RO        |
| 10  | Event 2 state monitor                             | AB         | RO        |
| 11  | Event 3 state monitor                             | AC         | RO        |
| 12  | Event 4 state monitor                             | AD         | RO        |
| 13  | Heater break alarm 1 (HBA1) state monitor         | AE         | RO        |
| 14  | Heater break alarm 2 (HBA2) state monitor         | AF         | RO        |
| 15  | Manipulated output value (MV1) monitor [heat-side]| O1         | RO        |
| 16  | Manipulated output value (MV2) monitor [cool-side]| O2         | RO        |
| 17  | Error code                                        | ER         | RO        |
| 18  | Digital input (DI) state monitor                  | L1         | RO        |
| 19  | Output state monitor                              | Q1         | RO        |
| 20  | Operation mode state monitor                      | L0         | RO        |
| 21  | Memory area soak                                  | TR         | RO        |
| 22  | Integrated operating                              | UT         | RO        |
| 23  | Holding peak value                                | Hp         | RO        |
| 24  | Power feed forward                                | HM         | RO        |
| 25  | Backup memory state monitor                       | EM         | RO        |
| 26  | ROM version monitor                               | VR         | RO        |
| 35  | PID/AT transfer                                   | G1         | R/W       |
| 36  | Auto/Manual transfer                              | J1         | R/W       |
| 37  | Remote/local transfer                             | C1         | R/W       |
| 38  | RUN/STOP transfer                                 | SR         | R/W       |
| 39  | Memory area transfer                              | ZA         | R/W       |
| 40  | Interlock release                                 | IL         | R/W       |
| 41  | Event 1 set value (EV1) ★                         | A1         | R/W       |
| 42  | Event 2 set value (EV2) ★                         | A2         | R/W       |
| 43  | Event 3 set value (EV3) ★                         | A3         | R/W       |
| 44  | Event 4 set value (EV4) ★                         | A4         | R/W       |
| 45  | Control loop break alarm (LBA) time  ★            | A5         | R/W       |
| 46  | LBA deadband ★                                    | N1         | R/W       |
| 47  | Set value (SV)  ★                                 | S1         | R/W       |
| 48  | Proportional band [heat-side] ★                   | P1         | R/W       |
| 49  | Integral time [heat-side] ★                       | I1         | R/W       |
| 50  | Derivative time [heat-side] ★                     | D1         | R/W       |
| 51  | Control response parameter  ★                     | CA         | R/W       |
| 52  | Proportional band [heat-side] ★                   | P2         | R/W       |
| 53  | Integral time [cool-side]  ★                      | 12         | R/W       |
| 54  | Derivative time (cool-side) ★                     | D2         | R/W       |
| 55  | Overlap/Deadband ★                                | V1         | R/W       |
| 56  | Manual reset  ★                                   | MR         | R/W       |
| 57  | Setting change rate limiter (up) ★                | HH         | R/W       |
| 58  | Setting change rate Limiter (down)★               | HL         | R/W       |
| 59  | Area soak time ★                                  | TM         | R/W       |
| 60  | Link area number ★                                | LP         | R/W       |
| 61  | Heater break alarm (HBA1) set value 1             | A7         | R/W       |
| 62  | Heater break determination point 1                | NE         | R/W       |
| 63  | Heater melting determination point 1              | NF         | R/W       |
| 64  | Heater break alarm (HBA2) set value 2             | A8         | R/W       |
| 65  | Heater break determination point 2                | NH         | R/W       |
| 66  | Heater melting determination point 2              | NI         | R/W       |
| 67  | PV bias                                           | РВ         | R/W       |
| 68  | PV digital filter                                 | E1         | R/W       |
| 69  | PV ratio                                          | PR         | R/W       |
| 70  | PV low input cut-off                              | DP         | R/W       |
| 71  | RS bias                                           | RB         | R/W       |
| 72  | RS digital filter                                 | F2         | R/W       |
| 73  | RS ratio                                          | RR         | R/W       |
| 74  | Proportional cycle time [heat-side]               | T0         | R/W       |
| 75  | Proportional cycle time (cool-side)               | T1         | R/W       |
| 76  | Manual manipulated output value                   | ON         | R/W       |
| 77  | Set lock level                                    | LК         | R/W       |
| 206 |   Startup tuning (ST)                             | ST         | R/W       |
| 212 |   Automatic temperature rise learning             | Y8         | R/W       |


For more information, refer to https://www.rkcinst.co.jp/english/downloads/8929/imr01w07e4/