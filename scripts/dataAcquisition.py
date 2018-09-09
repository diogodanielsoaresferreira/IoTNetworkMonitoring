import sys
import argparse
import pyshark
import json
import time
import pygeoip
from geopy.distance import geodesic

IpDatabase = pygeoip.GeoIP('GeoLiteCity.dat')

HOST_IPS = ["192.168.0.10", "http://192.168.100.1", "http://192.168.100.2", "http://192.168.100.3", "http://192.168.100.4", "http://192.168.100.5",
"http://192.168.100.6", "http://192.168.100.7", "http://192.168.100.8", "http://192.168.100.9", "http://192.168.100.10"]

SENSOR_IPS = ["192.168.0.1", "192.168.0.2", "192.168.0.3", "192.168.0.4"]

HOST_LOCATION = (38.736946, -9.142685)


def main():

	# Start time to calculate execution time
	start_time = None

	# Packets amount in the capture
	packets_amount = 0

	# Features to be written to the output file
	# [0] - IPv4 packets sum length (from host_ips to sensor_ips)
	# [1] - IPv4 packets sum length (from sensor_ips to host_ips)
	# [2] - IPv4 packets sum length (from sensor_ips to unknow ips)
	# [3] - Number of ARP packets
	# [4] - Number of TCP packets (IPv4)
	# [5] - Number of UDP packets (IPv4)
	# [6] - Number of other packets (IPv4)
	# [7] - IPv4 packets number (from host_ips to sensor_ips)
	# [8] - IPv4 packets number (from sensor_ips to host_ips)
	# [9] - IPv4 packets number (from sensor_ips to unknow ips)
	# [10] - Number of DNS packets
	# [11] - Number of ICMP packets
	# [12] - Number of external IP's contacted
	# [13] - Number of external IP's that contact the sensors
	# [14] - IPv4 packets sum length (from sensor_ips to sensor_ips)
	# [15] - IPv4 packets number (from sensor_ips to sensor_ips)
	# [16] - Number of TCP SYN flags
	# [17] - Number of TCP ACK flags
	# [18] - Number of TCP FIN flags
	# [19] - Number of TCP URG flags
	# [20] - Number of TCP PUSH flags
	# [21] - Number of TCP RST flags
	# [22] - Geographical distance from the location of server to the location of external IP
	# [23] - Geographical distance from the location of external IP to the location of server

	outF = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

	# External IP's contacted
	external_ips_dst = []

	# External IP's that contact the sensors
	external_ips_src = []


	# Timestamp of the first packet
	T0 = 0

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

					# Arp
					if eth_type=="0x00000806":
						arp_packet = layers[1]
						#print(arp_packet)
						#print(arp_packet.__dict__)

						arp_layer_name = arp_packet._layer_name
						arp_raw_mode = arp_packet.raw_mode
						arp_all_fields = arp_packet._all_fields

						arp_opcode = arp_all_fields.get("arp.opcode")
						arp_hw_size = arp_all_fields.get("arp.hw.size")
						arp_src_hw_mac = arp_all_fields.get("arp.src.hw_mac")
						arp_src_proto_ipv4 = arp_all_fields.get("arp.src.proto_ipv4")
						arp_proto_type = arp_all_fields.get("arp.proto.type")
						arp_dst_hw_max = arp_all_fields.get("arp.dst.hw_mac")
						arp_proto_size = arp_all_fields.get("arp.proto.size")
						arp_dst_proto_ipv4 = arp_all_fields.get("arp.dst.proto_ipv4")
						arp_hw_type = arp_all_fields.get("arp.hw.type")

					# Ipv4 packet
					elif eth_type=="0x00000800":
						ipv4_packet = layers[1]
						#print(layers[1])
						#print(ipv4_packet.__dict__)

						ipv4_layer_name = ipv4_packet._layer_name
						ipv4_raw_mode = ipv4_packet.raw_mode
						ipv4_all_fields = ipv4_packet._all_fields

						ipv4_geoIp = ipv4_all_fields.get('')
						ipv4_flags_mf = ipv4_all_fields.get('ip.flags.mf')
						ipv4_len = ipv4_all_fields.get('ip.len')
						ipv4_frag_offset = ipv4_all_fields.get('ip.frag_offset')
						ipv4_dst = ipv4_all_fields.get('ip.dst')
						ipv4_protocol = ipv4_all_fields.get('ip.proto')
						ipv4_dsfield_dscp = ipv4_all_fields.get('ip.frag_offset')
						ipv4_dsfield = ipv4_all_fields.get('ip.dsfield')
						ipv4_hdr_len = ipv4_all_fields.get('ip.hdr_len')
						ipv4_host = ipv4_all_fields.get('ip.host')
						ipv4_id = ipv4_all_fields.get('ip.id')
						ipv4_flags_rb = ipv4_all_fields.get('ip.flags.rb')
						ip_version = ipv4_all_fields.get('ip.version')
						ip_checksum = ipv4_all_fields.get('ip.checksum.status')
						ipv4_src = ipv4_all_fields.get('ip.src')
						ipv4_dsfield_ecn = ipv4_all_fields.get('ip.dsfield.ecn')
						ipv4_ttl = ipv4_all_fields.get('ip.ttl')
						ipv4_src_host = ipv4_all_fields.get('ip.src_host')
						ipv4_dst_host = ipv4_all_fields.get('ip.dst_host')
						ipv4_flags_df = ipv4_all_fields.get('ip.flags.df')
						ipv4_flags = ipv4_all_fields.get('ip.flags')
						ip_addr = ipv4_all_fields.get('ip.addr')
						ipv4_checksum = ipv4_all_fields.get('ip.checksum')

						# TCP packet
						if ipv4_protocol=='6':
							tcp_packet = layers[2]
							#print(tcp_packet)
							#print(tcp_packet.__dict__)

							tcp_layer_name = tcp_packet._layer_name
							tcp_raw_mode = tcp_packet.raw_mode
							tcp_all_fields = tcp_packet._all_fields

							tcp_text = tcp_all_fields.get('')
							tcp_timestamp_tsval = tcp_all_fields.get('tcp.options.timestamp.tsval')
							tcp_flags_res = tcp_all_fields.get('tcp.flags.res')
							tcp_flags_fin = tcp_all_fields.get('tcp.flags.fin')
							tcp_flags_syn = tcp_all_fields.get('tcp.flags.syn')
							tcp_type_class = tcp_all_fields.get('tcp.options.type.class')
							tcp_flags_push = tcp_all_fields.get('tcp.flags.push')
							tcp_nxtseq = tcp_all_fields.get('tcp.nxtseq')
							tcp_flags_ns = tcp_all_fields.get('tcp.flags.ns')
							tcp_port = tcp_all_fields.get('tcp.port')
							tcp_window_size_value = tcp_all_fields.get('tcp.window_size_value')
							tcp_src_port = tcp_all_fields.get('tcp.srcport')
							tcp_timestamp_tsecr = tcp_all_fields.get('tcp.options.timestamp.tsecr')
							tcp_ack = tcp_all_fields.get('tcp.ack')
							tcp_stream = tcp_all_fields.get('tcp.stream')
							tcp_flags = tcp_all_fields.get('tcp.flags')
							tcp_analysis_push_bytes_sent = tcp_all_fields.get('tcp.analysis.push_bytes_sent')
							tcp_urgent_pointer = tcp_all_fields.get('tcp.urgent_pointer')
							tcp_flags_ack = tcp_all_fields.get('tcp.flags.ack')
							tcp_flags_cwr = tcp_all_fields.get('tcp.flags.cwr')
							tcp_checksum_status = tcp_all_fields.get('tcp.checksum.status')
							tcp_window_size = tcp_all_fields.get('tcp.window_size')
							tcp_flags_ecn = tcp_all_fields.get('tcp.flags.ecn')
							tcp_options = tcp_all_fields.get('tcp.options')
							tcp_type_copy = tcp_all_fields.get('tcp.options.type.copy')
							tcp_flags_urg = tcp_all_fields.get('tcp.flags.urg')
							tcp_analysis_bytes_in_flight = tcp_all_fields.get('tcp.analysis.bytes_in_flight')
							tcp_length = tcp_all_fields.get('tcp.len')
							tcp_window_size_scale_factor = tcp_all_fields.get('tcp.window_size_scalefactor')
							tcp_segment_data = tcp_all_fields.get('tcp.segment_data')
							tcp_seg = tcp_all_fields.get('tcp.seq')
							tcp_reset = tcp_all_fields.get('tcp.flags.reset')
							tcp_hdr_len = tcp_all_fields.get('tcp.hdr_len')
							tcp_options_len = tcp_all_fields.get('tcp.option_len')
							tcp_option_kind = tcp_all_fields.get('tcp.option_kind')
							tcp_dstport = tcp_all_fields.get('tcp.dstport')
							tcp_checksum = tcp_all_fields.get('tcp.checksum')
							tcp_flags_str = tcp_all_fields.get('tcp.flags.str')
							tcp_options_type = tcp_all_fields.get('tcp.options.type')
							tcp_type_number = tcp_all_fields.get('tcp.options.type.number')
							tcp_analysis = tcp_all_fields.get('tcp.analysis')
							tcp_ws_expert_severity = tcp_all_fields.get('_ws.expert.severity')
							tcp_ws_expert_message = tcp_all_fields.get('_ws.expert.message')
							tcp_ws_expert = tcp_all_fields.get('_ws.expert')
							tcp_ws_expert_group = tcp_all_fields.get('_ws.expert.group')
							tcp_checksum = tcp_all_fields.get('tcp.checksum')
							tcp_analysis_ack_frame = tcp_all_fields.get('tcp.analysis.acks_frame')

						# UDP
						elif ipv4_protocol=="17":
							udp_packet = layers[2]

							udp_raw_mode = udp_packet.raw_mode
							udp_layer_name = udp_packet._layer_name
							udp_all_fields = udp_packet._all_fields

							udp_port = udp_all_fields.get("udp.port")
							udp_source_port = udp_all_fields.get("udp.srcport")
							udp_checksum = udp_all_fields.get("udp.checksum")
							udp_stream = udp_all_fields.get("udp.stream")
							udp_destination_port = udp_all_fields.get("udp.dstport")
							udp_length = udp_all_fields.get("udp.length")
							udp_checksum_status = udp_all_fields.get("udp.checksum.status")

							# DNS request
							if len(layers)>3 and layers[3]._layer_name=='dns':
								upper_layer = layers[3]

						# ICMP
						elif ipv4_protocol=="1":
							icmp_packet = layers[2]

						else:
							print("Unrecognized transport protocol")
							print(ipv4_protocol)
							print(layers[2])
							print(layers[2].__dict__)

					# Ipv6 packet
					elif eth_type=="0x000086dd":
						ipv6_packet = layers[1]
						#print(ipv6_packet)
						#print(ipv6_packet.__dict__)

						ipv6_raw_mode = ipv6_packet.raw_mode
						ipv6_layer_name = ipv6_packet._layer_name
						ipv6_all_fields = ipv6_packet._all_fields

						ipv6_text = ipv6_all_fields.get('')
						ipv6_tclass = ipv6_all_fields.get('ipv6.tclass')
						ipv6_version = ipv6_all_fields.get('ipv6.version')
						ipv6_payload_length = ipv6_all_fields.get('ipv6.plen')
						ipv6_host = ipv6_all_fields.get('ipv6.host')
						ip_version = ipv6_all_fields.get('ip.version')
						ipv6_src_host = ipv6_all_fields.get('ipv6.src_host')
						ipv6_tclass_dscp = ipv6_all_fields.get('ipv6.tclass.dscp')
						ipv6_nxt = ipv6_all_fields.get('ipv6.nxt')
						ipv6_dst = ipv6_all_fields.get('ipv6.dst')
						ipv6_src = ipv6_all_fields.get('ipv6.src')
						ipv6_hop_limit = ipv6_all_fields.get('ipv6.hlim')
						ipv6_dst_host = ipv6_all_fields.get('ipv6.dst_host')
						ipv6_addr = ipv6_all_fields.get('ipv6.addr')
						ipv6_tclass_ecn = ipv6_all_fields.get('ipv6.tclass.ecn')
						ipv6_flow = ipv6_all_fields.get('ipv6.flow')

					elif eth_type != None and eth_type != "0x00006002":
						print(eth_type)
						print(eth_content)
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


				# If packet is ipv4, update features
				if encapsulation_type=="1" and eth_type=="0x00000800":
					# Length src/dst features update
					if ipv4_src in HOST_IPS:
						# Packet from host to sensor
						if ipv4_dst in SENSOR_IPS:
							outF[0] = outF[0] + int(packet_length)
							outF[7] += 1
					elif ipv4_src in SENSOR_IPS:
						# Packet from sensor to host
						if ipv4_dst in HOST_IPS:
							outF[1] = outF[1] + int(packet_length)
							outF[8] += 1
						# Packet from sensor to sensor
						elif ipv4_dst in SENSOR_IPS:
							outF[14] = outF[1] + int(packet_length)
							outF[15] += 1
						# Packet from sensor to unknown IP
						else:
							outF[2] = outF[2] + int(packet_length)
							outF[9] += 1
							if ipv4_dst not in external_ips_dst:
								external_ips_dst.append(ipv4_dst)
								outF[12] += 1

							external_ip = IpDatabase.record_by_name(ipv4_dst)
							if external_ip != None:
								distance = geodesic(HOST_LOCATION, (external_ip["latitude"], external_ip["longitude"]))
								distance = distance._Distance__kilometers
								if distance>outF[22]:
									outF[22] = distance

					# Packet from unkown IP to sensor
					elif ipv4_dst in SENSOR_IPS:
						if ipv4_src not in external_ips_src:
							external_ips_src.append(ipv4_src)
							outF[13] += 1

							external_ip = IpDatabase.record_by_name(ipv4_src)
							if external_ip != None:
								distance = geodesic(HOST_LOCATION, (external_ip["latitude"], external_ip["longitude"]))
								distance = distance._Distance__kilometers
								if distance>outF[23]:
									outF[23] = distance


					if ipv4_protocol=='6': # If tcp, update features
						outF[4] += 1 # Count tcp packets
						if tcp_flags_syn != "0":
							outF[16] += int(tcp_flags_syn)
						if tcp_flags_ack != "0":
							outF[17] += int(tcp_flags_ack)
						if tcp_flags_fin != "0":
							outF[18] += int(tcp_flags_fin)
						if tcp_flags_urg != "0":
							outF[19] += int(tcp_flags_urg)
						if tcp_flags_push != "0":
							outF[20] += int(tcp_flags_push)
						if tcp_reset != "0":
							outF[21] += int(tcp_reset)

					elif ipv4_protocol=='17': # If udp, update features
						outF[5] += 1 # Count udp packets
					elif ipv4_protocol=='1':
						outF[11] += 1 # Count icmp packets
					else: # If other, update features
						outF[6] += 1 # Count other packets

				# If arp, update features
				if encapsulation_type=="1" and eth_type=="0x00000806":
					# Count arp packets
					outF[3] += 1

				# Count dns packets
				if len(layers)>3 and layers[3]._layer_name=='dns':
					outF[10] += 1

				# If the last ks is different from the ks, update the file
				# Clean features and repeat until the last ks is the same
				if last_ks != ks and packets_amount>0:
					while last_ks != ks:
						outF_len = len(outF)

						for i in range(outF_len):
							file_obj.write(str(outF[i])+' ')
							outF[i] = 0
						file_obj.write('\n')
						
						external_ips_dst = []
						external_ips_src = []
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


