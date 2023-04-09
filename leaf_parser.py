from io import BufferedReader
from typing import Any
import struct
import sys

def read_int(file: BufferedReader) -> int:
	return struct.unpack('<i', file.read(4))[0]

def read_float(file: BufferedReader) -> float:
	return struct.unpack('<f', file.read(4))[0]

def read_bool(file: BufferedReader) -> bool:
	return struct.unpack('<?', file.read(1))[0]

def read_string(file: BufferedReader) -> str:
	size = read_int(file)
	return file.read(size).decode()

def read_hash(file: BufferedReader) -> str:
	hash_big_endian = file.read(4)
	hash_little_endian = bytes(reversed(hash_big_endian))
	return hash_little_endian.hex()

def read_vector(file: BufferedReader) -> tuple[float, float, float]:
	x = read_float(file)
	y = read_float(file)
	z = read_float(file)
	return (x, y, z)

def read_rgba(file: BufferedReader) -> tuple[float, float, float, float]:
	r = read_float(file)
	g = read_float(file)
	b = read_float(file)
	a = read_float(file)
	return (r, g, b, a)

def read_animation_component_section(file: BufferedReader) -> dict[str, Any]:
	"""https://rainbowunicorn7297.github.io/#.leaf%20Objects"""
	animation_component_version_number = read_int(file)
	frame = read_float(file)
	unit_of_time = read_string(file)
	return {}

def read_edit_state_component_section(file: BufferedReader) -> dict[str, Any]:
	"""https://rainbowunicorn7297.github.io/#.leaf%20Objects"""
	return {}

section_readers = {
	'63259f0a': read_animation_component_section,
	'3c8efb12': read_edit_state_component_section,
}
def read_section(file: BufferedReader) -> dict[str, Any]:
	section_marker = read_hash(file)
	section_reader = section_readers[section_marker]
	return section_reader(file)

def read_sections(file: BufferedReader) -> list[dict[str, Any]]:
	num_sections = read_int(file)
	sections: list[dict[str, Any]] = []
	for _ in range(num_sections):
		section = read_section(file)
		sections.append(section)
	return sections

def read_trait_path(file: BufferedReader) -> list[str | tuple[str, int]]:
	"""https://rainbowunicorn7297.github.io/#TraitPath"""
	num_sub_levels = read_int(file)
	sub_levels: list[str | tuple[str, int]] = []
	for _ in range(num_sub_levels):
		member = read_hash(file)
		member_index = read_int(file)
		sub_levels.append(member if member_index == -1 else (member, member_index))
	return sub_levels

data_point_readers = [
	read_int,
	read_bool,
	read_float,
	read_rgba,
	None,
	None,
	None,
	None,
	read_bool,
	None,
	None,
	None,
	None,
	None,
	None,
	None,
	None,
	None,
	None,
	None,
]
def read_data_point(file: BufferedReader, trait_type: int) -> tuple[float, Any]:
	"""https://rainbowunicorn7297.github.io/#Data%20Point%20Types"""
	data_point_reader = data_point_readers[trait_type]
	time = read_float(file)
	data_point = data_point_reader(file)
	interpolation_method = read_string(file)
	easing_method = read_string(file)
	return (time, data_point)

def read_data_points(file: BufferedReader, trait_type: int):
	num_data_points = read_int(file)
	data_points: dict[float, float | tuple[float, float, float, float]] = {}
	for _ in range(num_data_points):
		data_point = read_data_point(file, trait_type)
		data_points[data_point[0]] = data_point[1]
	return data_points

