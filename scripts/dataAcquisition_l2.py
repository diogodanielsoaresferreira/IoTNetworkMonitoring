import sys
import argparse
import pyshark
import json
import time

# Version 2
HOST_MAC = ["8e:af:6a:9b:1a:d7", "1a:44:c5:c6:d2:74", "f6:a2:cd:42:b8:a2",
"86:ef:c3:2c:8e:50", "a2:d2:03:41:0e:30", "00:11:22:33:44:55"]

SENSORS_MAC = ["08:00:27:0f:71:bb", "08:00:27:02:cd:44", "08:00:27:21:75:43", "08:00:27:79:55:6d"]

GATEWAY_MAC = ["ca:01:38:84:00:06"]


def main():

	# Start time to calculate execution time
	start_time = None

	# Packets amount in the capture
	packets_amount = 0

	# Features to be written to the output file
	# [0] - Packet length from sensor to host
	# [1] - Packet length from host to sensor
	# [2] - Packet length from sensor to gateway
	# [3] - Packet length from gateway to sensor
	# [4] - Packet length from sensors to sensors
	# [5] - Packet length from sensors to unknown mac's
	# [6] - Packet length from unknown mac's to sensors
	# [7] - Number of packets from sensor to host
	# [8] - Number of packets from host to sensor
	# [9] - Number of packets from sensor to gateway mac
	# [10] - Number of packets from gateway mac to sensor
	# [11] - Number of packets from sensors to sensors
	# [12] - Number of packets from sensors to unknown MAC's
	# [13] - Number of packets from unknown MAC's to sensors
	# [14] - Number of contacted mac's


	outF = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

	# Timestamp of the first packet
	T0 = 0

	# Contacted mac's
	macs = []

	parser=argparse.ArgumentParser()
	parser.add_argument('-f', '--file', nargs='?',required=True, help='capture .pcap filename')
	parser.add_argument('-o', '--output', nargs='?',required=True, help='output file') 
	parser.add_argument('-si', '--sampling_interval', type=int, help='sampling interval (in seconds)', default=1)
	parser.add_argument('-w', '--observation_window', type=int, help='observation window (in seconds)', default=600)
	args=parser.parse_args()

	sampDelta=args.sampling_interval
	obsDelta=args.observation_window

	start_time = time.time()

	# Process packets in file
	try:
		cap = pyshark.FileCapture(args.file, keep_packets=False)

		# List all attributes form capture
		# print(dir(cap))

		# List all attributes from packet
		#print(dir(cap[0]))

		# File output
		with open(args.output, 'w') as file_obj:

			# Iteration through packets
			for packet in cap:

				#print(packet.__dict__)
				
				# Get the packet information
				packet_time = packet.sniff_time
				timestamp = packet.sniff_timestamp
				number = packet.number
				frame_info = packet.frame_info
				packet_length = packet.length
				captured_length = packet.captured_length
				layers = packet.layers
				highest_layer = packet.highest_layer
				transport_layer = packet.transport_layer
				eth_content = packet.eth

				# Get the layer 1 information

				#print(frame_info.__dict__)

				raw_mode = frame_info.raw_mode
				layer_name = frame_info._layer_name
				all_fields = frame_info._all_fields

				protocols = all_fields.get('frame.protocols')
				offset_shift = all_fields.get('frame.offset_shift')
				frame_number = all_fields.get('frame.number')
				time_epoch = all_fields.get('frame.time_epoch')
				frame_length = all_fields.get('frame.len')
				time_delta = all_fields.get('frame.time_delta')
				interface_id = all_fields.get('frame.interface_id')
				frame_ignored = all_fields.get('frame.ignored')
				encapsulation_type = all_fields.get('frame.encap_type')
				marked = all_fields.get('frame.marked')
				capture_length = all_fields.get('frame.cap_len')

				# If encapsulation is ethernet
				if encapsulation_type=="1":
					eth_raw_mode = eth_content.raw_mode
					eth_layer_name = eth_content._layer_name
					eth_all_fields = eth_content._all_fields
					src = eth_all_fields["eth.src"]
					dst = eth_all_fields["eth.dst"]
					src_resolved = eth_all_fields["eth.src_resolved"]
					dst_resolved = eth_all_fields["eth.dst_resolved"]
					eth_type = eth_all_fields.get("eth.type")
					lg = eth_all_fields["eth.lg"]
					addr = eth_all_fields["eth.addr"]
					addr_resolved = eth_all_fields["eth.addr_resolved"]

					
				else:
					print(frame_info)

				# If is first packet, get the first timestamp
				if packets_amount==0:
					T0 = float(timestamp)
					last_ks = -1
				else:
					# Save the last ks
					last_ks = ks
				
				# Update the ks
				ks=int((float(timestamp)-T0)/sampDelta)%obsDelta


				if src_resolved in SENSORS_MAC:

					if dst_resolved in HOST_MAC:
						outF[0] += int(frame_length.fields[0].show)
						outF[7] += 1

					elif dst_resolved in GATEWAY_MAC:
						outF[2] += int(frame_length.fields[0].show)
						outF[9] += 1

					elif dst_resolved in SENSORS_MAC:
						outF[4] += int(frame_length.fields[0].show)
						outF[11] += 1

					else:
						outF[5] += int(frame_length.fields[0].show)
						outF[12] += 1

				elif dst_resolved in SENSORS_MAC:

					if src_resolved in HOST_MAC:
						outF[1] += int(frame_length.fields[0].show)
						outF[8] += 1

					elif src_resolved in GATEWAY_MAC:
						outF[3] += int(frame_length.fields[0].show)
						outF[10] += 1

					else:
						outF[6] += int(frame_length.fields[0].show)
						outF[13] += 1

				if src_resolved not in macs:
					macs.append(src_resolved)

				if dst_resolved not in macs:
					macs.append(dst_resolved)

				outF[14] = len(macs)-1

				# If the last ks is different from the ks, update the file
				# Clean features and repeat until the last ks is the same
				if last_ks != ks and packets_amount>0:
					while last_ks != ks:
						outF_len = len(outF)

						for i in range(outF_len):
							file_obj.write(str(outF[i])+' ')
							outF[i] = 0
						file_obj.write('\n')
						macs = []
						last_ks = (last_ks + 1) % obsDelta

				# Update the number of packets
				packets_amount += 1


	except FileNotFoundError:
		print('\nFile not found. Program finished.')
		sys.exit()
	except Exception as e:
		print(e)
		file_obj.close()
		print('\nCapture reading interrupted.')

	print('\n' + str(packets_amount) + ' packets captured!\n')

	print('--- %s seconds ---' % (time.time() - start_time))


if __name__ == '__main__':
	main()


