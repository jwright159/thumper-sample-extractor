import sys

read_filename = sys.argv[1] #'5a82f017.pc'
write_filename = sys.argv[2] #'sample_leaf.leaf'
start_byte = int(sys.argv[3], 0) #0x00034d36
end_byte = int(sys.argv[4], 0) #0x00036833

with open(read_filename, 'rb') as read_file:
	read_file.seek(start_byte)
	data = read_file.read(end_byte - start_byte)

with open(write_filename, 'w+b') as write_file:
	write_file.write(data)