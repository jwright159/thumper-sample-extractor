from io import BufferedReader
from typing import Any, Callable
import struct
import sys

DataObject = dict[str, Any]
DataList = list[DataObject]

def read_int(file: BufferedReader) -> int:
	return struct.unpack('<i', file.read(4))[0]

def read_short(file: BufferedReader) -> int:
	return struct.unpack('<h', file.read(4))[0]

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

def read_color(file: BufferedReader) -> tuple[float, float, float, float]:
	r = read_float(file)
	g = read_float(file)
	b = read_float(file)
	a = read_float(file)
	return (r, g, b, a)

def read_transform(file: BufferedReader) -> dict[str, tuple[float, float, float]]:
	position = read_vector(file)
	rotation_x = read_vector(file)
	rotation_y = read_vector(file)
	rotation_z = read_vector(file)
	scale = read_vector(file)
	return {
		'pos': position,
		'rot_x': rotation_x,
		'rot_y': rotation_y,
		'rot_z': rotation_z,
		'scale': scale,
	}

def read_file_path(file: BufferedReader) -> str | tuple[int, str]:
	root_index = read_int(file)
	file_path = read_string(file)
	return file_path if root_index == 0 else (root_index, file_path)

def read_animation_component(file: BufferedReader) -> DataObject:
	"""https://rainbowunicorn7297.github.io/#.leaf%20Objects"""
	animation_component_version_number = read_int(file)
	frame = read_float(file)
	unit_of_time = read_string(file)
	return {}

def read_edit_state_component(file: BufferedReader) -> DataObject:
	"""https://rainbowunicorn7297.github.io/#.leaf%20Objects"""
	return {}

def read_approach_animation_component(file: BufferedReader) -> DataObject:
	animation_component_version_number = read_int(file)
	frame = read_float(file)
	unit_of_time = read_string(file)
	approach_animation_component_version_number = read_int(file)
	num_approach_beats = read_int(file)
	return {
		'approach_beats': num_approach_beats
	}

def read_transform_component(file: BufferedReader) -> DataObject:
	"""https://rainbowunicorn7297.github.io/#.spn%20Objects"""
	transform_component_version_number = read_int(file)
	transform_parent_object_name = read_string(file)
	transform_constraint = read_string(file)
	transform = read_transform(file)
	return {
		'xfm_name': transform_parent_object_name,
		'constrainnt': transform_constraint,
		**transform,
	}

def read_draw_component(file: BufferedReader) -> DataObject:
	"""https://rainbowunicorn7297.github.io/#.mesh%20Objects"""
	draw_component_version_number = read_int(file)
	is_visible = read_bool(file)
	draw_layer = read_string(file)
	render_bucket = read_string(file)
	num_draw_children = read_int(file)
	for _ in range(num_draw_children):
		draw_child_name = read_string(file)

component_readers = {
	'63259f0a': read_animation_component,
	'3c8efb12': read_edit_state_component,
	'6c2d3373': read_approach_animation_component,
	'84e761eb': read_transform_component,
	'f92719ee': read_draw_component,
}
def read_component(file: BufferedReader) -> DataObject:
	component_marker = read_hash(file)
	component_reader = component_readers[component_marker]
	return component_reader(file)

