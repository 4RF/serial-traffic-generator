# Serial Traffic Generator
This is a tool for testing the performance of serial links. You can make the following measurements:
* Throughput
* Latency
* Poll response latency

# RTS/CTS Flow Control
With this enabled, the tester will assert the RTS signal and then wait for the CTS signal to be returned before sending any serial data. The RTS signal is de-asserted after each packet has finished being transmitted.

# Accuracy
## Serial Driver Delays
The accuracy of any readings made with this application can be compromised by buffering delays in the operating system serial drivers. These delays are often very high in some USB to serial port converters.

The only known working configuration is as follows:
* Devices containing the FT232R chip from FTDI
* The latency timer configuration must be set to 1ms. This is configurable in Windows through device manager under properties->Port Settings->Advanced->Latency Timer.

## Impact of Interpacket Gap on Throughput
Artificially high throughput values may be reported by some equipment if the Interpacket Gap setting does not match the value used on the tested equipment. This can result in more than one serial packet being sent as a single packet by the tested equipment.

If the device being tested contains counters for the number of packets transferred, please ensure that these match the number of packets sent.

# Throughput
In this mode, the time taken to send the specified number of packets is measured.

Throughput/Latency/Poll Packet Size - Specifies the size of each test packet

Response Packet Size - Ingored for this test mode

Packet Count - The number of test packets to send

Interpacket Gap - specifies the separated between packets. This separation is what is used by devices under test to delineate individual packets. For this reason this setting must match the configuration of the device being tested.

# Latency
In this mode, a measurement is taken of the time between when a packet is written to the operating serial buffers of the Sender Port, and when the entire message has been received on the Receiver Port.

If RTS/CTS Flow Control is selected, then the time measurement starts when the RTS signal is asserted. This means the time delay before the CTS signal is asserted by the device is also counted.

This type of latency measurement is called First In Last Out or FILO latency, and is a measure of the total time taken to transfer the data.

Throughput/Latency/Poll Packet Size - Specifies the size of each test packet

Response Packet Size - Ingored for this test mode

Packet Count - The number of test packets to send

Interpacket Gap - Ingored for this test mode

# Round Trip
In this mode, a packet is sent from the Sender Port. Once it has been fully received by the Receiver Port, another packet is sent by the Receiver Port. The latency measurement is taken from the time between when a packet is written to the operating serial buffers of the Sender Port, and when the entire response message has been received back on the Sender Port.

If RTS/CTS Flow Control is selected, then the time measurement starts when the RTS signal is asserted. This means the time delay before the CTS signal is asserted by the device is also counted.

This type of latency measurement is called First In Last Out or FILO latency, and is a measure of the total time taken to transfer the data.

Throughput/Latency/Poll Packet Size - Specifies the size of each test packet sent from the Sender Port

Response Packet Size - Specifies the size of each test packet returned on the Receiver Port

Packet Count - The number of test packets to send

Interpacket Gap - Ingored for this test mode
