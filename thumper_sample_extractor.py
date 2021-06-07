from io import BufferedReader
from os import listdir, makedirs
from fsb5 import FSB5
from typing import Set, Tuple
from os.path import join, dirname, exists
from numpy import uint32

def hash32(f: str) -> str:
	f = 'A' + f
	h = uint32(0x811c9dc5)
	for c in f:
		h = uint32(uint32(h ^ ord(c)) * 0x1000193)
	h = uint32(h * 0x2001)
	h = uint32(uint32(h ^ uint32(h >> 0x7)) * 0x9)
	h = uint32(uint32(h ^ uint32(h >> 0x11)) * 0x21)
	return hex(h)[2:]

sample_set: Set[str] = set()
query = b'samples'
ext_query = b'.wav'
def get_sample_list(file_name: str, pc: BufferedReader):
	pc.seek(0)

	data = pc.read()
	barr = bytearray(data)
	path_index = barr.find(query)
	while path_index >= 0:
		ext_index = barr.index(ext_query, path_index)
		file_type = int.from_bytes(data[:4], 'little')
		obj_type = data[4:8].hex()
		obj_type = \
			'gfx' if obj_type == '4314a51b' else \
			'seq' if obj_type == '484595b0' else \
			'obj' if obj_type == '19621c9d' else \
			'lev' if obj_type == '9e4d370b' else \
			'ava' if obj_type == '4f6274e6' else \
			obj_type
		sample_path = data[path_index:ext_index+4].decode()

		print(file_name, file_type, obj_type, hex(path_index), sample_path)
		sample_set.add(sample_path)

		path_index = barr.find(query, ext_index)

def get_sample(cache_path: str, pc: BufferedReader, save_path: str = ''):
	pc.seek(0)

	# we want type 13, or "Audio sample (FSB5, FMOD Sample Bank) files and texture (.dds, DirectDraw Surface) files"
	pc_type = int.from_bytes(pc.read(4), 'little')
	pc_magic_header = pc.read(4) # Gonna be "FSB5" or "DDS "
	if pc_type == 13 and pc_magic_header == b'FSB5':

		pc.seek(4) # Actual data starts here
		
		fsb = FSB5(pc.read())
		#print(f, fsb.header)
		
		ext = fsb.get_sample_extension()

		for sample in fsb.samples:
			if save_path:
				save_path = save_path[:save_path.rindex('.')] + '.' + ext # it's ogg not wav
			else:
				save_path = join('samples', f"{sample.name}.{ext}")
			#print(cache_path, save_path)

			makedirs(dirname(save_path), exist_ok=True)

			with open(save_path, 'wb') as sample_file:
				rebuilt_sample = fsb.rebuild_sample(sample)
				sample_file.write(rebuilt_sample)


if __name__ == '__main__':

	files = [f for f in listdir() if f[-3:] == '.pc']
	for f in files:
		with open(f, 'rb') as pc:
			get_sample_list(f, pc)
			#get_sample(f, pc)

	if sample_set:
		with open('sample_list.txt', 'w') as sample_txt:
			sample_txt.write('\n'.join(sorted(list(sample_set), key=str.casefold)))
		
		bad_caches: Set[Tuple[str, str]] = set()
		for sample_path in sample_set:
			pc_path = hash32(sample_path) + '.pc'
			print(pc_path, sample_path, end='')

			if exists(pc_path):
				print()
				with open(pc_path, 'rb') as pc:
					get_sample(pc_path, pc, sample_path)
			
			else:
				print(" not found!")
				bad_caches.add((pc_path, sample_path))
		
		if bad_caches:
			with open('missing_caches.txt', 'w') as bad_cache_txt:
				bad_cache_txt.write("These cache files were not found!\n" + '\n'.join([f"{x[0]} {x[1]}" for x in sorted(list(bad_caches), key=lambda x: str.casefold(x[1]))]))