def read_components(file: BufferedReader) -> DataList:
	num_components = read_int(file)
	components: DataList = []
	for _ in range(num_components):
		component = read_component(file)
		components.append(component)
	return components

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
	read_color,
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
	if data_point_reader is None:
		raise TypeError(f'No data point reader for trait type {trait_type}')
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
def read_sequencer_object(file: BufferedReader) -> DataObject:
	"""https://rainbowunicorn7297.github.io/#.leaf%20Objects and https://rainbowunicorn7297.github.io/#Sequencer%20Objects"""
	object_name = read_string(file)
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
	unused_4 = read_color(file)
	intensity_scale = read_bool(file)
	unused_5 = read_bool(file)
	unknown = read_bool(file)
	return {
		'obj_name': object_name,
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

def read_sequencer_objects(file: BufferedReader) -> DataList:
	"""https://rainbowunicorn7297.github.io/#.leaf%20Objects"""
	num_sequencer_objects = read_int(file)
	sequencer_objects: DataList = []
	for _ in range(num_sequencer_objects):
		sequencer_object_component = read_sequencer_object(file)
		sequencer_objects.append(sequencer_object_component)
	return sequencer_objects

def read_leaf(file: BufferedReader, name: str) -> DataObject:
	"""https://rainbowunicorn7297.github.io/#.leaf%20Objects"""
	sequin_leaf_version_number = read_int(file)
	trait_anim_version_number = read_int(file)
	obj_version_number = read_int(file)
	components = read_components(file)
	sequencer_objects = read_sequencer_objects(file)
	num_beats = read_int(file)
	path_phase = read_float(file)
	tile_phase = read_float(file)
	for _ in range(num_beats):
		unused = read_vector(file)
	turn_lane_offset = read_int(file)
	return {
		'obj_type': 'SequinLeaf',
		'obj_name': name,
		'seq_objs': sequencer_objects,
		'beat_cnt': num_beats,
	}

def read_global_library(file: BufferedReader) -> DataObject:
	unknown = read_int(file)
	library_name = read_string(file)
	return {}

def read_global_libraries(file: BufferedReader) -> DataList:
	num_global_libraries = read_int(file)
	global_libraries: DataList = []
	for _ in range(num_global_libraries):
		global_library = read_global_library(file)
		global_libraries.append(global_library)
	return global_libraries

def read_level_external_object(file: BufferedReader) -> DataObject:
	object_type = read_hash(file)
	object_name = read_string(file)
	unknown = read_int(file)
	return {}

def read_level_external_objects(file: BufferedReader) -> DataList:
	num_external_objects = read_int(file)
	external_objects: DataList = []
	for _ in range(num_external_objects):
		external_object = read_level_external_object(file)
		external_objects.append(external_object)
	return external_objects

def read_lvl_grouping(file: BufferedReader) -> DataObject:
	lvl_object_name = read_string(file)
	gate_object_name = read_string(file)
	has_checkpoint = read_bool(file)
	checkpoint_leader_lvl_object_name = read_string(file)
	rest_lvl_object_name = read_string(file)
	unknown_1 = read_bool(file)
	unknown_2 = read_bool(file)
	unknown_3 = read_int(file)
	unknown_4 = read_bool(file)
	is_in_play_plus = read_bool(file)
	return {
		'lvl_name': lvl_object_name,
		'gate_name': gate_object_name,
		'checkpoint': has_checkpoint,
		'checkpoint_leader_lvl_name': checkpoint_leader_lvl_object_name,
		'rest_lvl_name': rest_lvl_object_name,
		'play_plus': is_in_play_plus,
	}

def read_lvl_groupings(file: BufferedReader) -> DataList:
	num_lvl_groupings = read_int(file)
	lvl_groupings: DataList = []
	for _ in range(num_lvl_groupings):
		lvl_grouping = read_lvl_grouping(file)
		lvl_groupings.append(lvl_grouping)
	return lvl_groupings

def read_master(file: BufferedReader, name: str) -> DataObject:
	sequin_master_version_number = read_int(file)
	sequencer_objects_version_number = read_int(file)
	obj_version_number = read_int(file)
	components = read_components(file)
	sequencer_objects = read_sequencer_objects(file)
	min_end_frame = read_float(file)
	skybox_object_name = read_string(file)
	intro_lvl_obj_name = read_string(file)
	lvl_groupings = read_lvl_groupings(file)
	unknown_1 = read_bool(file)
	unknown_2 = read_bool(file)
	unknown_3 = read_int(file)
	unknown_4 = read_int(file)
	unknown_5 = read_int(file)
	unknown_6 = read_int(file)
	unknown_7 = read_vector(file)
	checkpoint_lvl_object_name = read_string(file)
	unknown_8 = read_string(file)
	return {
		'obj_type': 'SequinMaster',
		'obj_name': name,
		'skybox_name': 'skybox_cube', # FIXME: can't set skybox name from here
		'intro_lvl_name': intro_lvl_obj_name,
		'groupings': lvl_groupings,
		'checkpoint_lvl_name': checkpoint_lvl_object_name,
	}

def read_step(file: BufferedReader) -> DataObject:
	unknown_1 = read_string(file)
	if not unknown_1:
		num_beats = read_int(file)
		should_skip_sequin = read_bool(file)
		if not should_skip_sequin:
			sequin = read_string(file)
		unknown_2 = read_string(file)
		num_sub_paths = read_int(file)
		sub_paths = []
		for _ in range(num_sub_paths):
			unknown_3 = read_string(file)
			unknown_4 = read_string(file)
			sub_paths.append([unknown_3, unknown_4]) # FIXME: this is probably wrong
	step_type = read_string(file)
	offset_between_current_and_prev_step = read_int(file)
	transform = read_transform(file)
	unknown_5 = read_bool(file)
	unknown_6 = read_bool(file)
	return {
		'beat_cnt': num_beats,
		'leaf_name': sequin,
		'main_path': unknown_2,
		'sub_paths': sub_paths,
		**transform,
	}

def read_steps(file: BufferedReader) -> DataList:
	steps: DataList = []
	while read_bool(file):
		step = read_step(file)
		steps.append(step)
	return steps

def read_loop(file: BufferedReader) -> DataObject:
	samp_object_name = read_string(file)
	num_beats_per_loop = read_int(file)
	ch_object_name = read_int(file)
	return {
		'samp_name': samp_object_name,
		'beats_per_loop': num_beats_per_loop,
	}

def read_loops(file: BufferedReader) -> DataList:
	num_loops = read_int(file)
	loops: DataList = []
	for _ in range(num_loops):
		loop = read_loop(file)
		loops.append(loop)
	return loops

def read_lvl(file: BufferedReader, name: str) -> DataObject:
	"""https://rainbowunicorn7297.github.io/#.lvl%20Objects"""
	sequin_lvl_version_number = read_int(file)
	sequencer_objects_version_number = read_int(file)
	obj_version_number = read_int(file)
	[approach_animation_component, edit_state_component] = read_components(file)
	sequencer_objects = read_sequencer_objects(file)
	min_end_frame = read_float(file)
	move_type = read_string(file)
	move_sequin = read_string(file)
	steps = read_steps(file)
	loops = read_loops(file)
	unknown_1 = read_bool(file)
	volume = read_float(file)
	start_flow = read_string(file)
	start_flow_trait_path = read_trait_path(file)
	start_flow_trait_type = read_string(file)
	is_input_allowed = read_bool(file)
	tutorial_type = read_string(file)
	start_angle_fracs = read_vector(file)
	return {
		'obj_type': 'SequinLevel',
		'obj_name': name,
		**approach_animation_component,
		'seq_objs': sequencer_objects,
		'leaf_seq': steps,
		'loops': loops,
		'volume': volume,
		'input_allowed': is_input_allowed,
		'tutorial_type': tutorial_type,
		'start_angle_fracs': start_angle_fracs
	}

def read_boss_pattern(file: BufferedReader) -> DataObject:
	gate_level_script_node = read_hash(file)
	boss_pattern_lvl_object_name = read_string(file)
	unknown_1 = read_bool(file)
	gate_sentry_type = read_string(file)
	unknown_2 = read_float(file)
	bucket_num = read_int(file)
	return {}

def read_boss_patterns(file: BufferedReader) -> DataList:
	num_boss_patterns = read_int(file)
	boss_patterns: DataList = []
	for _ in range(num_boss_patterns):
		boss_pattern = read_boss_pattern(file)
		boss_patterns.append(boss_pattern)
	return boss_patterns

def read_gate(file: BufferedReader, name: str) -> DataObject:
	"""https://rainbowunicorn7297.github.io/#.gate%20Objects"""
	sequin_gate_version_number = read_int(file)
	obj_version_number = read_int(file)
	components = read_components(file)
	spn_obj_name = read_string(file)
	ent_trait_path = read_trait_path(file)
	boss_patterns = read_boss_patterns(file)
	pre_boss_lvl_object_name = read_string(file)
	post_boss_lvl_object_name = read_string(file)
	restart_lvl_obj_name = read_string(file)
	unknown_1 = read_string(file)
	component_type = read_string(file)
	unknown_2 = read_float(file)
	level_random_type = read_string(file)
	return {} # TODO: this has no matching file

def read_samp(file: BufferedReader, name: str) -> DataObject:
	"""https://rainbowunicorn7297.github.io/#.samp%20Objects"""
	sample_version_number = read_int(file)
	obj_version_number = read_int(file)
	components = read_components(file)
	sample_play_mode = read_string(file)
	file_path = read_file_path(file)
	should_stream = read_bool(file)
	loop_count = read_int(file)
	volume = read_float(file)
	pitch = read_float(file)
	pan = read_float(file)
	offset = read_float(file)
	channel_group = read_string(file)
	return {
		'items': [
			{
				'obj_type': 'Sample',
				'obj_name': name,
				'mode': sample_play_mode,
				'path': file_path,
				'volume': volume,
				'pitch': pitch,
				'pan': pan,
				'offset': offset,
				'channel_group': channel_group
			}
		]
	}

def read_spn(file: BufferedReader, name: str) -> DataObject:
	"""https://rainbowunicorn7297.github.io/#.spn%20Objects"""
	entity_spawner_version_number = read_int(file)
	obj_version_number = read_int(file)
	[edit_state_component, transform_component] = read_components(file)
	entity_objlib_file_path = read_file_path(file)
	render_bucket = read_string(file)
	return {
		'items': [
			{
				'obj_type': 'EntitySpawner',
				'obj_name': name,
				**transform_component,
				'objlib_path': entity_objlib_file_path,
				'bucket': render_bucket,
			}
		]
	}

def read_tex(file: BufferedReader, name: str) -> DataObject:
	"""https://rainbowunicorn7297.github.io/#.tex%20Objects"""
	tex_2d_version_number = read_int(file)
	obj_version_number = read_int(file)
	components = read_components(file)
	compression = read_string(file)
	has_mips = read_bool(file)
	file_path = read_file_path(file)
	return {} # TODO: this has no matching file

def read_mat(file: BufferedReader, name: str) -> DataObject:
	"""https://rainbowunicorn7297.github.io/#.mat%20Objects"""
	mat_version_number = read_int(file)
	obj_version_number = read_int(file)
	components = read_components(file)
	decal_map = read_string(file)
	emissive_map = read_string(file)
	reflection_map = read_string(file)
	blending = read_string(file)
	material_lighting = read_int(file)
	cull_mode = read_string(file)
	z_mode = read_string(file)
	unknown_1 = read_bool(file)
	unknown_2 = read_bool(file)
	material_filtering = read_string(file)
	emissive_color = read_color(file)
	ambient_color = read_color(file)
	diffuse_color = read_color(file)
	specular_color = read_color(file)
	reflectivity_color = read_color(file)
	alpha = read_float(file)
	unknown_3 = read_float(file)
	specular_map = read_string(file)
	texture_transform_mode = read_string(file)
	texture_transform = read_transform(file)
	unknown_4 = read_float(file)
	should_disable_noise_vignette_when_low_spec_rendering_used = read_bool(file)
	noise_vignette_object_name = read_string(file)
	unknown_5 = read_bool(file)
	return {} # TODO: this has no matching file

def read_mesh(file: BufferedReader, name: str) -> DataObject:
	"""https://rainbowunicorn7297.github.io/#.mesh%20Objects"""
	mesh_version_number = read_int(file)
	obj_version_number = read_int(file)
	components = read_components(file)
	mat_object_name = read_string(file)
	is_mesh_data_defined_in_object = read_string(file)
	if is_mesh_data_defined_in_object:
		num_vertices = read_int(file)
		for _ in range(num_vertices):
			vertex_position = read_vector(file)
			vertex_normal = read_vector(file)
			vertex_uvw = read_vector(file)
		num_faces = read_int(file)
		for _ in range(num_faces):
			vertex_index_1 = read_short(file)
			vertex_index_2 = read_short(file)
			vertex_index_3 = read_short(file)
		unknown_1 = read_bool(file)
		unknown_2 = read_bool(file)
	else:
		file_path = read_file_path(file)
		cache_name_param_1 = read_int(file)
		cache_name_param_2 = read_int(file)
		cache_name_param_3 = read_int(file)
		cache_name_param_4 = read_bool(file)
		cache_name_param_5 = read_int(file)
	return {} # TODO: this has no matching file

def read_path(file: BufferedReader, name: str) -> DataObject:
	path_version_number = read_int(file)
	obj_version_number = read_int(file)
	components = read_components(file)
	tile_scale = read_vector(file)
	tile_size = read_vector(file)
	lane_spacing = read_float(file)
	mesh_object_name = read_string(file)
	does_bend = read_bool(file)
	bend_scale_interpolation_method = read_string(file)
	does_pulse_color = read_bool(file)
	does_pulse_scale = read_bool(file)
	v_scale = read_float(file)
	num_path_decorators = read_int(file)
	for _ in range(num_path_decorators):
		path_decorator_name = read_string(file)
	is_visible = read_bool(file)
	return {} # TODO: this has no matching file

level_object_readers: dict[str, Callable[[BufferedReader, str], Any]] = {
	'ce7e85f6': read_leaf,
	'490780b9': read_master,
	'd3058b5d': read_drawer,
	'7aa8f390': read_samp,
	'bcd17473': read_lvl,
	'd897d5db': read_spn,
	'7d9db5ef': read_xfm,
	'5232f8f9': read_anim,
	'bf69f115': read_mesh,
	'4890a3f6': read_path,
	'7ba5c8e0': read_mat,
	'86621b1e': read_flow,
	'aa63a508': read_gate,
	'3bbcc4ec': read_env,
	'96ba8a70': read_tex,
}
def read_level_object_declaration(file: BufferedReader) -> tuple[str, Callable[[BufferedReader, str], Any]]:
	object_name = read_string(file)
	object_type = read_hash(file)
	object_reader = level_object_readers[object_type]
	return (object_name, object_reader)

def read_level_object_declarations(file: BufferedReader) -> list[tuple[str, Callable[[BufferedReader, str], Any]]]:
	num_objects = read_int(file)
	object_declarations: list[tuple[str, Callable[[BufferedReader, str], Any]]] = []
	for _ in range(num_objects):
		object_declaration = read_level_object_declaration(file)
		object_declarations.append(object_declaration)
	return object_declarations

def read_level_objlib(file: BufferedReader):
	unknown_1 = read_int(file)
	unknown_2 = read_int(file)
	unknown_3 = read_int(file)
	unknown_4 = read_int(file)
	global_libraries = read_global_libraries(file)
	original_file_path = read_string(file)
	external_objects = read_level_external_objects(file)
	object_declarations = read_level_object_declarations(file)
	for object_declaration in object_declarations:
		object = object_declaration[1](file, object_declaration[0])

objlib_readers = {
	'0b374d9e': read_level_objlib
}
def read_objlib_file(file: BufferedReader):
	objlib_type = read_hash(file)
	objlib_reader = objlib_readers[objlib_type]
	return objlib_reader(file)

file_readers = {
	8: read_objlib_file
}
def read_file(file: BufferedReader):
	file_type = read_int(file)
	file_reader = file_readers[file_type]
	return file_reader(file)

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