trait_type_names = [
	'kTraitInt',
	'kTraitBool',
	'kTraitFloat',
	'kTraitColor',
	'kTraitObj',
	'kTraitVec3',
	'kTraitPath',
	'kTraitEnum',
	'kTraitAction',
	'kTraitObjVec',
	'kTraitString',
	'kTraitCue',
	'kTraitEvent',
	'kTraitSym',
	'kTraitList',
	'kTraitTraitPath',
	'kTraitQuat',
	'kTraitChildLib',
	'kTraitComponent',
	'kNumTraitTypes',
]
def read_sequencer_object(file: BufferedReader) -> dict[str, Any]:
	"""https://rainbowunicorn7297.github.io/#Sequencer%20Objects"""
	trait_path = read_trait_path(file)
	trait_type = read_int(file)
	data_points = read_data_points(file, trait_type)
	ui_elements = read_data_points(file, trait_type)
	line_animation_type = read_int(file)
	default_trait_interpolation_method = read_int(file)
	default_trait_easing_method = read_int(file)
	unused_1 = read_int(file)
	unused_2 = read_int(file)
	intensity_operation_1 = read_string(file)
	intensity_operation_2 = read_string(file)
	has_intensity_phase = read_bool(file)
	trait_setter_op = read_bool(file)
	step_frequency = read_int(file)
	unused_3 = read_float(file)
	unused_4 = read_rgba(file)
	intensity_scale = read_bool(file)
	unused_5 = read_bool(file)
	return {
		'param_path': trait_path[0],
		'trait_type': trait_type_names[trait_type],
		'data_points': data_points,
		'step': 'False',
		'footer': [
			line_animation_type,
			default_trait_easing_method,
			default_trait_interpolation_method,
			unused_1,
			unused_2,
			intensity_operation_1,
			intensity_operation_2,
			int(has_intensity_phase),
			int(trait_setter_op),
			step_frequency,
			unused_3,
			*unused_4,
			int(intensity_scale),
			int(unused_5),
		]
	}

def read_trait_animation_sequencer_object_section(file: BufferedReader) -> dict[str, Any]:
	"""https://rainbowunicorn7297.github.io/#.leaf%20Objects"""
	object_name = read_string(file)
	sequencer_object = read_sequencer_object(file)
	unknown = read_bool(file)
	return {
		'obj_name': object_name,
		**sequencer_object
	}

def read_trait_animation(file: BufferedReader) -> list[dict[str, Any]]:
	"""https://rainbowunicorn7297.github.io/#.leaf%20Objects"""
	num_sequencer_objects = read_int(file)
	sequencer_objects: list[dict[str, Any]] = []
	for _ in range(num_sequencer_objects):
		sequencer_object_section = read_trait_animation_sequencer_object_section(file)
		sequencer_objects.append(sequencer_object_section)
	return sequencer_objects

def read_leaf(file: BufferedReader, name: str) -> dict[str, Any]:
	"""https://rainbowunicorn7297.github.io/#.leaf%20Objects"""
	sequin_leaf_version_number = read_int(file)
	trait_anim_version_number = read_int(file)
	obj_version_number = read_int(file)
	sections = read_sections(file)
	trait_animation = read_trait_animation(file)
	num_beats = read_int(file)
	path_phase = read_float(file)
	tile_phase = read_float(file)
	for _ in range(num_beats):
		unused = read_vector(file)
	turn_lane_offset = read_int(file)
	return {
		'obj_type': 'SequinLeaf',
		'obj_name': name,
		'seq_objs': trait_animation,
		'beat_cnt': num_beats,
	}

def format_fake_json(data: Any, indent: int = 0) -> str:
	indents = indent * '\t'
	inner_indents = (indent + 1) * '\t'
	if isinstance(data, dict):
		return '{' + ''.join('\n' + inner_indents + format_fake_json(key, indent + 1) + ': ' + format_fake_json(value, indent + 1) + ',' for key, value in data.items()) + '\n' + indents + '}'
	elif isinstance(data, list):
		return '[' + ''.join('\n' + inner_indents + format_fake_json(item, indent + 1) + ',' for item in data) + '\n' + indents + ']'
	elif isinstance(data, int):
		return str(data)
	elif isinstance(data, float):
		return str(int(data)) if data.is_integer() else str(data)
	elif isinstance(data, str):
		return '\'' + data + '\''
	else:
		raise TypeError('Unknown type to format ' + str(type(data)))

def main():
	leaf_path = sys.argv[1] #'sample_leaf.txt'
	leaf_name = leaf_path[:leaf_path.rindex('.')]
	with open(leaf_path, 'rb') as leaf_file:
		leaf = read_leaf(leaf_file, leaf_path)
	
	leaf_save_path = f'leaf_{leaf_name}.txt'
	with open(leaf_save_path, 'w+') as leaf_file:
		leaf_file.write(format_fake_json(leaf))

if __name__ == '__main__':
	main()