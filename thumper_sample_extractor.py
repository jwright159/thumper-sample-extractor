"""Documentation: https://rainbowunicorn7297.github.io/"""

from io import BufferedReader, BytesIO
from os import listdir, makedirs
from fsb5 import FSB5
from typing import Callable, Set, Tuple
from os.path import join, dirname, exists
from numpy import uint32
from PIL import Image, UnidentifiedImageError

def hash32(f: str) -> str:
	"""A magic number is a 32-bit hash value produced by applying a hash function on a string or a byte array.
	Hash tables are maintained in the game executable mapping hash values to objects or string literals like game file paths,
	object types and parameter names. This is probably done to avoid expensive string operations such as comparisons and creating new copies,
	and to allow fast lookup of objects using the hash value as the ID."""
	f = 'A' + f
	h = uint32(0x811c9dc5)
	for c in f:
		h = uint32(uint32(h ^ ord(c)) * 0x1000193)
	h = uint32(h * 0x2001)
	h = uint32(uint32(h ^ uint32(h >> 0x7)) * 0x9)
	h = uint32(uint32(h ^ uint32(h >> 0x11)) * 0x21)
	return hex(h)[2:]

magic_header_descriptors: dict[bytes, str] = {
	bytes.fromhex('4314a51b'): 'GFX',
	bytes.fromhex('484595b0'): 'Sequin',
	bytes.fromhex('19621c9d'): 'Obj',
	bytes.fromhex('9e4d370b'): 'Level',
	bytes.fromhex('4f6274e6'): 'Avatar',
	b'FSB5': 'Audio',
	b'DDS ': 'Texture',
}

def list_file_headers(file_name: str, pc: BufferedReader):
	pc.seek(0)
	pc_type = int.from_bytes(pc.read(4), 'little')
	pc_magic_header = pc.read(4)
	print(file_name, pc_type, magic_header_descriptors[pc_magic_header] if pc_magic_header in magic_header_descriptors else pc_magic_header)

def find_file_references(file_name: str, pc: BufferedReader, start_query: str, end_query: str):
	"""Takes a file and finds all references to other filepaths that start with `query` and end in `ext_query`"""
	start_query_bytes = start_query.encode()
	end_query_bytes = end_query.encode()

	pc.seek(0)
	pc_type = int.from_bytes(pc.read(4), 'little')
	pc_magic_header = pc.read(4)

	pc.seek(0)
	data = pc.read()
	barr = bytearray(data)
	path_index = barr.find(start_query_bytes)
	while path_index >= 0:
		ext_index = barr.index(end_query_bytes, path_index) + len(end_query_bytes)
		target_path_bytes = data[path_index:ext_index]
		try:
			target_path = target_path_bytes.decode()
			print(file_name, pc_type, pc_magic_header, magic_header_descriptors[pc_magic_header] if pc_magic_header in magic_header_descriptors else pc_magic_header, hex(path_index), target_path)
			yield target_path
		except UnicodeDecodeError:
			print(f'Could not decode {target_path_bytes}')
		finally:
			path_index = barr.find(start_query_bytes, ext_index)

Extractor = Callable[[BufferedReader, str, str | None], None]

def extract_mesh(pc: BufferedReader, cache_path: str, save_path: str | None):
	if save_path is None:
		save_path = join('extracted', 'meshes', f'{cache_path}.x')
	print(save_path)
	makedirs(dirname(save_path), exist_ok=True)
	with open(save_path, 'wb') as file:
		file.write(pc.read())

def extract_audio(pc: BufferedReader, cache_path: str, save_path: str | None):
	fsb = FSB5(pc.read())
	#print(f, fsb.header)
	
	ext = fsb.get_sample_extension()

	for sample in fsb.samples:
		if save_path is None:
			save_path = join('extracted', 'samples', f'{sample.name}.{ext}')
		else:
			save_path = save_path[:save_path.rindex('.')] + '.' + ext # it's ogg not wav
		#print(cache_path, save_path)

		makedirs(dirname(save_path), exist_ok=True)

		with open(save_path, 'wb') as sample_file:
			rebuilt_sample = fsb.rebuild_sample(sample)
			sample_file.write(rebuilt_sample)

def extract_texture(pc: BufferedReader, cache_path: str, save_path: str | None):
	if save_path is None:
		save_path = join('extracted', 'textures', f'{cache_path}.png')
	print(save_path)
	makedirs(dirname(save_path), exist_ok=True)
	try:
		texture = Image.open(BytesIO(pc.read()))
		texture.save(save_path)
	except UnidentifiedImageError:
		print(f'Could not load texture file {cache_path}')

