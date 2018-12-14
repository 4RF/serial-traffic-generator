# Serial Traffic Generator
#
# Copyright (c) 2016-2018 4RF
#
# This file is subject to the terms and conditions of the GNU General Public
# License Version 3.  See the file "LICENSE" in the main directory of this
# archive for more details.

import time
import serial
import serial.tools.list_ports
import random
import threading
import configparser
import os

from tkinter import *
from tkinter import ttk
from tkinter import scrolledtext
from tkinter import messagebox

class SerialThroughput:
    def __init__(self):
        self.send_thread = None
        self.receive_thread = None

        # Pipeline variables. Only valid for throughput tests
        # packet_received: event to syncronize between send and receive threads
        # packet_received_timeout(seconds): time to wait at sender for response from receiver
        # pipeline_max: max number of packet between sender and receiver (set to 0 for no pipeline)
        # pipeline_current: current number of packet between receiver and transmitter
        self.packet_received = None
        self.packet_received_timeout = 10
        self.pipeline_max = 3

        self.start_time = None
        self.last_rx_time = None
        self.end_time = None
        self.stop_threads = False
        
        config = configparser.ConfigParser()
        config.read('SerialTrafficGenerator.ini')
        if 'config' in config:
            confsection = config['config']
        else:
            confsection = None
        
        top = Tk()
        
        top.geometry("500x700")
            
        top.title("4RF Serial Traffic Generator 1.8")

        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        try:
            top.iconbitmap(os.path.join(base_path, 'serialtrafficgenerator.ico'))
        except:
            # Don't fail if icon file is missing
            pass
        
        top.columnconfigure(0, weight=1)
        top.columnconfigure(1, weight=4)
        
        currentrow = 0

        Label (top, text="Sender Port").grid(row=currentrow, column=0, padx=5, pady=5, sticky='E')

        # Get the available Serial Ports
        serialPorts = ()
        serPorts = self.serial_ports()
        for ports in serPorts:
            serialPorts = serialPorts + (ports,)
            
        send = StringVar()
        combo = ttk.Combobox (top, textvariable=send)
        combo['values'] = serialPorts
        combo.current(0)
        if confsection:
            txport = confsection.get('txport', '')
            if txport in serialPorts:
                combo.current(serialPorts.index(txport))
        combo.grid(row=currentrow, column=1, padx=5, pady=5, sticky='EW')
        currentrow += 1

        Label (top, text="Receiver Port").grid(row=currentrow, column=0, padx=5, pady=5, sticky='E')

        recv = StringVar()
        combo = ttk.Combobox (top, textvariable=recv)
        combo['values'] = serialPorts
        combo.current(0)
        if confsection:
            rxport = confsection.get('rxport', '')
            if rxport in serialPorts:
                combo.current(serialPorts.index(rxport))

        combo.grid(row=currentrow, column=1, padx=5, pady=5, sticky='EW')
        currentrow += 1
        
        Label (top, text="Mode").grid(row=currentrow, column=0, padx=5, pady=5, sticky='E')
        mode = StringVar()
        combo = ttk.Combobox (top, textvariable=mode)
        combo['values'] = [ "Throughput", "Latency", "Poll Response" ]
        combo.current(0)
        combo.bind("<<ComboboxSelected>>", lambda _ : self.mode_combo_changed(mode.get()))
        if confsection:
            val = confsection.get('mode', '')
            if val in combo['values']:
                combo.current(combo['values'].index(val))
        combo.grid(row=currentrow, column=1, padx=5, pady=5, sticky='EW')
        currentrow += 1

        Label (top, text="Baud Rate").grid(row=currentrow, column=0, padx=5, pady=5, sticky='E')
        baud = IntVar()

        combo = ttk.Combobox (top, textvariable=baud)
        combo['values'] = (115200, 57600, 38400, 19200, 9600, 4800, 2400, 1200, 600, 300)
        combo.current(0)
        if confsection:
            val = confsection.get('baud', '')
            if val in combo['values']:
                combo.current(combo['values'].index(val))
        combo.grid(row=currentrow, column=1, padx=5, pady=5, sticky='EW')
        currentrow += 1

        Label (top, text="Data Bits").grid(row=currentrow, column=0, padx=5, pady=5, sticky='E')

        dBits = IntVar()

        combo = ttk.Combobox (top, textvariable=dBits)
        combo['values'] = (8, 7, 6, 5)
        combo.current(0)
        if confsection:
            val = confsection.get('databits', '')
            if val in combo['values']:
                combo.current(combo['values'].index(val))
        combo.grid(row=currentrow, column=1, padx=5, pady=5, sticky='EW')
        currentrow += 1

        Label (top, text="Parity").grid(row=currentrow, column=0, padx=5, pady=5, sticky='E')

        prty = StringVar()

        combo = ttk.Combobox (top, textvariable=prty)
        combo['values'] = ("None", "Odd", "Even")
        combo.current(0)
        if confsection:
            val = confsection.get('parity', '')
            if val in combo['values']:
                combo.current(combo['values'].index(val))
        combo.grid(row=currentrow, column=1, padx=5, pady=5, sticky='EW')
        currentrow += 1

        Label (top, text="Stop Bits").grid(row=currentrow, column=0, padx=5, pady=5, sticky='E')

        sBits = IntVar()

        combo = ttk.Combobox (top, textvariable=sBits)
        combo['values'] = (1, 2)
        combo.current(0)
        if confsection:
            val = confsection.get('stop_bits', '')
            if val in combo['values']:
                combo.current(combo['values'].index(val))
        combo.grid(row=currentrow, column=1, padx=5, pady=5, sticky='EW')
        currentrow += 1
        
        self.cts_rts = IntVar()
        self.cts_rts.set(1)
        if confsection:
            val = confsection.get('flow_control', 'True')
            if val == 'True':
                self.cts_rts.set(1)
            else:
                self.cts_rts.set(0)
        ttk.Checkbutton(top, text="RTS/CTS Flow Control", variable=self.cts_rts).grid(row=currentrow, column=1, padx=5, pady=5, sticky='W')
        currentrow += 1

        Label (top, text="Packet Size").grid(row=currentrow, column=0, padx=5, pady=5, sticky='E')

        size_value = IntVar()
        size_value.set(512)
        if confsection:
            val = confsection.get('packet_size', '512')
            size_value.set(int(val))
        Entry (top, textvariable=size_value).grid(row=currentrow, column=1, padx=5, pady=5, sticky='W')
        currentrow += 1
        
        self.response_packet_size_label = Label (top, text="Response Packet Size")
        self.response_packet_size_label.grid(row=currentrow, column=0, padx=5, pady=5, sticky='E')

        response_size_value = IntVar()
        response_size_value.set(512)
        if confsection:
            val = confsection.get('response_packet_size', '512')
            response_size_value.set(int(val))
        self.response_packet_size_entry = Entry (top, textvariable=response_size_value)
        self.response_packet_size_entry.grid(row=currentrow, column=1, padx=5, pady=5, sticky='W')
        currentrow += 1

        self.response_packet_size_label.grid_remove()
        self.response_packet_size_entry.grid_remove()

        Label (top, text="Packet Count").grid(row=currentrow, column=0, padx=5, pady=5, sticky='E')

        cnt_value = IntVar()
        cnt_value.set(100)
        if confsection:
            val = confsection.get('packet_count', '100')
            cnt_value.set(int(val))
        Entry (top, textvariable=cnt_value).grid(row=currentrow, column=1, padx=5, pady=5, sticky='W')
        currentrow += 1

        Label (top, text="Interpacket Gap\n(chars)").grid(row=currentrow, column=0, padx=5, pady=5, sticky='E')

        tx_delay_value = StringVar()
        tx_delay_value.set("3.5")
        if confsection:
            val = confsection.get('inter_packet_gap', '3.5')
            tx_delay_value.set(float(val))
        Entry (top, textvariable=tx_delay_value).grid(row=currentrow, column=1, padx=5, pady=5, sticky='W')
        currentrow += 1
        
        Label (top, text="Timeout (ms)").grid(row=currentrow, column=0, padx=5, pady=5, sticky='E')

        read_timeout = IntVar()
        read_timeout.set(5000)
        if confsection:
            val = confsection.get('timeout', '5000')
            read_timeout.set(int(val))
        Entry (top, textvariable=read_timeout).grid(row=currentrow, column=1, padx=5, pady=5, sticky='W')
        currentrow += 1

        self.start_stop_button = Button (top, text="Start", justify=CENTER, bd=6, 
                                    command = lambda : self.start_stop_click(send.get(), recv.get(), baud.get(), dBits.get(), prty.get(), 
                                                            sBits.get(), size_value.get(), response_size_value.get(), float(tx_delay_value.get()), 
                                                            cnt_value.get(), mode.get(), read_timeout.get()))

        self.start_stop_button.grid(row=currentrow, column=0, columnspan=2)
        currentrow += 1
        
        self.result_box = scrolledtext.ScrolledText (top, wrap="word")
        self.result_box.grid(row=currentrow, column=0, columnspan=2, sticky='nsew')
        top.rowconfigure(currentrow, weight=1)
        
        self.tktop = top
        
        top.after(100, self.check_completion)

    def mode_combo_changed(self, mode):
        if mode == "Poll Response":
            self.response_packet_size_label.grid()
            self.response_packet_size_entry.grid()
        else:
            self.response_packet_size_label.grid_remove()
            self.response_packet_size_entry.grid_remove()

    def serial_ports(self):
        result = []
        
        ports = serial.tools.list_ports.comports()
        
        # Sort the list of comports by com number, because windows returns list in a random order
        ports = sorted(ports, key=lambda port: int(''.join(ch for ch in port.device if ch.isdigit())))
        
        for p in ports:
            str = p.device
            if p.description:
                str = str + " - " + p.description
            result.append(str)
        
        return result
    
    def bits_per_char(self):
        return 1 + self.data_bits + self.stop_bits + self.parity
        
    def calc_packet_tx_delay(self, len):
        # Accurately measuring the time before a packet has finished transmitting is important for two reasons:
        # 1. Inserting an accurate interpacket gap. This is needed to ensure receiving radio sees a gap between packets,
        #    otherwise radio may join packets together and show an artificially fast throughput.
        # 2. For legacy radios with key-up signals, 485 devices etc, it is important to key the radio under test down 
        #    AFTER data has been transferred
        #
        # There is no good tx complete event provided in windows, so this application assumes that after data
        # has been written into the tx buffer, windows will transmit all characters without any gaps. This means
        # The application can wait the number of bytes * bits per bytes to find the end point of the packet.
        if (self.tx_delay_chars > 0) or self.use_flow_control:
            tx_delay_data = len * self.bits_per_char() / self.baud_rate
            tx_delay_ifg = self.tx_delay_chars * self.bits_per_char() / self.baud_rate
            if tx_delay_ifg < 0.001:
                tx_delay_ifg = 0.001
            tx_delay_seconds = tx_delay_data + tx_delay_ifg
        else:
            tx_delay_seconds = 0

        return tx_delay_seconds

    def start_stop_click(self, sender_port, receiver_port, baud_rate, data_bits, parity, stop_bits, packet_size, response_size, tx_delay_chars, packet_count, mode, timeout):
        if (self.send_thread and self.send_thread.is_alive()) or (self.receive_thread and self.receive_thread.is_alive()):
            if self.cancel_test():
                self.start_stop_button.config(text="Start")
                self.result_box.insert(END, "\nTest Cancelled.\n")
            else:
                self.result_box.insert(END, "\nTest Cancel Failed!\n")
        else:
            if (receiver_port == sender_port) and (mode == "Poll Response"):
                messagebox.showerror("Configuration Error", "You must select two different serial ports for Poll Response mode")
                return

            self.stop_threads = False
            self.mode = mode
            
            config = configparser.ConfigParser()
            config['config'] = {
                'txport' : sender_port,
                'rxport' : receiver_port,
                'baud' : baud_rate,
                'data_bits' : data_bits,
                'stop_bits' : stop_bits,
                'parity' : parity,
                'packet_size' : packet_size,
                'response_packet_size' : response_size,
                'packet_count' : packet_count,
                'inter_packet_gap' : tx_delay_chars,
                'mode' : mode,
                'timeout' : timeout
            }
            self.packet_received_timeout = timeout/1000.0 + 0.1
            if self.cts_rts.get() == 1:
                config['config']['flow_control'] = 'True'
            else:
                config['config']['flow_control'] = 'False'
            
            with open('SerialTrafficGenerator.ini', 'w') as configfile:
                config.write(configfile)
        
            if (parity == "None"):
                parity = 0
                pm = serial.PARITY_NONE
            elif parity == "Odd":
                parity = 1
                pm = serial.PARITY_ODD
            else:
                parity = 1
                pm = serial.PARITY_EVEN
                
            stop_bits = int(stop_bits)
            if stop_bits == 1:
                sb = serial.STOPBITS_ONE
            elif stop_bits == 2:
                sb = serial.STOPBITS_TWO
            else:
                sb = serial.STOPBITS_ONE_POINT_FIVE
            
            data_bits = int(data_bits)
            if data_bits == 5:
                bs = serial.FIVEBITS
            elif data_bits == 6:
                bs = serial.SIXBITS
            elif data_bits == 7:
                bs = serial.SEVENBITS
            else:
                bs = serial.EIGHTBITS
            
            # Remove the human readable name from the serial port, as only the device name is needed when opening port
            sender_port = sender_port.split(' ')[0]
            receiver_port = receiver_port.split(' ')[0]
            
            self.packet_count = packet_count
            self.packet_size = packet_size
            self.response_size = response_size
            self.data_bits = data_bits
            self.stop_bits = stop_bits
            self.parity = parity
            self.tx_delay_chars = tx_delay_chars
            self.baud_rate = baud_rate
            
            self.rx_packet_count = 0
            self.rx_packet_ok_count = 0
            self.rx_response_packet_count = 0
            self.rx_response_packet_ok_count = 0
            self.rx_byte_count = 0
            self.tx_packet_count = 0
            self.tx_response_packet_count = 0
            self.latencies = []
            
            self.result_box.delete("1.0", END)
            
            try:
                if self.cts_rts.get() == 1:
                    self.use_flow_control = True
                else:
                    self.use_flow_control = False
                
                # Connect to the Serial ports
                sender = serial.Serial (sender_port, baud_rate, rtscts=False, stopbits=sb, bytesize=bs, parity=pm, timeout=timeout/1000.0, write_timeout=10)
                if receiver_port == sender_port:
                    receiver = sender
                else:
                    receiver = serial.Serial (receiver_port, baud_rate, rtscts=False, stopbits=sb, bytesize=bs, parity=pm, timeout=timeout/1000.0)
                
                # Ensure that RTS signal is innitially low for both serial ports. This is often used as a key-up signal
                # of half duplex devices and we want to ensure that sender is in receive/tx idle state at start, and receiver 
                # is always in receive mode
                sender.setRTS(False)
                receiver.setRTS(False)
            
                # Create threads for sending and receiving
                if mode == "Throughput":
                    self.packet_received = threading.Semaphore(self.pipeline_max)
                    self.send_thread = threading.Thread(target=self.send_data_thread, args=(sender,))
                    self.receive_thread = threading.Thread(target=self.read_data_thread, args=(receiver,))
                    
                    # Start the Threads
                    self.receive_thread.start()
                    self.send_thread.start()
                elif mode == "Latency":
                    self.send_thread = threading.Thread(target=self.latency_thread, args=(sender, receiver))
                    self.receive_thread = self.send_thread
                    self.send_thread.start()
                elif mode == "Poll Response":
                    self.send_thread = threading.Thread(target=self.poll_response_thread, args=(sender, receiver))
                    self.receive_thread = self.send_thread
                    self.send_thread.start()

                self.result_box.insert(END, "Running test, please wait...\n")
                self.start_stop_button.config(text="Stop")
            except:
                self.result_box.insert(END, "Error running test. Check serial ports are not in use.\n")
                self.cancel_test()
        
    def flow_control_tx_start(self, port):
        # When flow control is enabled, we set the RTS signal (to key up external radio, RS485 device etc)
        # and then wait for CTS signal to confirm that device under test is ready to transmit
        if self.use_flow_control:
            flow_control_start = time.clock()
            port.setRTS(True)
            while port.getCTS() == False:
                if time.clock() - flow_control_start > 10:
                    raise Exception('Timeout waiting for flow control')
        
        self.tx_start = time.clock()
    
    
    def flow_control_tx_finish(self, port, tx_delay_seconds):
        # A delay is required between each write to ensure the requested inter-packet gap is introduced
        sleep_duration = tx_delay_seconds - (time.clock() - self.tx_start)
        
        if sleep_duration < 0.001:
            sleep_duration = 0.001

        # Only use sleep for longer delays (windows only provids 1ms resolution sleep)
        # NOTE: Assumption of 1ms resolution may only be valid for recent windows versions (eg windows 7, 8, and 10)
        if sleep_duration >= 0.002:
            time.sleep(sleep_duration - 0.001)
        
        # Busy wait for any remaining time, which gives good accuracy for small delays
        sleep_duration = tx_delay_seconds - (time.clock() - self.tx_start)
        if sleep_duration > 0:
            # For shorter delays, use busy wait loop
            s = time.clock()
            while time.clock() - s < sleep_duration:
                pass
        
        # Ensure any external devices are keyed off after packet transmission has completed
        if self.use_flow_control:
            port.setRTS(False)
    
    def latency_thread(self, send_port, receive_port):
        # Build the packet based on the size passed
        packet = bytearray(self.packet_size)
        for x in range(0, self.packet_size):
            packet[x] = random.randint(0,255)
            
        tx_delay_seconds = self.calc_packet_tx_delay(self.packet_size)
        
        try:
            for x in range (0, self.packet_count):
                if self.stop_threads:
                    break

                start = time.clock()
                
                self.flow_control_tx_start(send_port)
                
                send_port.write(packet)
                self.tx_packet_count += 1
                
                self.flow_control_tx_finish(send_port, tx_delay_seconds)
                
                data = receive_port.read(self.packet_size)
                
                if len(data) > 0:
                    self.rx_byte_count += len(data)
                    self.rx_packet_count += 1
                    
                    if data == packet:
                        self.rx_packet_ok_count += 1
                
                    latency = time.clock() - start
                    self.latencies.append(latency)
        except:
			# This is usually because of a timeout. Just exit the sending thread
            pass

    def poll_response_thread(self, polling_port, responder_port):
        tx_delay_seconds = self.calc_packet_tx_delay(self.packet_size)
        tx_response_delay_deconds = self.calc_packet_tx_delay(self.response_size)
    
        # Build the packet based on the size passed
        packet = bytearray(self.packet_size)
        for x in range(0, self.packet_size):
            packet[x] = random.randint(0,255)
        
        response_packet = bytearray(self.response_size)
        for x in range(0, self.response_size):
            response_packet[x] = random.randint(0,255)

        try:
            for x in range (0, self.packet_count):
                if self.stop_threads:
                    break

                start = time.clock()
                
                self.flow_control_tx_start(polling_port)
                
                polling_port.write(packet)
                self.tx_packet_count += 1
                
                self.flow_control_tx_finish(polling_port, tx_delay_seconds)
                
                data = responder_port.read(self.packet_size)
                
                if len(data) > 0:
                    self.rx_byte_count += len(data)
                    self.rx_packet_count += 1
                    
                    if data == packet:
                        self.rx_packet_ok_count += 1
                    
                        self.flow_control_tx_start(responder_port)
                        responder_port.write(response_packet)
                        self.tx_response_packet_count += 1
                        
                        self.flow_control_tx_finish(responder_port, tx_response_delay_deconds)
                        
                        data = polling_port.read(self.response_size)
                        
                        if len(data) > 0:
                            self.rx_byte_count += len(data)
                            self.rx_response_packet_count += 1
                            
                            if data == response_packet:
                                self.rx_response_packet_ok_count += 1
                                self.latencies.append(time.clock() - start)
        except:
			# This is usually because of a timeout. Just exit the sending thread
            pass

    def send_data_thread(self, send_port):
        tx_delay_seconds = self.calc_packet_tx_delay(self.packet_size)
        
        # Build the packet based on the size passed
        packet = bytearray(self.packet_size)
        for x in range(0, self.packet_size):
            packet[x] = random.randint(0,255)
        
        # Record the start time of the test, used to calculate total test time and therefore throughput
        self.start_time = time.clock()
        self.pipeline_current = 0
        try:
            for x in range (0, self.packet_count):
                self.packet_received.acquire(True)
                self.flow_control_tx_start(send_port)
                
                send_port.write(packet)
                
                #Increment send packet count
                self.tx_packet_count += 1

                self.flow_control_tx_finish(send_port, tx_delay_seconds)

                if self.stop_threads:
                    break
            
        except:
			# This is usually because of a timeout. Just exit the sending thread
            pass

    
    def read_data_thread (self, receive_port):
        self.rx_byte_count = 0
        self.last_rx_time = None
        
        while (not self.stop_threads):  
            if (self.rx_byte_count >= (self.packet_size * self.packet_count)):
                break
            else:
                data = receive_port.read(self.packet_size)
                self.rx_byte_count += len(data)
                if len(data) == 0:
                    break
                else:
                    self.last_rx_time = time.clock()
                if self.pipeline_max:
                    if (self.rx_byte_count % self.packet_size) == 0:
                        self.packet_received.release()
        
        self.end_time = time.clock()
        
    def check_completion(self):
        if self.send_thread and self.receive_thread:
            self.result_box.delete("1.0", END)

            if (not self.send_thread.is_alive()) and (not self.receive_thread.is_alive()):
                self.print_values(True)
                
                self.send_thread = None
                self.receive_thread = None
                self.end_time = None
                self.start_time = 0.0
                self.start_stop_button.config(text="Start")
            else:
                self.result_box.insert(INSERT, "Running test, please wait...\n")
                self.print_values(False)
                
        self.tktop.after(100, self.check_completion)


    def print_values (self, test_finished):
        if self.last_rx_time and self.end_time and (self.end_time < self.last_rx_time):
            end_time = self.last_rx_time
        elif self.end_time:
            end_time = self.end_time
        else:
            end_time = time.clock()
        
        if self.mode == "Throughput":
            if self.start_time:
                elapsed_time = end_time - self.start_time
            else:
                elapsed_time = 0
            tx_characters = self.packet_size * self.packet_count
            
            if elapsed_time > 0:
                # Packets per second only counts whole packets received
                rxPackets = self.rx_byte_count // self.packet_size
                packetsps = rxPackets / elapsed_time
                
                charsps = self.rx_byte_count / elapsed_time
            
                # When calculating the bits per second for RS232, the start, stop and parity bits must be counted as well as the actual data bits
                bitsps = self.rx_byte_count * (1 + self.data_bits + self.parity + self.stop_bits) / elapsed_time
            else:
                packetsps = 0
                charsps = 0
                bitsps = 0

            self.result_box.insert(INSERT, "Tx Characters        : %s (%.1f %%)\n" % (self.tx_packet_count * self.packet_size, (self.tx_packet_count / self.packet_count * 100)))
            self.result_box.insert(INSERT, "Rx Characters        : %s (%.1f %%)\n" % (self.rx_byte_count, (self.rx_byte_count / (self.packet_count * self.packet_size) * 100)))
            if test_finished:
                self.result_box.insert(INSERT, "Lost Characters      : %s\n" % (tx_characters - self.rx_byte_count))
            else:
                self.result_box.insert(INSERT, "Remaining Characters : %s\n" % (tx_characters - self.rx_byte_count))
            self.result_box.insert(INSERT, "Run Time             : {:.3f}\n\n".format(elapsed_time))
            self.result_box.insert(INSERT, "Packets/s            : {:.3f}\n".format(packetsps))
            self.result_box.insert(INSERT, "Char/s               : {:.3f}\n".format(charsps))
            self.result_box.insert(END,    "Bits/s               : {:.3f}\n".format(bitsps))
        elif self.mode == "Latency":
            self.result_box.insert(INSERT, "Tx Packets         : %d\n" % self.tx_packet_count)
            self.result_box.insert(INSERT, "Rx Packets         : %d\n" % self.rx_packet_ok_count)
            self.result_box.insert(INSERT, "Rx Failed          : %d\n\n" % (self.rx_packet_count - self.rx_packet_ok_count))

        elif self.mode == "Poll Response":
            self.result_box.insert(INSERT, "Poll Packets Sent         : %d\n" % self.tx_packet_count)
            self.result_box.insert(INSERT, "Poll Packets Received     : %d\n" % self.rx_packet_ok_count)
            self.result_box.insert(INSERT, "Response Packets Sent     : %d\n" % self.tx_response_packet_count)
            self.result_box.insert(INSERT, "Response Packets Received : %d\n" % self.rx_response_packet_ok_count)

        if len(self.latencies) > 0:
            self.result_box.insert(INSERT, "First 3 FILO Latencies :")
            for l in self.latencies[0:3]:
                self.result_box.insert(INSERT, " {:.3f}".format(l))
            self.result_box.insert(INSERT, "\nLast 3 FILO Latencies  :")
            for l in self.latencies[len(self.latencies)-3:]:
                self.result_box.insert(INSERT, " {:.3f}".format(l))
            if test_finished:
                if self.mode == "Latency":
                    transfer_size = self.packet_size
                else:
                    transfer_size = self.packet_size + self.response_size
                ideal_latency = transfer_size * self.bits_per_char() / self.baud_rate
                filo_latency = sum(self.latencies) / len(self.latencies)
                if filo_latency > ideal_latency:
                    added_latency = filo_latency - ideal_latency
                else:
                    added_latency = 0
                
                # It is not possible to accurately measure the time that the first byte of a packet arrives. This is due to the 
                # serial port hardware having an internal FIFO buffer, and only delivering bytes to operating system in a burst.
                # This in turn means we have no way of measuring FILO latency accurately. The below calculation infers what this
                # will be, however this may be innacurate if the device being tested broke the data up into smaller packets for
                # transport
                if filo_latency > ideal_latency*2:
                    lifo_latency = filo_latency - ideal_latency*2
                else:
                    lifo_latency = 0
                self.result_box.insert(INSERT, "\n\nAverage Latency (seconds)\n")
                self.result_box.insert(INSERT, "  FILO                   : {:.3f}\n".format(filo_latency))
                self.result_box.insert(INSERT, "  LIFO (1)               : {:.3f}\n".format(lifo_latency))
                self.result_box.insert(INSERT, "  Ideal FILO at {:d} bps : {:.3f}\n".format(self.baud_rate, ideal_latency))
                self.result_box.insert(INSERT, "  Extra FILO (2)         : {:.3f}\n".format(added_latency))
                self.result_box.insert(INSERT, "\n")
                self.result_box.insert(INSERT, "(1) LIFO latency may not be accurate, as it cannot be accurately measured with PC serial ports\n")
                self.result_box.insert(INSERT, "(2) Compared with simple RS232 loopback\n\n")
                self.result_box.insert(INSERT, "Glossary:\n")
                self.result_box.insert(INSERT, "FILO) First In Last Out.\n")
                self.result_box.insert(INSERT, "This is the time between the first bit into the transmitter and the last bit out of the receiver, or simply the total time taken to transfer the data.\n\n")
                self.result_box.insert(INSERT, "LIFO) Last In First Out.\n")
                self.result_box.insert(INSERT, "This is the time between the last bit into the transmitter and the first bit out of the receiver. Assuming the device is buffering each packet, this gives a measure of the internal transfer speed of the device.")
                
    def cancel_test (self):
        self.stop_threads = True
        if self.packet_received:
            self.packet_received.release()
        if self.send_thread:
            if self.send_thread.isAlive():
                self.send_thread.join(self.packet_received_timeout * 2)
            if self.send_thread.isAlive():
                print("Error stopping send thread")
            else:
                self.send_thread = None
        if self.receive_thread:
            if self.receive_thread.isAlive():
                self.receive_thread.join(self.packet_received_timeout * 2)
            if self.receive_thread.isAlive():
                print("Error stopping receive thread")
            else:
                self.receive_thread = None

        return (self.send_thread == None) and (self.receive_thread == None)
    
    def execute (self):
        self.tktop.mainloop()
        self.cancel_test()

if __name__ == "__main__":
    serial_throughput = SerialThroughput()
    serial_throughput.execute()