file_type_extractors: dict[int, dict[bytes, Extractor | None] | Extractor | None] = {
	0: None,	# Scoring file. Defines the scoring rules, such as how many points are awarded for each type of action and no miss and no damage bonuses.
	4: None,	# Config files
	5: None,	# A list of UI menus, such as the main menu (Credits, Level Select, Leaderboards, Options) and in-game pause screen (Restart Checkpoint, Exit)
	6: extract_mesh,	# 3D mesh (stripped-down .x, DirectX file format) files and localization files
	8: { # Game object library (.objlib, custom format) files
		bytes.fromhex('4314a51b'): None,	# GFX library. Most .objlib files that do not fit into the other types are in this category, including .objlib files that contain UI objects, bosses, VFX, skyboxes, interactive visual objects, and decorative visual objects with simple animations.
		bytes.fromhex('484595b0'): None,	# Sequin library. These are .objlib files that contain decorative visual objects with complex animations that require more sequencing control.
		bytes.fromhex('19621c9d'): None,	# Obj library. These are .objlib files that control the audio aspect of the game, including channels and SFX, and VR playspace scale
		bytes.fromhex('9e4d370b'): None,	# Level library. These are .objlib files that control the sequence and timing of objects appearing in a level.
		bytes.fromhex('4f6274e6'): None,	# Avatar library. This is the .objlib file that control the appearance of the beetle and its reactions to input and obstacles.
	},
	9: None,	# Credits files and level config files
	12: None,	# Texture (.dds, DirectDraw Surface) files
	13: {
		b'FSB5': extract_audio,	# Audio sample (FSB5, FMOD Sample Bank) files
		b'DDS ': extract_texture,	# Texture (.dds, DirectDraw Surface) files
	},
	14: None,	# A list of levels (Level 1 – Level 9)
	28: None,	# Shader files
	93: None,	# Unknown
}
"""https://rainbowunicorn7297.github.io/#Overall%20Structure%20of%20Game%20Files"""

def extract_file(cache_path: str, pc: BufferedReader, file_type: int, magic_header: bytes | None = None, save_path: str | None = None):
	pc.seek(0)
	pc_file_type = int.from_bytes(pc.read(4), 'little')
	pc_magic_header = pc.read(4)
	if pc_file_type == file_type and (pc_magic_header == magic_header if magic_header else True):
		pc.seek(4) # Actual data starts here (includes magic header)

		if file_type not in file_type_extractors:
			print(f'File type {file_type} not understood')
		else:
			extractor_group = file_type_extractors[file_type]
			if extractor_group is None:
				print(f'No extractor created for file type {file_type}')
			elif isinstance(extractor_group, dict):
				if magic_header is None:
					print(f'No magic header supplied for file type {file_type} where one is needed')
				elif magic_header not in extractor_group:
					print(f'File type {file_type} with magic header {magic_header} not understood')
				else:
					extractor = extractor_group[magic_header]
					if extractor is None:
						print(f'No extractor created for file type {file_type} and magic header {magic_header}')
					else:
						extractor(pc, cache_path, save_path)
			else:
				extractor = extractor_group
				extractor(pc, cache_path, save_path)

def find_all_references_and_extract(description: str, start_query: str, end_query: str, file_type: int, magic_header: bytes | None = None):
	target_paths: Set[str] = set()

	files = [f for f in listdir() if f[-3:] == '.pc']
	for f in files:
		with open(f, 'rb') as pc:
			target_paths.update(find_file_references(f, pc, start_query, end_query))

	with open(f'{description} list.txt', 'w') as list_txt:
		list_txt.write('\n'.join(sorted(list(target_paths), key=str.casefold)))
	
	missing_caches: Set[Tuple[str, str]] = set()
	for target_path in target_paths:
		pc_path = hash32(target_path) + '.pc'

		if exists(pc_path):
			print(pc_path, target_path)
			with open(pc_path, 'rb') as pc:
				extract_file(pc_path, pc, file_type, magic_header, target_path)
		
		else:
			print(pc_path, target_path, 'not found!')
			missing_caches.add((pc_path, target_path))
	
	if missing_caches:
		with open(f'missing {description} caches.txt', 'w') as bad_cache_txt:
			bad_cache_txt.write('These cache files were not found!\n' + '\n'.join([f'{x[0]} {x[1]}' for x in sorted(list(missing_caches), key=lambda x: str.casefold(x[1]))]))

def attempt_extract_all(file_type: int, magic_header: bytes | None = None):
	files = [f for f in listdir() if f[-3:] == '.pc']
	for f in files:
		with open(f, 'rb') as pc:
			extract_file(f, pc, file_type, magic_header)

def list_all_file_headers():
	files = [f for f in listdir() if f[-3:] == '.pc']
	for f in files:
		with open(f, 'rb') as pc:
			list_file_headers(f, pc)

def main():
	list_all_file_headers()
	#find_all_references_and_extract('audio sample', 'samples/', '.wav', 13, b'FSB5')
	#find_all_references_and_extract('texture', 'fx/textures/', '.png', 13, b'DDS ')
	#attempt_extract_all(13, b'DDS ')
	#attempt_extract_all(6, 'xof ') #bytes.fromhex('01000000'))

if __name__ == '__main__':
	main()