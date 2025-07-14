# Support for power loss recovery on klipper based 3d printers
#
# Copyright (C) 2025  Ankur Verma <ankurver@gmail.com>
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import logging
import json
import os
from collections import deque
from typing import Dict, Any, Optional, Tuple, Deque

def load_config(config):
	return PowerLossRecovery(config)

class PowerLossRecovery:
	
	def _parse_gcode_config_option(self, config, option_name, default=''):
		"""
		Parse a G-code configuration option, handling multi-line commands.
		
		Args:
			config: Klipper config object
			option_name: Name of the config option to parse
			default: Default value if option is not found
		
		Returns:
			tuple: (raw_string, parsed_lines_list)
		"""
		try:
			# Get raw string from config
			raw_value = config.get(option_name, default)
			
			# Parse into lines, filtering empty ones
			lines = [line.strip() for line in raw_value.split('\n') if line.strip()]
			
			if self.debug_mode:
				logging.info(f"PowerLossRecovery: Parsed {option_name}: {len(lines)} lines")
				if lines:
					logging.info(f"First line example: {lines[0]}")
				
			return raw_value, lines
			
		except Exception as e:
			raise config.error(f"Error parsing {option_name}: {str(e)}")
			
	def __init__(self, config):
		self.printer = config.get_printer()
		self.reactor = self.printer.get_reactor()
		
		# Get configuration values with proper error handling
		try:
			self.save_interval = config.getfloat('save_interval', 30., 
										   minval=0., maxval=300.)
			self.save_on_layer = config.getboolean('save_on_layer', True)
			self.variables_file = config.get('variables_file', 
										  '~/printer_state_vars.cfg')
			self.debug_mode = config.getboolean('debug_mode', False)
			self.resuming_print = False  # Flag to track PLR resume process
			
			# Get part cooling fans configuration
			self.part_cooling_fans = []
			fans_str = config.get('part_cooling_fans', '')
			if fans_str:
				self.part_cooling_fans = [fan.strip() for fan in fans_str.split(',') if fan.strip()]
				if self.debug_mode:
					logging.info(f"PowerLossRecovery: Configured part cooling fans: {self.part_cooling_fans}")
			
			# New configuration options for history
			self.history_size = config.getint('history_size', 5, minval=2, maxval=20)
			self.save_delay = config.getint('save_delay', 2, minval=0, 
										  maxval=self.history_size - 1)
			
			# Add probe iteration setting
			self.probe_iteration_count = config.getint('probe_iteration_count', 0, minval=0, maxval=10)
			if self.debug_mode:
				logging.info(f"PowerLossRecovery: Probe iteration count: {self.probe_iteration_count}")
				
			if self.debug_mode:
				logging.info("PowerLossRecovery: Debug mode enabled")
				logging.info(f"PowerLossRecovery: History size: {self.history_size}, Save delay: {self.save_delay}")
			
			try:
				# Dictionary mapping config names to attribute names
				gcode_configs = {
					'restart_gcode': ('restart_gcode', 'restart_gcode_lines'),
					'apply_offset_gcode': ('apply_offset_gcode', 'apply_offset_gcode_lines'),
					'before_resume_gcode': ('before_resume_gcode', 'before_resume_gcode_lines'),
					'after_resume_gcode': ('after_resume_gcode', 'after_resume_gcode_lines'),
					'before_calibrate_gcode': ('before_calibrate_gcode', 'before_calibrate_gcode_lines'),
					'after_calibrate_gcode': ('after_calibrate_gcode', 'after_calibrate_gcode_lines')
				}
				
				# Parse each config option
				for config_name, (raw_attr, lines_attr) in gcode_configs.items():
					raw_value, lines = self._parse_gcode_config_option(config, config_name)
					setattr(self, raw_attr, raw_value)
					setattr(self, lines_attr, lines)
					
					# Special handling for restart_gcode debug output
					if config_name == 'restart_gcode' and self.debug_mode and lines:
						logging.info(f"PowerLossRecovery: Found {len(lines)} restart G-code lines")
						for line in lines:
							logging.info(f"PowerLossRecovery: G-code line: {repr(line)}")
							
				if self.debug_mode:
					logging.info("PowerLossRecovery: Completed G-code configuration parsing")
					for config_name, (raw_attr, lines_attr) in gcode_configs.items():
						lines = getattr(self, lines_attr)
						logging.info(f"{config_name}: {len(lines)} lines parsed")
						
			except Exception as e:
				raise config.error(f"Error parsing G-code configurations: {str(e)}")

				
			# Important: Check if time-based saving is enabled
			self.time_based_enabled = self.save_interval > 0
			# Add tracking for cumulative layer height
			self.current_z_height = 0.

				
		except Exception as e:
			raise config.error(f"Error reading PowerLossRecovery config: {str(e)}")
		
		

		# Initialize state variables
		self.gcode = self.printer.lookup_object('gcode')
		self.save_variables = None
		self.toolhead = None
		self.extruder = None
		self.heater_bed = None
		self.last_layer = 0
		self.is_active = False
		self.last_save_time = 0
		# After other self.* initializations:
		self._last_layer_change_time = 0
		self._last_extruder_change_time = 0
		self._consecutive_failures = 0
		self._last_save_attempt = 0
		# Add with other state variables initialization
		self.power_loss_recovery_enabled = False  # Default to enabled
		
		# Initialize history queue
		self.state_history: Deque[Dict[str, Any]] = deque(maxlen=self.history_size)
		
		### Z-PLUS HOMING ####
		
		self.name = config.get_name()
		# Load config values
		self.position_endstop = config.getfloat('z_position', 0.)
		self.fast_move_speed = config.getfloat('fast_move_speed', 10.0, above=0.)
		self.slow_homing_speed = config.getfloat('slow_homing_speed', 2.0, above=0.)
		self.retract_dist = config.getfloat('retract_dist', 2.0, above=0.)
		self.max_adjustment = config.getfloat('max_adjustment', 5.0, above=0.)
		self.fast_travel_upto_z_height = config.getfloat('fast_travel_upto_z_height', 0., above=0.)
		self.fast_travel_speed = config.getfloat('fast_travel_speed', 50.0, above=0.)
		self.stepper_z_adjust_offset = config.getfloat('stepper_z_adjust_offset', 0.0)
		self.z_height_offset = config.getfloat('z_height_offset', 0.0)
		
		# Add adjustment offsets for all Z steppers
		self.stepper_adjust_offsets = {}
		self.stepper_adjust_offsets['stepper_z'] = config.getfloat('stepper_z_adjust_offset', 0.0)
		
		# Add configuration for additional steppers (z1, z2, z3)
		for i in range(1, 4):
			offset_name = f'stepper_z{i}_adjust_offset'
			try:
				self.stepper_adjust_offsets[f'stepper_z{i}'] = config.getfloat(offset_name, 0.0)
			except Exception:
				# If config option doesn't exist, default to 0
				self.stepper_adjust_offsets[f'stepper_z{i}'] = 0.0
				
		if self.debug_mode:
			for name, offset in self.stepper_adjust_offsets.items():
				if offset != 0:
					self._debug_log(f"{name} adjustment offset: {offset}")


		# Sample settings
		self.sample_count = config.getint('sample_size', 3, minval=1)
		self.sample_retract_dist = config.getfloat('sample_retract_dist', 2., above=0.)
		self.samples_tolerance = config.getfloat('samples_tolerance', 0.100, minval=0.)
		self.samples_retries = config.getint('samples_retry_count', 5, minval=0)
		self.samples_tolerance_retries = config.getint('samples_tolerance_retries', 3, minval=0)
		self.probe_samples_range = config.getfloat('probe_samples_range', 0.5, above=0.)
		self.halt_after_initial_probe = config.getboolean('halt_after_initial_probe', False)
		
		# Store pin config for each stepper
		self.pins = {}
		for i in range(4):
			pin_name = f'pin_stepper_z{i if i > 0 else ""}'
			try:
				self.pins[pin_name] = config.get(pin_name)
			except Exception:
				continue
				
		# Register save_variables support
		self.save_variables = None
		try:
			self.save_variables = self.printer.load_object(config, 'save_variables')
		except self.printer.config_error as e:
			raise self.printer.config_error(
				"save_variables module required for z_offset storage")
								  
		# Initialize lists
		self.endstops = []
		self.z_steppers = []
		self.stepper_names = []
		

		# Variables for storing results
		self.initial_trigger_position = None
		self.stepper_positions = {}
		
		# Variables for storing results
		self.z_positions = {}
		self.z_offsets = {}
		
		# Register event handlers
		self.printer.register_event_handler("klippy:connect", self._handle_connect)
		self.printer.register_event_handler("klippy:ready", self._handle_ready)
		self.printer.register_event_handler("extruder:activate_extruder",
										  self._handle_activate_extruder)
		self.printer.register_event_handler('klippy:mcu_identify',
										  self._handle_mcu_identify)
		# Add to the printer.register_event_handler section in __init__
		self.printer.register_event_handler("print_stats:complete", 
										  self._handle_print_complete)
		self.printer.register_event_handler("print_stats:error", 
										  self._handle_print_complete)
										  
		# Setup GCode commands
		self.gcode = self.printer.lookup_object('gcode')
		self.gcode.register_command('PLR_Z_HOME',
								  self.cmd_PLR_Z_HOME,
								  desc=self.cmd_PLR_Z_HOME_help)
		self.gcode.register_command('PLR_SAVE_PRINT_STATE', self.cmd_PLR_SAVE_PRINT_STATE,
								  desc=self.cmd_PLR_SAVE_PRINT_STATE_help)
		
		if self.save_on_layer:
			self.gcode.register_command('PLR_SAVE_PRINT_STATE_WITH_LAYER',
								  self._handle_layer_change,
								  desc="Layer change handler for PowerLossRecovery")
	
		self.gcode.register_command('PLR_QUERY_SAVED_STATE', 
								  self.cmd_PLR_QUERY_SAVED_STATE,
								  desc=self.cmd_PLR_QUERY_SAVED_STATE_help)
		
		self.gcode.register_command('PLR_RESET_PRINT_DATA',
								  self.cmd_PLR_RESET_PRINT_DATA,
								  desc=self.cmd_PLR_RESET_PRINT_DATA_help)

		# Add with other command registrations
		self.gcode.register_command('PLR_ENABLE', 
								  self.cmd_PLR_ENABLE,
								  desc=self.cmd_PLR_ENABLE_help)
		self.gcode.register_command('PLR_DISABLE',
								  self.cmd_PLR_DISABLE,
								  desc=self.cmd_PLR_DISABLE_help)
								  
		self.gcode.register_command('PLR_RESUME_PRINT', 
								self.cmd_PLR_RESUME_PRINT,
								desc=self.cmd_PLR_RESUME_PRINT_help)

		self.gcode.register_command('PLR_SAVE_MESH',
									  self.cmd_PLR_SAVE_MESH,
									  desc=self.cmd_PLR_SAVE_MESH_help)
		self.gcode.register_command('PLR_LOAD_MESH',
									  self.cmd_PLR_LOAD_MESH,
									  desc=self.cmd_PLR_LOAD_MESH_help)
									  
		self.gcode.register_command('PLR_TEST_APPLY_OFFSETS',
		  self.cmd_PLR_TEST_APPLY_OFFSETS,
		  desc=self.cmd_PLR_TEST_APPLY_OFFSETS_help)
									  
	### Z-PLUS HOMING #####
	
	
	def _handle_mcu_identify(self):
		# Get Z steppers via kinematics
		kin = self.printer.lookup_object('toolhead').get_kinematics()
		self.z_steppers = [s for s in kin.get_steppers() if s.is_active_axis('z')]
		
		if len(self.z_steppers) > len(self.pins):
			raise self.printer.config_error(
				"Missing endstop pins in config. Found %d Z steppers but only %d pins defined" 
				% (len(self.z_steppers), len(self.pins)))
		
		# Setup endstop for each Z stepper
		ppins = self.printer.lookup_object('pins')
		for i, stepper in enumerate(self.z_steppers):
			pin_name = f'pin_stepper_z{i if i > 0 else ""}'
			pin = self.pins[pin_name]
			ppins.allow_multi_use_pin(pin.replace('^', '').replace('!', ''))
			pin_params = ppins.lookup_pin(pin, can_invert=True, can_pullup=True)
			mcu = pin_params['chip']
			endstop = mcu.setup_pin('endstop', pin_params)
			self.endstops.append(endstop)
			self.stepper_names.append(stepper.get_name())
			endstop.add_stepper(stepper)
			
	def _load_saved_z_offsets(self):
		"""Load saved Z offsets from variables file"""
		if not self.save_variables:
			return {}
			
		loaded_offsets = {}
		try:
			# Get variables directly from save_variables status
			eventtime = self.printer.get_reactor().monotonic()
			variables = self.save_variables.get_status(eventtime)['variables']
			
			for name in self.stepper_names:
				var_name = f"z_offset_{name}"
				try:
					# Look directly in variables dictionary
					if var_name in variables:
						offset = float(variables[var_name])
						loaded_offsets[name] = offset
						if self.debug_mode:
							self._debug_log(f"Loaded offset for {name}: {offset:.3f}mm")
					else:
						if self.debug_mode:
							self._debug_log(f"No saved offset found for {name}")
				except Exception as e:
					if self.debug_mode:
						self._debug_log(f"Error loading offset for {name}: {str(e)}")
					continue
			
			if self.debug_mode:
				if loaded_offsets:
					self._debug_log("Successfully loaded offsets:")
					for name, offset in loaded_offsets.items():
						self._debug_log(f"{name}: {offset:.3f}mm")
				else:
					self._debug_log("No valid offsets found in variables file")
					
			return loaded_offsets
		
		except Exception as e:
			self._debug_log(f"Error loading saved offsets: {str(e)}")
			return {}
			
	def _save_z_offset(self, name, z_offset):
		"""Save Z offset to Klipper variables"""
		if not self.save_variables:
			return
		try:
			var_name = f"z_offset_{name}"
			save_cmd = self.gcode.create_gcode_command(
				"SAVE_VARIABLE", "SAVE_VARIABLE",
				{"VARIABLE": var_name, "VALUE": z_offset})
			self.save_variables.cmd_SAVE_VARIABLE(save_cmd)
		except Exception as e:
			raise self.printer.command_error(
				f"Error saving Z offset for {name}: {str(e)}")
	
		
	def _get_stepper_position_in_steps(self, stepper):
		"""Get the raw stepper position in microsteps"""
		try:
			# Get the stepper's mcu position
			mcu_pos = stepper.get_mcu_position()
			# Get steps per mm for this stepper
			steps_per_mm = stepper.get_step_dist()
			if steps_per_mm:
				return mcu_pos, (1.0 / steps_per_mm)
			return None, None
		except Exception as e:
			if self.debug_mode:
				self._debug_log(f"Error getting stepper position: {str(e)}")
			return None, None
	
	def _get_averaged_position(self, stepper, samples=5, delay=0.100):
		"""Get an averaged stepper position reading to reduce measurement noise."""
		positions = []
		for _ in range(samples):
			positions.append(stepper.get_mcu_position())
			self.toolhead.dwell(delay)
		return sum(positions) / len(positions)
	
	def _verify_movement_completion(self, stepper, tolerance=1):
		"""Verify that stepper movement has completely settled."""
		initial_pos = stepper.get_mcu_position()
		self.toolhead.dwell(0.250)
		final_pos = stepper.get_mcu_position()
		return abs(final_pos - initial_pos) < tolerance
	
	def _log_movement_stats(self, name, positions, trigger_times):
		"""Log statistical data about movement precision."""
		if len(positions) > 1:
			mean = sum(positions) / len(positions)
			variance = sum((x - mean) ** 2 for x in positions) / (len(positions) - 1)
			stats = {
				'mean': mean,
				'variance': variance,
				'min_time': min(trigger_times),
				'max_time': max(trigger_times)
			}
			if self.debug_mode:
				self._debug_log(f"{name} movement stats: {stats}")
	
	def _calculate_stepper_movement(self, stepper, start_pos, end_pos, steps_per_mm):
		"""Calculate actual movement distance based on stepper steps"""
		if None in (start_pos, end_pos, steps_per_mm):
			return None
		steps_moved = end_pos - start_pos
		return steps_moved / steps_per_mm
	
	def _probe_single_stepper(self, stepper, endstop, name, ref_z):
		"""
		Probe a single Z stepper with enhanced precision tracking and measurement
		
		Args:
			stepper: The stepper object to probe
			endstop: Associated endstop for this stepper
			name: Name of the stepper for logging
			ref_z: Reference Z height to return to between samples
		
		Returns:
			float: The calculated trigger height for this stepper
		"""
		# Enhanced initialization and position tracking
		toolhead = self.printer.lookup_object('toolhead')
		mcu = self.printer.lookup_object('mcu')
		
		# Flush motion queue and ensure stability
		print_time = toolhead.get_last_move_time()
		mcu.flush_moves(print_time, print_time)
		toolhead.wait_moves()
		
		# Increased dwell time for stability
		toolhead.dwell(1.000)
		
		# Debug logging
		if self.debug_mode:
			self._debug_log(f"\nStarting probe sequence for {name}")
			self._debug_log(f"Reference Z height: {ref_z}")
		
		# Verify movement stability before starting
		if not self._verify_movement_completion(stepper):
			raise self.printer.command_error(f"{name} movement not stable")
			
		# Get initial position with averaging
		initial_pos, steps_per_mm = self._get_stepper_position_in_steps(stepper)
		if initial_pos is None:
			raise self.printer.command_error(f"Unable to get initial position for {name}")
			
		if self.debug_mode:
			self._debug_log(f"{name} initial position: {initial_pos} steps")
			self._debug_log(f"Steps per mm: {steps_per_mm}")
			
		# Initialize statistics tracking
		position_samples = []
		trigger_times = []
		
		# Move up until endstop triggers - Initial probe
		try:
			probe_pos = list(toolhead.get_position())
			probe_pos[2] = self.position_endstop
			
			# Enhanced position recording with averaging
			pre_probe_pos = self._get_averaged_position(stepper)
			probe_start_time = self.reactor.monotonic()
			
			if self.debug_mode:
				self._debug_log(f"{name} averaged position before probe: {pre_probe_pos} steps")
			
			# Perform initial probe
			measured_pos = self.printer.lookup_object('homing').probing_move(
				endstop, probe_pos, self.fast_move_speed)
				
			# Record triggered position with averaging
			toolhead.dwell(0.100)  # Allow settling
			trigger_pos = self._get_averaged_position(stepper)
			trigger_time = self.reactor.monotonic()
			
			# Track positions and timing for statistics
			position_samples.append(trigger_pos)
			trigger_times.append(trigger_time - probe_start_time)
			
			# Calculate initial travel distance with enhanced precision
			initial_travel = self._calculate_stepper_movement(stepper, pre_probe_pos, trigger_pos, steps_per_mm)
			
			# Flush motion queue after probe
			print_time = toolhead.get_last_move_time()
			mcu.flush_moves(print_time, print_time)
			toolhead.wait_moves()
			
			if self.debug_mode:
				self._debug_log(f"{name} initial trigger position: {trigger_pos} steps")
				self._debug_log(f"Initial travel distance: {initial_travel:.3f}mm")
			
		except self.printer.command_error as e:
			msg = str(e)
			if "triggered prior to movement" in msg:
				raise self.printer.command_error(
					f"{name} endstop triggered before movement. Check Z position and endstop.")
			raise
		
		# Retract to sampling start position
		retract_pos = list(toolhead.get_position())
		retract_pos[2] -= self.sample_retract_dist
		toolhead.manual_move(retract_pos, self.fast_move_speed)
		toolhead.wait_moves()
		
		# Get position after retraction - this becomes our base position
		base_pos = self._get_averaged_position(stepper)
		if self.debug_mode:
			self._debug_log(f"{name} base position for sampling: {base_pos} steps")
		
		# Collect samples of total travel distance
		samples = []
		retry_count = 0
		
		while len(samples) < self.sample_count:
			if retry_count >= self.samples_retries:
				raise self.printer.command_error(
					f"Unable to get consistent samples for {name} after {retry_count} retries")
			
			try:
				# Move to probing start position
				probe_start_pos = list(toolhead.get_position())
				probe_start_pos[2] = measured_pos[2] - self.sample_retract_dist
				toolhead.manual_move(probe_start_pos, self.slow_homing_speed)
				toolhead.wait_moves()
				
				# Enhanced position recording for samples
				if not self._verify_movement_completion(stepper):
					if self.debug_mode:
						self._debug_log(f"Movement not stable before sample {len(samples) + 1}")
					continue
					
				pre_sample_pos = self._get_averaged_position(stepper)
				sample_start_time = self.reactor.monotonic()
				
				if self.debug_mode:
					self._debug_log(f"\nSample {len(samples) + 1}:")
					self._debug_log(f"Starting position: {pre_sample_pos} steps")
				
				# Perform sample probe
				sample_pos = self.printer.lookup_object('homing').probing_move(
					endstop, probe_pos, self.slow_homing_speed)
				
				# Enhanced trigger position recording
				toolhead.dwell(0.100)  # Allow settling
				trigger_sample_pos = self._get_averaged_position(stepper)
				sample_trigger_time = self.reactor.monotonic()
				
				# Track positions and timing
				position_samples.append(trigger_sample_pos)
				trigger_times.append(sample_trigger_time - sample_start_time)
				
				# Calculate sample travel with enhanced precision
				sample_travel = self._calculate_stepper_movement(
					stepper, base_pos, trigger_sample_pos, steps_per_mm)
				
				# Calculate total travel distance (initial + sample)
				total_travel = initial_travel + sample_travel
				
				if self.debug_mode:
					self._debug_log(f"Sample trigger position: {trigger_sample_pos} steps")
					self._debug_log(f"Sample travel from base: {sample_travel:.3f}mm")
					self._debug_log(f"Total travel distance: {total_travel:.3f}mm")
				
				# Verify sample is within allowed range
				if samples:
					existing_min = min(samples)
					existing_max = max(samples)
					if max(abs(total_travel - existing_min), abs(total_travel - existing_max)) > self.probe_samples_range:
						if self.debug_mode:
							self._debug_log(
								f"Sample outside allowed range: {total_travel:.3f}mm "
								f"(min: {existing_min:.3f}mm, max: {existing_max:.3f}mm)")
						retry_count += 1
						continue
				
				# Flush motion queue after sample
				print_time = toolhead.get_last_move_time()
				mcu.flush_moves(print_time, print_time)
				toolhead.wait_moves()
				
				samples.append(total_travel)
				
				# Retract after sample if not the last one
				if len(samples) < self.sample_count:
					toolhead.manual_move(retract_pos, self.slow_homing_speed)
					toolhead.wait_moves()
				
			except self.printer.command_error as e:
				retry_count += 1
				if "triggered prior to movement" in str(e):
					if self.debug_mode:
						self._debug_log(f"Endstop triggered before movement, retrying")
					continue
				raise
		
		# Log movement statistics
		self._log_movement_stats(name, position_samples, trigger_times)
		
		# Calculate final trigger height with enhanced precision
		samples.sort()
		trigger_height = samples[len(samples)//2]  # Use median for robustness
		
		if self.debug_mode:
			self._debug_log(f"\n{name} final results:")
			self._debug_log(f"All samples (total travel): {', '.join([f'{s:.3f}' for s in samples])}mm")
			self._debug_log(f"Initial travel distance: {initial_travel:.3f}mm")
			self._debug_log(f"Selected trigger height: {trigger_height:.3f}mm")
		
		return trigger_height
		
	def _apply_z_offsets(self, toolhead, stepper_name=None, mode='CALIBRATE'):
		"""
		Apply Z offset for a single stepper or all steppers.
		Args:
			toolhead: Klipper toolhead object
			stepper_name: Name of stepper to adjust, or None for all steppers
			mode: 'CALIBRATE' or 'RESUME' to determine offset source
		"""
		mcu = self.printer.lookup_object('mcu')
		print_time = toolhead.get_last_move_time()
		
		# Load saved positions for kinematic reset
		saved_positions = None
		if mode == 'RESUME':
			try:
				eventtime = self.printer.get_reactor().monotonic()
				variables = self.save_variables.get_status(eventtime)['variables']
				ref_pos_key = 'z_endstop_position_stepper_z'
				if ref_pos_key in variables:
					saved_positions = variables[ref_pos_key]
					if self.debug_mode:
						self._debug_log(f"Found reference position: {saved_positions}")
			except Exception as e:
				if self.debug_mode:
					self._debug_log(f"Error loading reference position: {str(e)}")
		
		# Get stepper list to process
		steppers_to_process = []
		if stepper_name:
			# Find specific stepper
			for stepper, name in zip(self.z_steppers, self.stepper_names):
				if name == stepper_name:
					steppers_to_process = [(stepper, name)]
					break
		else:
			# Process all steppers
			steppers_to_process = list(zip(self.z_steppers, self.stepper_names))
		
		if not steppers_to_process:
			if self.debug_mode:
				self._debug_log(f"No steppers found to process")
			return
		
		try:
			# Process each stepper
			for stepper, name in steppers_to_process:
				# Get base offset based on mode and apply adjustment
				base_offset = self.z_offsets.get(name, 0) if mode == 'CALIBRATE' else \
							self._load_saved_z_offsets().get(name, 0)
				# Apply adjustment offset during actual movement
				adjustment = self.stepper_adjust_offsets.get(name, 0)
				offset = base_offset + adjustment
				
				if self.debug_mode and adjustment != 0:
					self._debug_log(
						f"Applying adjustment to {name}: Base offset {base_offset:.3f}mm, "
						f"Adjustment {adjustment:.3f}mm, Final {offset:.3f}mm")
		
				if offset == 0:
					if self.debug_mode:
						self._debug_log(f"No offset to apply for {name}")
					continue
		
				# Isolate current stepper
				for s in self.z_steppers:
					s.set_trapq(None)
				stepper.set_trapq(toolhead.get_trapq())
				toolhead.dwell(0.100)
		
				# Clear motion queue
				mcu.flush_moves(print_time, print_time)
				toolhead.wait_moves()
		
				# Apply offset
				current_pos = toolhead.get_position()
				new_pos = list(current_pos)
				new_pos[2] += offset
		
				if self.debug_mode:
					self._debug_log(
						f"Applying offset to {name}: "
						f"Current Z: {current_pos[2]:.3f}, "
						f"Offset: {offset:.3f}, "
						f"New Z: {new_pos[2]:.3f}"
					)
		
				# Move to new position
				toolhead.manual_move(new_pos, self.slow_homing_speed)
				toolhead.wait_moves()
		
				# Reset kinematic position if processing multiple steppers
				if not stepper_name and saved_positions:
					try:
						# Apply z_height_offset to the Z position
						adjusted_z = saved_positions[2] + self.z_height_offset
						reset_cmd = f"SET_KINEMATIC_POSITION Z={adjusted_z}"
						if self.debug_mode:
							self._debug_log(f"Resetting kinematic position with Z offset: {reset_cmd}")
						self.gcode.run_script_from_command(reset_cmd)
						toolhead.dwell(0.100)
					except Exception as e:
						if self.debug_mode:
							self._debug_log(f"Error resetting kinematic position: {str(e)}")
		
				if mode == 'CALIBRATE':
					self._save_z_offset(name, base_offset)
				
		finally:
			# Restore normal stepper operation
			print_time = toolhead.get_last_move_time()
			mcu.flush_moves(print_time, print_time)
			toolhead.wait_moves()
			for stepper in self.z_steppers:
				stepper.set_trapq(toolhead.get_trapq())
	
	def _probe_with_iterations(self, toolhead, initial_offsets):
		"""
		Perform multiple probe iterations after initial probing.
		
		Args:
			toolhead: Klipper toolhead object
			initial_offsets: Dictionary of offsets from first probing
		
		Returns:
			Dictionary of final calculated offsets
		"""
		
		if self.probe_iteration_count == 0:
			if self.debug_mode:
				self._debug_log("\nNo additional probe iterations requested")
				self._debug_log("\nUsing initial offsets as final:")
				for name, offset in initial_offsets.items():
					self._debug_log(f"{name}: {offset:.3f}")
			return initial_offsets
			
		if self.debug_mode:
			self._debug_log(f"\nStarting {self.probe_iteration_count} probe iterations")
			
		# Store results for each iteration
		iteration_results = {name: [] for name in self.stepper_names}
		
		try:
			for iteration in range(self.probe_iteration_count):
				if self.debug_mode:
					self._debug_log(f"\nIteration {iteration + 1} of {self.probe_iteration_count}")
				
				# Move entire Z axis down by retract distance between iterations
				current_pos = toolhead.get_position()
				retract_pos = list(current_pos)
				retract_pos[2] = max(current_pos[2] - self.retract_dist, 0)  # Prevent negative Z
				
				# Enable all steppers for full Z movement
				for s in self.z_steppers:
					s.set_trapq(toolhead.get_trapq())
				toolhead.dwell(0.100)  # Wait for steppers to be enabled
				
				# Move down
				if self.debug_mode:
					self._debug_log(f"\nRetracting Z axis to {retract_pos[2]:.3f} before iteration {iteration + 1}")
				toolhead.manual_move(retract_pos, self.fast_move_speed)
				toolhead.wait_moves()
				
				reference_z = retract_pos[2]  # Use retracted position as new reference
				
				# Probe each stepper in this iteration
				for i, (stepper, endstop, name) in enumerate(zip(
					self.z_steppers, self.endstops, self.stepper_names)):
					
					if self.debug_mode:
						self._debug_log(f"\nIterative probe {name} (iteration {iteration + 1})")
					
					# Disable all steppers except current one
					for s in self.z_steppers:
						s.set_trapq(None)
					stepper.set_trapq(toolhead.get_trapq())
					toolhead.dwell(0.500)
					
					try:
						# Probe this stepper
						trigger_height = self._probe_single_stepper(
							stepper, endstop, name, reference_z)
						
						# Store result for this iteration
						if i == 0:
							# First stepper (reference)
							first_trigger = trigger_height
							iteration_results[name].append(0.0)  # Always 0 for reference
						else:
							# Calculate offset relative to first stepper
							offset = first_trigger - trigger_height
							iteration_results[name].append(offset)
							
						if self.debug_mode:
							if i == 0:
								self._debug_log(
									f"Reference height: {trigger_height:.3f}")
							else:
								self._debug_log(
									f"Calculated offset: {offset:.3f}")
					
					except Exception as e:
						# Re-enable all steppers before raising error
						for s in self.z_steppers:
							s.set_trapq(toolhead.get_trapq())
						raise self.printer.command_error(
							f"Error in iteration {iteration + 1} probing {name}: {str(e)}")
				
				# Re-enable all steppers after iteration
				for s in self.z_steppers:
					s.set_trapq(toolhead.get_trapq())
					
			# Calculate final offsets
			final_offsets = {}
			for name in self.stepper_names:
				if name == self.stepper_names[0]:
					# First stepper keeps initial offset (usually with adjustment)
					final_offsets[name] = initial_offsets[name]
				else:
					# For other steppers, use last iteration measurement
					measurements = iteration_results[name]
					last_iteration_offset = measurements[-1]
					
					# Add last iteration offset to initial offset
					final_offsets[name] = initial_offsets[name] + last_iteration_offset
					
					if self.debug_mode:
						self._debug_log(
							f"\n{name} measurements analysis:"
							f"\nInitial offset: {initial_offsets[name]:.3f}"
							f"\nAll iterations: {[f'{x:.3f}' for x in measurements]}"
							f"\nLast iteration: {last_iteration_offset:.3f}"
							f"\nFinal offset: {final_offsets[name]:.3f}")
			
			if self.debug_mode:
				self._debug_log("\nFinal calculated offsets:")
				for name, offset in final_offsets.items():
					self._debug_log(f"{name}: {offset:.3f}")
			
			return final_offsets
		
		except Exception as e:
			if self.debug_mode:
				self._debug_log(f"Error in probe iterations: {str(e)}")
			raise
	
	def _debug_log(self, message):
		"""
		Output debug messages to both the printer console and klippy log
		
		Args:
			message: The message to log
		"""
		if not self.debug_mode:
			return
			
		prefix = "PLR LOG:: "
		formatted_msg = f"{prefix}{message}"
		
		# Log to klippy.log
		#logging.info(formatted_msg)
		
		# Output to printer console
		self.gcode.respond_info(formatted_msg)
	
	def _save_endstop_position(self, name, position):
		"""Save an endstop position to the variables file"""
		if not self.save_variables:
			return
			
		try:
			var_name = f"z_endstop_position_{name}"
			save_cmd = self.gcode.create_gcode_command(
				"SAVE_VARIABLE", "SAVE_VARIABLE",
				{"VARIABLE": var_name, "VALUE": list(position)})
			self.save_variables.cmd_SAVE_VARIABLE(save_cmd)
			
			if self.debug_mode:
				self._debug_log(
					f"Saved {name} position: {position[0]:.3f}, {position[1]:.3f}, {position[2]:.3f}")
		except Exception as e:
			raise self.printer.command_error(
				f"Error saving position for {name}: {str(e)}")
	
	def _restore_fan_speeds(self, state_data):
		"""Restore part cooling fan speeds from saved state"""
		try:
			if not state_data or 'fan_speeds' not in state_data:
				if self.debug_mode:
					self._debug_log("No fan speed data found in saved state")
				return
		
			fan_speeds = state_data.get('fan_speeds', {})
			if not fan_speeds:
				return
		
			# Get current active extruder
			toolhead = self.printer.lookup_object('toolhead')
			cur_extruder = toolhead.get_extruder().get_name()
			
			for fan_name in self.part_cooling_fans:
				try:
					if fan_name not in fan_speeds:
						continue
						
					speed = fan_speeds[fan_name]
					
					if self.debug_mode:
						self._debug_log(f"Fan found - {fan_name} with speed {speed}")
					
					# Check if this is the parts cooling fan for current extruder
					if fan_name == 'fan' or fan_name == f"{cur_extruder}_fan":
						# Use M106 with P0 for parts cooling fan
						speed_byte = int(speed * 255. + .5)
						fan_cmd = f"M106 P0 S{speed_byte}"
						if self.debug_mode:
							self._debug_log(f"Setting parts cooling fan {fan_name} using M106: {fan_cmd}")
					else:
						# Use SET_FAN_SPEED for other fans
						fan = self.printer.lookup_object(fan_name, None)
						if fan is None:
							if self.debug_mode:
								self._debug_log(f"Fan {fan_name} not found - skipping")
							continue
							
						fan_cmd = f"SET_FAN_SPEED FAN={fan_name} SPEED={speed}"
						if self.debug_mode:
							self._debug_log(f"Setting generic fan {fan_name} using SET_FAN_SPEED: {fan_cmd}")
					
					self.gcode.run_script_from_command(fan_cmd)
					
				except Exception as e:
					if self.debug_mode:
						self._debug_log(f"Error restoring {fan_name} speed: {str(e)}")
		
		except Exception as e:
			if self.debug_mode:
				self._debug_log(f"Error in fan speed restoration: {str(e)}")
	
	
	def _restore_xyz_offsets(self, state_data):
		"""Restore XYZ offsets from saved state"""
		try:
			if not state_data or 'xyz_offsets' not in state_data:
				if self.debug_mode:
					self._debug_log("No XYZ offset data found in saved state")
				return
		
			offsets = state_data.get('xyz_offsets', {})
			if not offsets:
				return
		
			# Construct SET_GCODE_OFFSET command
			offset_cmd = "SET_GCODE_OFFSET"
			for axis, value in offsets.items():
				offset_cmd += f" {axis.upper()}={value}"
			
			if self.debug_mode:
				self._debug_log(f"Restoring XYZ offsets: {offset_cmd}")
			
			self.gcode.run_script_from_command(offset_cmd)
		
		except Exception as e:
			if self.debug_mode:
				self._debug_log(f"Error restoring XYZ offsets: {str(e)}")
				
			
	cmd_PLR_TEST_APPLY_OFFSETS_help = "Test applying Z offsets using values stored in variables file"
	def cmd_PLR_TEST_APPLY_OFFSETS(self, gcmd):
		"""Apply stored Z offsets for testing purposes"""
		try:
			mode = gcmd.get('MODE', 'CALIBRATE').upper()
			if mode not in ['CALIBRATE', 'RESUME']:
				raise self.printer.command_error("MODE must be either CALIBRATE or RESUME")
			
			toolhead = self.printer.lookup_object('toolhead')
			if 'z' not in toolhead.get_status(self.reactor.monotonic())['homed_axes']:
				raise self.printer.command_error("Must home Z first")
				
			# Load and display current offsets
			saved_offsets = self._load_saved_z_offsets()
			gcmd.respond_info("Stored offsets:")
			for name, offset in saved_offsets.items():
				gcmd.respond_info(f"{name}: {offset:.3f}")
				
			# Apply the offsets
			self._apply_z_offsets(toolhead, mode=mode)
			gcmd.respond_info(f"Applied Z offsets in {mode} mode")
			
		except Exception as e:
			raise self.printer.command_error(f"Error testing offsets: {str(e)}")
	
	cmd_PLR_Z_HOME_help = "Home Z axis with multiple endstops. MODE=CALIBRATE to measure and save offsets, MODE=RESUME to use saved offsets"
	def cmd_PLR_Z_HOME(self, gcmd):
		mode = gcmd.get('MODE', 'CALIBRATE').upper()
		if mode not in ['CALIBRATE', 'RESUME']:
			raise self.printer.command_error("MODE must be either CALIBRATE or RESUME")
			
		toolhead = self.printer.lookup_object('toolhead')
		curtime = self.printer.get_reactor().monotonic()
		
		# Execute pre-operation G-code based on mode
		try:
			if mode == 'RESUME' and self.before_resume_gcode_lines:
				if self.debug_mode:
					self._debug_log("Executing before-resume G-code commands...")
				for line in self.before_resume_gcode_lines:
					self.gcode.run_script_from_command(line)
					toolhead.wait_moves()
			elif mode == 'CALIBRATE' and self.before_calibrate_gcode_lines:
				if self.debug_mode:
					self._debug_log("Executing before-calibrate G-code commands...")
				for line in self.before_calibrate_gcode_lines:
					self.gcode.run_script_from_command(line)
					toolhead.wait_moves()
		except Exception as e:
			raise self.printer.command_error(
				f"Error executing pre-operation G-code: {str(e)}")
		
		if 'z' not in toolhead.get_status(curtime)['homed_axes']:
			raise self.printer.command_error("Must home Z first")
		
		try:
			if self.debug_mode:
				self._debug_log(f"\nStarting PLR Z Home in {mode} mode")
				self._debug_log("Movement parameters:")
				self._debug_log(f"Z endstop position: {self.position_endstop}")
				self._debug_log(f"Initial speed: {self.slow_homing_speed} mm/s")
				self._debug_log(f"Fast travel parameters:")
				self._debug_log(f"Height: {self.fast_travel_upto_z_height} mm")
				self._debug_log(f"Speed: {self.fast_travel_speed} mm/s")
			
			# Initial probe with first endstop
			if self.debug_mode:
				self._debug_log("\nPerforming initial probe with first endstop")
			
			# Record starting position
			initial_pos = toolhead.get_position()
			if self.debug_mode:
				self._debug_log(f"Initial position: X{initial_pos[0]:.3f} Y{initial_pos[1]:.3f} Z{initial_pos[2]:.3f}")
			
			# Fast travel to initial height if configured
			if self.fast_travel_upto_z_height > 0 and mode == 'CALIBRATE':
				fast_pos = list(initial_pos)
				fast_pos[2] = min(self.fast_travel_upto_z_height, self.position_endstop)
				if self.debug_mode:
					self._debug_log(f"Fast travel to Z={fast_pos[2]:.3f} at {self.fast_travel_speed} mm/s")
				toolhead.manual_move(fast_pos, self.fast_travel_speed)
				toolhead.wait_moves()
			
			# Perform initial probe
			initial_endstop = self.endstops[0]
			probe_pos = list(initial_pos)
			probe_pos[2] = self.position_endstop
			
			try:
				measured_pos = self.printer.lookup_object('homing').probing_move(
					initial_endstop, probe_pos, self.fast_move_speed)
				
				if  mode == 'CALIBRATE':
					# Save initial probe position
					self._save_endstop_position('stepper_z', measured_pos)
					
				if self.debug_mode:
					self._debug_log(f"Initial probe trigger at Z={measured_pos[2]:.3f}")
				
			except self.printer.command_error as e:
				msg = str(e)
				if "triggered prior to movement" in msg:
					raise self.printer.command_error(
						"Initial endstop triggered before movement. Check Z position.")
				raise
			
			# Return to safe height for individual probing
			retract_pos = list(measured_pos)
			retract_pos[2] -= self.retract_dist
			toolhead.manual_move(retract_pos, self.fast_move_speed)
			toolhead.wait_moves()
			
			reference_z = retract_pos[2]  # Save this height for returning between probes
			
			if self.halt_after_initial_probe:
				self._debug_log(
					"Initial Z probe completed. Halting as requested.")
				return
			
			# Individual stepper probing
			self._debug_log("\nStarting individual stepper probing...")
			
			for i, (stepper, endstop, name) in enumerate(zip(
				self.z_steppers, self.endstops, self.stepper_names)):
				
				if self.debug_mode:
					self._debug_log(f"\nProbing {name} (stepper {i+1} of {len(self.z_steppers)})")
				
				# Disable all steppers except the current one
				for s in self.z_steppers:
					s.set_trapq(None)
				stepper.set_trapq(toolhead.get_trapq())
				
				# Ensure movement has settled
				toolhead.dwell(0.500)  # 100ms pause
				
				try:
					# Probe this stepper
					trigger_height = self._probe_single_stepper(
						stepper, endstop, name, reference_z)
					
					# Store raw trigger height results
					if i == 0:
						# First stepper (reference)
						first_trigger = trigger_height
						self.z_offsets[name] = 0.0  # Reference stepper always has 0 offset
					else:
						# Calculate offset relative to first stepper without adjustment
						base_offset = first_trigger - trigger_height
						self.z_offsets[name] = base_offset
						
					# Save offset only in CALIBRATE mode
					if mode == 'CALIBRATE':
						self._save_z_offset(name, self.z_offsets[name])
					
					if self.debug_mode:
						self._debug_log(f"{name} final offset: {self.z_offsets[name]:.3f}mm")
					
				except Exception as e:
					# Re-enable all steppers before raising error
					for s in self.z_steppers:
						s.set_trapq(toolhead.get_trapq())
					raise self.printer.command_error(
						f"Error probing {name}: {str(e)}")
			
			# Re-enable all steppers
			for s in self.z_steppers:
				s.set_trapq(toolhead.get_trapq())
			
			# Store initial offsets after first probing round
			initial_offsets = self.z_offsets.copy()
			
			if self.probe_iteration_count > 1 and mode == 'CALIBRATE':
				if self.debug_mode:
					self._debug_log(
						f"\nStarting additional {self.probe_iteration_count} probe iterations")
				
				try:
					# Perform iterative probing and get final offsets
					final_offsets = self._probe_with_iterations(toolhead, initial_offsets)
					
					# Update z_offsets with final calculated values
					self.z_offsets.update(final_offsets)
					
					# Save final offsets if in CALIBRATE mode
					if mode == 'CALIBRATE':
						for name, offset in self.z_offsets.items():
							self._save_z_offset(name, offset)
							
				except Exception as e:
					raise self.printer.command_error(
						f"Error during probe iterations: {str(e)}")
						
			# Final homing sequence
			self._debug_log("\nStarting final homing sequence...")
			
			# Return to reference height
			return_pos = list(toolhead.get_position())
			return_pos[2] = reference_z
			toolhead.manual_move(return_pos, self.slow_homing_speed)
			toolhead.wait_moves()
			
			# 3. Final home at slow speed
			measured_pos = self.printer.lookup_object('homing').probing_move(
				self.endstops[0], probe_pos, self.slow_homing_speed)
		
			
			# Apply Z offsets for all steppers
			try:
				if self.debug_mode:
					self._debug_log("\nApplying Z offsets for all steppers")
				self._apply_z_offsets(toolhead, stepper_name=None, mode=mode)
			except Exception as e:
				raise self.printer.command_error(
					f"Error applying Z offsets: {str(e)}")
			
			try:
				# Execute post-operation G-code based on mode
				if mode == 'RESUME' and self.after_resume_gcode_lines:
					if self.debug_mode:
						self._debug_log("Executing after-resume G-code commands...")
					for line in self.after_resume_gcode_lines:
						self.gcode.run_script_from_command(line)
						toolhead.wait_moves()
				elif mode == 'CALIBRATE' and self.after_calibrate_gcode_lines:
					if self.debug_mode:
						self._debug_log("Executing after-calibrate G-code commands...")
					for line in self.after_calibrate_gcode_lines:
						self.gcode.run_script_from_command(line)
						toolhead.wait_moves()
			except Exception as e:
				# Log error but don't fail the operation
				if self.debug_mode:
					self._debug_log(
						f"Warning: Error executing post-operation G-code: {str(e)}")
			
			if mode == 'RESUME':
				try:
					saved_state = self._get_saved_state()
					if saved_state:
						# Restore fan speeds
						self._restore_fan_speeds(saved_state)
						# Restore XYZ offsets
						self._restore_xyz_offsets(saved_state)
				except Exception as e:
					if self.debug_mode:
						self._debug_log(f"Warning: Error restoring settings: {str(e)}")
				
				self.resuming_print = False  # Ensure flag is set before you start printing.
			
			# Success message with results
			msg = [f"\nPLR Z Home ({mode} mode) completed successfully:"]
			msg.append("Final Z offsets:")
			for name, offset in self.z_offsets.items():
				msg.append(f"{name}: {offset:.3f}mm")
			
			if self.debug_mode:
				msg.append("\nFinal stepper positions:")
				for stepper, name in zip(self.z_steppers, self.stepper_names):
					pos = stepper.get_commanded_position()
					msg.append(f"{name}: {pos:.3f}")
			
			self._debug_log("\n".join(msg))
			
		except Exception as e:
			msg = str(e)
			if self.debug_mode:
				self._debug_log(f"Error in Z calibration: {str(e)}")
			# Ensure all steppers are re-enabled
			try:
				for s in self.z_steppers:
					s.set_trapq(toolhead.get_trapq())
			except:
				pass
			raise self.printer.command_error(
				f"Z calibration failed: {msg}")
			
		except Exception as e:
			msg = str(e)
			if self.debug_mode:
				self._debug_log(f"Error in Z calibration: {str(e)}")
			# Ensure all steppers are re-enabled
			try:
				for s in self.z_steppers:
					s.set_trapq(toolhead.get_trapq())
			except:
				pass
			raise self.printer.command_error(
				f"Z calibration failed: {msg}")
			
	
	### STATE MANAGEMENT and GCODE MODIFICATION ####
	
										
	def _verify_state(self, state: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
		"""
		Verify the integrity and validity of a state before saving.
		Returns (is_valid, error_message).
		"""
		if not isinstance(state, dict):
			return False, "State must be a dictionary"
			
		# Required keys and their type checks
		required_fields = {
			'position': {
				'type': dict,
				'subfields': {'x': (float, int), 'y': (float, int), 'z': (float, int)}
			},
			'layer': {'type': int},
			'layer_height': {'type': (float, int)},
			'file_progress': {
				'type': dict,
				'subfields': {
					'position': int,
					'total_size': int,
					'progress_pct': (float, int)
				}
			},
			'collection_time': {'type': (float, int)},
			'save_time': {'type': (float, int)},
			'hotend_temp': {'type': (float, int)},
			'bed_temp': {'type': (float, int)}
		}
		
		# Verify all required fields exist and are of correct type
		for field, validation in required_fields.items():
			if field not in state:
				return False, f"Missing required field: {field}"
				
			field_type = validation['type']
			if isinstance(field_type, tuple):
				if not isinstance(state[field], field_type):
					return False, f"Field {field} has wrong type"
			else:
				if not isinstance(state[field], validation['type']):
					return False, f"Field {field} has wrong type"
				
			# Check subfields if they exist
			if 'subfields' in validation:
				for subfield, subtype in validation['subfields'].items():
					if subfield not in state[field]:
						return False, f"Missing subfield {subfield} in {field}"
					if isinstance(subtype, tuple):
						if not isinstance(state[field][subfield], subtype):
							return False, f"Subfield {subfield} in {field} has wrong type"
					else:
						if not isinstance(state[field][subfield], subtype):
							return False, f"Subfield {subfield} in {field} has wrong type"
		
		# Verify logical constraints
		if state['file_progress']['total_size'] < 0:
			return False, "File size cannot be negative"
			
		if not (0 <= state['file_progress']['progress_pct'] <= 100):
			return False, "Progress percentage must be between 0 and 100"
			
		if state['layer'] < 0:
			return False, "Layer number cannot be negative"
				
		# Verify temperature ranges (basic sanity checks)
		if not (-273.15 <= float(state['hotend_temp']) <= 500):
			return False, "Hotend temperature out of reasonable range"
			
		if not (-273.15 <= float(state['bed_temp']) <= 200):
			return False, "Bed temperature out of reasonable range"
			
		return True, None


	def _optimize_background_interval(self) -> float:
		"""
		Calculate optimal background task interval based on current conditions.
		Returns the recommended interval in seconds.
		"""
		try:
			# Base interval from configuration
			interval = self.save_interval
			
			# Track time since critical events
			current_time = self.reactor.monotonic()
			time_since_extruder_change = current_time - self._last_extruder_change_time
			
			# Start with base interval
			reduction_factor = 1.0
			
			# Extruder change effect (moderate at start, tapering off)
			if time_since_extruder_change < 20:
				extruder_factor = 0.3 + (time_since_extruder_change / 20.0) * 0.7
				reduction_factor = min(reduction_factor, extruder_factor)
			
			# Apply reduction to interval
			interval = interval * reduction_factor
			
			# Check recent state changes if we have history
			if len(self.state_history) >= 2:
				last_states = list(self.state_history)[-2:]
				
				# Calculate position change
				pos_change = sum(
					abs(last_states[1]['position'][axis] - 
						last_states[0]['position'][axis])
					for axis in ['x', 'y', 'z']
				)
				
				# If significant movement, further decrease interval
				if pos_change > 10:  # mm of movement
					interval = interval * 0.75
				
				# Check temperature stability
				temp_change = abs(
					last_states[1]['hotend_temp'] - 
					last_states[0]['hotend_temp']
				)
				if temp_change > 5:  # degrees of change
					interval = interval * 0.75
			
			# Different minimum intervals based on event type
			min_interval = 5.0  # default minimum
			if time_since_extruder_change < 5:  # Very recent extruder change
				min_interval = 3.0  # Moderate for extruder changes
				
			# Never go below minimum safe interval for current conditions
			return max(interval, min_interval)
			
		except Exception as e:
			if self.debug_mode:
				logging.info(f"Error optimizing interval: {str(e)}")
			return self.save_interval

	def _collect_current_state(self) -> Dict[str, Any]:
		  try:
			  # Get single eventtime for all status queries
			  eventtime = self.reactor.monotonic()
			  
			  # Get all status objects at once using the same eventtime
			  try:
				  print_stats = self.printer.lookup_object('print_stats')
				  virtual_sdcard = self.printer.lookup_object('virtual_sdcard')
				  print_stats_status = print_stats.get_status(eventtime)
				  sdcard_status = virtual_sdcard.get_status(eventtime)
				  extruder_status = self.extruder.get_status(eventtime)
				  toolhead_status = self.toolhead.get_status(eventtime)
				  heater_bed_status = self.heater_bed.get_status(eventtime) if self.heater_bed else {}
				  
				  # Get fan speeds for configured part cooling fans
				  fan_speeds = {}
				  for fan_name in self.part_cooling_fans:
					  try:
						  fan = self.printer.lookup_object(fan_name)
						  if fan:
							  fan_status = fan.get_status(eventtime)
							  fan_speeds[fan_name] = round(float(fan_status.get('speed', 0)), 3)
					  except Exception as e:
						  if self.debug_mode:
							  logging.info(f"PowerLossRecovery: Error getting status for fan {fan_name}: {str(e)}")
				  
				  # Get file information
				  current_file = print_stats_status.get('filename', 'unknown')
				  file_position = sdcard_status.get('file_position', 0)
				  file_size = sdcard_status.get('file_size', 0)
				  
				  # Calculate progress percentage
				  progress = (file_position / file_size * 100) if file_size > 0 else 0
				  
				  current_progress = {
					  'position': file_position,
					  'total_size': file_size,
					  'progress_pct': round(progress, 2)
				  }
				  
				  # Get positions from the same timestamp
				  cur_pos = toolhead_status.get('position', [0., 0., 0., 0.])[:3]
				  
				  # Get temperatures from the same timestamp
				  hotend_temp = extruder_status.get('temperature', 0)
				  bed_temp = heater_bed_status.get('temperature', 0)
				  
				  # Get current XYZ offsets
				  gcode_move = self.printer.lookup_object('gcode_move')
				  if gcode_move:
					  gcode_status = gcode_move.get_status(eventtime)
					  homing_origin = gcode_status.get('homing_origin', [0., 0., 0.])
					  position_offset = gcode_status.get('position_offset', [0., 0., 0.])
					  xyz_offsets = {
						  'x': round(float(homing_origin[0] + position_offset[0]), 3),
						  'y': round(float(homing_origin[1] + position_offset[1]), 3),
						  'z': round(float(homing_origin[2] + position_offset[2]), 3)
					  }
				  else:
					  xyz_offsets = {'x': 0., 'y': 0., 'z': 0.}
					  if self.debug_mode:
						  logging.info("PowerLossRecovery: Could not get gcode_move object for XYZ offsets")

				  # Compile synchronized state information
				  state_info = {
					  'position': {
						  'x': round(float(cur_pos[0]), 3),
						  'y': round(float(cur_pos[1]), 3),
						  'z': round(float(cur_pos[2]), 3)
					  },
					  'xyz_offsets': xyz_offsets,
					  'fan_speeds': fan_speeds,
					  'layer': self.last_layer,
					  'layer_height': round(float(self.current_z_height), 3),
					  'file_progress': current_progress,
					  'active_extruder': extruder_status.get('active_extruder', 'extruder'),
					  'hotend_temp': round(float(hotend_temp), 1),
					  'bed_temp': round(float(bed_temp), 1),
					  'save_time': eventtime,
					  'current_file': current_file,
					  'collection_time': eventtime  # Add timestamp for verification
				  }
				  
				  if self.debug_mode:
					  logging.info(f"PowerLossRecovery: Collected synchronized state at time {eventtime:.2f} "
								 f"for file {current_file} at {current_progress['progress_pct']:.2f}%")
				  
				  return state_info
				  
			  except Exception as e:
				  if self.debug_mode:
					  logging.info(f"Error collecting synchronized state: {str(e)}")
				  return None
				  
		  except Exception as e:
			  logging.exception("PowerLossRecovery: Error in state collection")
			  if self.debug_mode:
				  logging.info(f"Error collecting state: {str(e)}")
			  return None
	
	def _get_move_buffer_status(self) -> dict:
		"""Get move buffer status from MCU"""
		try:
			mcu = self.printer.lookup_object('mcu')
			status = mcu.get_status(self.reactor.monotonic())
			return {
				'moves_pending': status.get('moves_pending', 0),
				'min_move_time': status.get('min_move_time', 0),
				'max_move_time': status.get('max_move_time', 0)
			}
		except Exception as e:
			if self.debug_mode:
				self._debug_log(f"Error getting move buffer status: {str(e)}")
			return {'moves_pending': 0, 'min_move_time': 0, 'max_move_time': 0}
	
	def _calculate_optimal_delay(self) -> int:
		try:
			toolhead = self.printer.lookup_object('toolhead')
			reactor = self.printer.get_reactor()
			mcu = self.printer.lookup_object('mcu')
			eventtime = reactor.monotonic()
			print_time = toolhead.get_last_move_time()
			est_print_time = mcu.estimated_print_time(eventtime)
			
			# Calculate MCU lag
			mcu_lag = print_time - est_print_time
			
			# Calculate how many save_intervals we need to cover the MCU lag
			needed_intervals = max(1, int(mcu_lag / self.save_interval) + 1)
			
			# Calculate optimal delay to cover the lag
			optimal_delay = needed_intervals
			
			if self.debug_mode:
				self._debug_log(
					f"Delay calculation:\n"
					f"  Print time: {print_time:.3f}\n"
					f"  Est print time: {est_print_time:.3f}\n"
					f"  MCU lag: {mcu_lag:.3f}s\n"
					f"  Save interval: {self.save_interval}s\n"
					f"  Needed intervals: {needed_intervals}\n"
					f"  Total time lag: {mcu_lag + (optimal_delay * self.save_interval):.3f}s\n"
					f"  Final delay: {optimal_delay} (base: {self.save_delay})"
				)
				
			return min(optimal_delay, self.history_size - 1)
			
		except Exception as e:
			if self.debug_mode:
				self._debug_log(f"Error calculating optimal delay: {str(e)}")
			return self.save_delay



	def _save_current_state(self):
		if not self.is_active:
			if self.debug_mode:
				logging.info("PowerLossRecovery: Not saving state - printer not active")
			return
			
		if self.resuming_print:
			if self.debug_mode:
				logging.info("PowerLossRecovery: Not saving state - PLR resume in progress")
			return
			
		if not self.power_loss_recovery_enabled:
			if self.debug_mode:
				logging.info("PowerLossRecovery: Not saving state - power loss recovery disabled")
			return
				
		if self.save_variables is None:
			if self.debug_mode:
				logging.info("PowerLossRecovery: Cannot save state - save_variables not initialized")
			return
		
		try:
			# Get the delayed state from history
			#if len(self.state_history) > self.save_delay:
			
			optimal_delay = self._calculate_optimal_delay()
			
			if len(self.state_history) > optimal_delay:
				
				# Convert deque to list for easier indexing from end
				history_list = list(self.state_history)
				state_to_save = history_list[-(self.save_delay + 1)]
				
				# Add buffer status to saved state
				buffer_status = self._get_move_buffer_status()
				state_to_save['mcu_status'] = buffer_status
				
				# Verify state before saving
				is_valid, error_msg = self._verify_state(state_to_save)
				if not is_valid:
					if self.debug_mode:
						logging.info(f"PowerLossRecovery: Invalid state, not saving: {error_msg}")
					return
				
				if self.debug_mode:
					collection_time = state_to_save.get('collection_time', 0)
					progress_info = state_to_save.get('file_progress', {})
					logging.info(f"PowerLossRecovery: Saving synchronized state from time {collection_time:.2f} "
							   f"at {progress_info.get('progress_pct', 0):.2f}% completion")
				
				# Save to variables file
				state_json = json.dumps(state_to_save)
				escaped_json = state_json.replace('"', '\\"')
				self.gcode.run_script_from_command(
					f'SAVE_VARIABLE VARIABLE=resume_meta_info VALUE="{escaped_json}"')
				
				self.last_save_time = self.reactor.monotonic()
				self._consecutive_failures = 0
				
				if self.debug_mode:
					logging.info("PowerLossRecovery: Successfully saved synchronized state")
			else:
				if self.debug_mode:
					logging.info(f"PowerLossRecovery: Not enough history ({len(self.state_history)} states) "
							   f"to save delayed state (need {self.save_delay + 1})")
				
		except Exception as e:
			logging.exception("PowerLossRecovery: Error saving printer state")
			if self.debug_mode:
				logging.info(f"Error saving printer state: {str(e)}")
		  

	def _background_task(self, eventtime):
		try:
			# Previous state tracking
			last_save_attempt = getattr(self, '_last_save_attempt', 0)
			consecutive_failures = getattr(self, '_consecutive_failures', 0)
			
			print_stats = self.printer.lookup_object('print_stats')
			current_state = print_stats.get_status(eventtime)['state']
			printing = current_state == 'printing'
			
			if printing != self.is_active:
				self.is_active = printing
				if printing:
					if self.debug_mode:
						logging.info("PowerLossRecovery: Print started - activating")
					self.state_history.clear()
					consecutive_failures = 0
				else:
					if self.debug_mode:
						logging.info("PowerLossRecovery: Print ended - deactivating")
					#self._reset_state()
			
			if self.is_active :
				if not self.power_loss_recovery_enabled:
					return eventtime + 1.0  # Check again in 30 seconds
					
				# Collect current state
				current_state = self._collect_current_state()
				if current_state:
					# Verify state before adding to history
					is_valid, error_msg = self._verify_state(current_state)
					if is_valid:
						self.state_history.append(current_state)
						consecutive_failures = 0
						if self.debug_mode:
							logging.info(
								f"PowerLossRecovery: Collected valid state "
								f"(history size: {len(self.state_history)})"
							)
					else:
						consecutive_failures += 1
						if self.debug_mode:
							logging.info(
								f"PowerLossRecovery: Invalid state collected: {error_msg}"
							)
				
				# Determine if we should save state
				should_save = False
				if self.time_based_enabled:
					time_since_last = eventtime - self.last_save_time
					interval = self._optimize_background_interval()
					should_save = time_since_last >= interval
				
				# Implement exponential backoff for failures
				if consecutive_failures > 0:
					backoff = min(30, 2 ** consecutive_failures)
					if eventtime - last_save_attempt < backoff:
						should_save = False
				
				if should_save:
					self._last_save_attempt = eventtime
					self._save_current_state()
			
			# Store state for next iteration
			self._consecutive_failures = consecutive_failures
			
			# Calculate next wake time
			if not self.time_based_enabled or not printing:
				return eventtime + 1.0
			
			# Use optimized interval
			return eventtime + self._optimize_background_interval()
				
		except Exception as e:
			logging.exception("Error in background task")
			return eventtime + 1.0
			  
					  
	def _handle_layer_change(self, gcmd):
		if not self.save_on_layer or not self.is_active:
			return
			
		try:
			self.last_layer = gcmd.get_int('LAYER', None)
			layer_height = gcmd.get_float('LAYER_HEIGHT', None)
			
			# Update last layer change time
			self._last_layer_change_time = self.reactor.monotonic()
			
			# Track cumulative layer height if provided
			if layer_height is not None:
				self.current_z_height = layer_height
				if self.debug_mode:
					logging.info(f"PowerLossRecovery: Layer height: {layer_height:.3f}, "
							   f"Cumulative Z height: {self.current_z_height:.3f}")
			
			if self.debug_mode:
				logging.info(f"PowerLossRecovery: Layer changed to {self.last_layer}")
			self._save_current_state()
			
			# Trigger the next background task immediately if active
			if self.is_active and self.time_based_enabled:
				self.reactor.register_timer(self._background_task, self.reactor.monotonic())
				
		except Exception as e:
			logging.exception("Error handling layer change")
			if self.debug_mode:
				logging.info(f"Error handling layer change: {str(e)}")
		
	def _handle_activate_extruder(self, eventtime):
		if not self.is_active:
			if self.debug_mode:
				logging.info("PowerLossRecovery: Extruder activation detected but printer not active")
			return
			
		try:
			# Update last extruder change time
			self._last_extruder_change_time = self.reactor.monotonic()
			
			if self.debug_mode:
				logging.info("PowerLossRecovery: Extruder activation detected - saving state")
			self._save_current_state()
			
			# Trigger the next background task immediately if active
			if self.is_active and self.time_based_enabled:
				self.reactor.register_timer(self._background_task, self.reactor.monotonic())
				
		except Exception as e:
			logging.exception("Error handling extruder activation")
			if self.debug_mode:
				logging.info(f"Error saving state after extruder activation: {str(e)}")
				
	def _handle_connect(self):
		try:
			self.save_variables = self.printer.lookup_object('save_variables', None)
			if self.save_variables is None:
				logging.info("save_variables not found. PowerLossRecovery will not save state.")
			elif self.debug_mode:
				logging.info("PowerLossRecovery: Successfully connected to save_variables")
		except Exception as e:
			logging.exception("Error during PowerLossRecovery connection")
			raise
	
	def _handle_ready(self):
		try:
			self.toolhead = self.printer.lookup_object('toolhead')
			self.extruder = self.printer.lookup_object('extruder')
			self.heater_bed = self.printer.lookup_object('heater_bed', None)
			
			if self.debug_mode:
				logging.info("PowerLossRecovery: Ready state - starting background task")
			
			# Start periodic timer with immediate first run
			self.reactor.register_timer(self._background_task, self.reactor.NOW)
			
		except Exception as e:
			logging.exception("Error during PowerLossRecovery ready state")
			raise
			
	
	def _reset_state(self):
		if self.save_variables is None:
			return
			
		try:
			empty_state = json.dumps({})
			self.gcode.run_script_from_command(
				f'SAVE_VARIABLE VARIABLE=resume_meta_info VALUE="{empty_state}"')
			self.last_layer = 0
			self.last_save_time = 0
			if self.debug_mode:
				logging.info("PowerLossRecovery: State reset completed")
		except Exception as e:
			logging.exception("Error resetting state")
			if self.debug_mode:
				logging.info(f"Error resetting printer state: {str(e)}")

	cmd_PLR_QUERY_SAVED_STATE_help = "Query the current status of the state saver"
	def cmd_PLR_QUERY_SAVED_STATE(self, gcmd):
		msg = ["PowerLossRecovery Status:"]
		msg.append(f"Active: {self.is_active}")
		msg.append(f"Power Loss Recovery: {'Enabled' if self.power_loss_recovery_enabled else 'Disabled'}")
		msg.append(f"Debug Mode: {'Enabled' if self.debug_mode else 'Disabled'}")
		msg.append(f"Time-based saving: {'Enabled (%ds interval)' % self.save_interval if self.time_based_enabled else 'Disabled'}")
		msg.append(f"Layer-based saving: {'Enabled (current layer: %d)' % self.last_layer if self.save_on_layer else 'Disabled'}")
		msg.append(f"History size: {self.history_size} (current: {len(self.state_history)})")
		msg.append(f"Save delay: {self.save_delay} states")
		
		try:
			val = self.save_variables.get_stored_variable('resume_meta_info')
			if val:
				saved_data = json.loads(val)
				progress_info = saved_data.get('file_progress', {})
				collection_time = saved_data.get('collection_time', 0)
				msg.extend([
					"",
					"Currently Saved State:",
					f"Collected at: {collection_time:.2f}",
					f"File: {saved_data.get('current_file', 'unknown')}",
					f"Layer: {saved_data.get('layer', 'unknown')}",
					f"Progress: {progress_info.get('progress_pct', 0):.2f}% " +
					f"(Position: {progress_info.get('position', 0)}/{progress_info.get('total_size', 0)} bytes)",
					"Position: X%.1f Y%.1f Z%.1f" % (
						saved_data.get('position', {}).get('x', 0),
						saved_data.get('position', {}).get('y', 0),
						saved_data.get('position', {}).get('z', 0)
					),
					f"Temperatures - Hotend: {saved_data.get('hotend_temp', 0):.1f}°C, Bed: {saved_data.get('bed_temp', 0):.1f}°C"
				])
		except Exception as e:
			if self.debug_mode:
				msg.append(f"\nError reading saved state: {str(e)}")
				
						
	cmd_PLR_SAVE_PRINT_STATE_help = "Manually save current printer state"
	def cmd_PLR_SAVE_PRINT_STATE(self, gcmd):
		self._save_current_state()
		gcmd.respond_info("Printer state saved")
		
	cmd_PLR_RESET_PRINT_DATA_help = "Clear all saved state data"
	def cmd_PLR_RESET_PRINT_DATA(self, gcmd):
		try:
			self._reset_state()
			msg = "PowerLossRecovery: All saved state data cleared"
			if self.debug_mode:
				msg += "\nDebug: Reset complete, variables file updated"
			gcmd.respond_info(msg)
		except Exception as e:
			gcmd.respond_info(f"Error clearing saved state: {str(e)}")	
			
	cmd_PLR_ENABLE_help = "Enable power loss recovery state saving"
	def cmd_PLR_ENABLE(self, gcmd):
		self.power_loss_recovery_enabled = True
		if self.debug_mode:
			logging.info("PowerLossRecovery: Power loss recovery enabled")
		gcmd.respond_info("Power loss recovery enabled")
	
	cmd_PLR_DISABLE_help = "Disable power loss recovery state saving"
	def cmd_PLR_DISABLE(self, gcmd):
		self.power_loss_recovery_enabled = False
		if self.debug_mode:
			logging.info("PowerLossRecovery: Power loss recovery disabled")
		gcmd.respond_info("Power loss recovery disabled")
	
	cmd_PLR_SAVE_MESH_help = "Save the currently active bed mesh profile name to variables file"
	def cmd_PLR_SAVE_MESH(self, gcmd):
		try:
			bed_mesh = self.printer.lookup_object('bed_mesh')
			if bed_mesh is None:
				raise self.printer.command_error("bed_mesh module not found")
				
			status = bed_mesh.get_status(self.reactor.monotonic())
			profile_name = status.get('profile_name')
			
			if not profile_name:
				raise self.printer.command_error("No bed mesh profile currently active")
				
			# Convert profile name to JSON string to handle literals properly
			save_cmd = self.gcode.create_gcode_command(
				"SAVE_VARIABLE", "SAVE_VARIABLE",
				{"VARIABLE": "saved_mesh_profile", "VALUE": json.dumps(profile_name)})
			self.save_variables.cmd_SAVE_VARIABLE(save_cmd)
			
			if self.debug_mode:
				self._debug_log(f"Saved bed mesh profile: {profile_name}")
				
			gcmd.respond_info(f"Saved bed mesh profile: {profile_name}")
			
		except Exception as e:
			msg = f"Error saving bed mesh profile: {str(e)}"
			if self.debug_mode:
				self._debug_log(msg)
			raise self.printer.command_error(msg)
			
	cmd_PLR_LOAD_MESH_help = "Load the previously saved bed mesh profile"
	def cmd_PLR_LOAD_MESH(self, gcmd):
		try:
			if self.save_variables is None:
				raise self.printer.command_error("save_variables not initialized")
				
			eventtime = self.reactor.monotonic()
			variables = self.save_variables.get_status(eventtime)['variables']
			profile_name = variables.get('saved_mesh_profile')
			
			if not profile_name or profile_name == '""':
				raise self.printer.command_error("No saved bed mesh profile found")
				
			# Remove any quotes from the stored profile name
			profile_name = profile_name.strip('"')
			profile_name = profile_name.strip('"')
			# Verify bed_mesh object exists
			bed_mesh = self.printer.lookup_object('bed_mesh')
			if bed_mesh is None:
				raise self.printer.command_error("bed_mesh module not found")
				
			# Verify profile exists before trying to load it
			profiles = bed_mesh.get_status(eventtime).get('profiles', {})
			if profile_name not in profiles:
				raise self.printer.command_error(f"Profile '{profile_name}' not found in bed_mesh profiles")
			
			load_cmd = f"BED_MESH_PROFILE LOAD='{profile_name}'"
			self.gcode.run_script_from_command(load_cmd)
			
			if self.debug_mode:
				self._debug_log(f"Loaded bed mesh profile: {profile_name}")
				
			gcmd.respond_info(f"Loaded bed mesh profile: {profile_name}")
			
		except Exception as e:
			msg = f"Error loading bed mesh profile: {str(e)}"
			if self.debug_mode:
				self._debug_log(msg)
			raise self.printer.command_error(msg)

	
	### POWER LOSS RECOVERY GCODE MODIFICATION SECTION ####
	
	
	def _get_saved_state(self) -> Optional[Dict[str, Any]]:
		"""
		Retrieve the last saved state from the variables file.
		Returns None if no valid state is found.
		"""
		try:
			if self.save_variables is None:
				if self.debug_mode:
					logging.info("PowerLossRecovery: Cannot get state - save_variables not initialized")
				return None
				
			# Get the stored state from save_variables status
			eventtime = self.reactor.monotonic()
			variables = self.save_variables.get_status(eventtime)['variables']
			state_data = variables.get('resume_meta_info')
			
			if not state_data:
				if self.debug_mode:
					logging.info("PowerLossRecovery: No saved state found")
				return None
				
			# Verify state integrity
			is_valid, error_msg = self._verify_state(state_data)
			if not is_valid:
				if self.debug_mode:
					logging.info(f"PowerLossRecovery: Invalid saved state: {error_msg}")
				return None
				
			return state_data
			
		except Exception as e:
			if self.debug_mode:
				logging.info(f"PowerLossRecovery: Error getting saved state: {str(e)}")
			return None
			
	def _get_gcode_dir(self) -> str:
		"""
		Get the gcode directory from Klipper's configuration.
		Returns the configured path or the default '~/gcode' if not found.
		"""
		try:
			# Get the virtual_sdcard object directly
			virtual_sd = self.printer.lookup_object('virtual_sdcard')
			if virtual_sd:
				if hasattr(virtual_sd, 'sdcard_dirname'):
					return os.path.expanduser(virtual_sd.sdcard_dirname)
				if hasattr(virtual_sd, '_sdcard_dirname'):
					return os.path.expanduser(virtual_sd._sdcard_dirname)
		except Exception as e:
			if self.debug_mode:
				logging.info(f"PowerLossRecovery: Error getting gcode directory from config: {str(e)}")
		
		# Default fallback path
		return os.path.expanduser('~/gcode')
	
	cmd_PLR_RESUME_PRINT_help = "Create a modified gcode file for power loss recovery resume"
	def cmd_PLR_RESUME_PRINT(self, gcmd):
		"""
		Create a modified version of the last printed gcode file for power loss recovery.
		The new file will start from the last saved position.
		"""
		try:
			
			self.resuming_print = True  # Set flag to disable state saving
			
			# Get the saved state
			state_data = self._get_saved_state()
			if not state_data:
				gcmd.respond_info("No valid saved state found")
				return
				
			# Extract required information
			current_file = state_data.get('current_file')
			if not current_file:
				gcmd.respond_info("No filename found in saved state")
				return
				
			file_progress = state_data.get('file_progress', {})
			file_position = file_progress.get('position')
			if file_position is None:
				gcmd.respond_info("No file position found in saved state")
				return
				
			# Get gcode directory from config and construct full file path
			gcode_dir = self._get_gcode_dir()
			input_file = os.path.join(gcode_dir, current_file)
			
			if not os.path.exists(input_file):
				gcmd.respond_info(f"Original gcode file not found: {input_file}")
				return
				
			# Modify the gcode file
			output_file = self._modify_gcode_file(input_file, file_position)
			if not output_file:
				gcmd.respond_info("Error creating modified gcode file")
				return
				
			# Start the print with the modified file
			try:
				virtual_sdcard = self.printer.lookup_object('virtual_sdcard')
				if not virtual_sdcard:
					raise self.printer.command_error("virtual_sdcard not found")
					
				# Load and start the print
				basename = os.path.basename(output_file)
				self.gcode.run_script_from_command(f'SDCARD_PRINT_FILE FILENAME="{basename}"')
				
				msg = [
					f"Created and started power loss recovery file: {basename}",
					f"Original file: {current_file}",
					f"Resume position: {file_position} ({file_progress.get('progress_pct', 0):.1f}%)"
				]
				gcmd.respond_info("\n".join(msg))
				
			except Exception as e:
				gcmd.respond_info(f"Error starting print: {str(e)}")
			
		except Exception as e:
			gcmd.respond_info(f"Error processing PLR resume: {str(e)}")
	
	
	def _modify_gcode_file(self, input_file: str, file_position: int) -> Optional[str]:
		try:
			# Get saved state for position information
			saved_state = self._get_saved_state()
			if not saved_state:
				if self.debug_mode:
					self._debug_log("PowerLossRecovery: No saved state found for position restoration")
				return None
				
			# Extract Z position from saved state
			try:
				saved_z = saved_state['position']['z']
				if self.debug_mode:
					self._debug_log(f"PowerLossRecovery: Found saved Z position: {saved_z}")
			except KeyError as e:
				if self.debug_mode:
					self._debug_log(f"PowerLossRecovery: Could not find Z position in saved state: {e}")
				return None
			
			# Get file paths
			base_name, ext = os.path.splitext(input_file)
			backup_file = f"{base_name}{ext}.plr"
			
			# Rename original file to backup
			try:
				os.rename(input_file, backup_file)
				if self.debug_mode:
					self._debug_log(f"PowerLossRecovery: Renamed original file to {backup_file}")
			except Exception as e:
				if self.debug_mode:
					self._debug_log(f"PowerLossRecovery: Error renaming original file: {str(e)}")
				return None
			
			if self.debug_mode:
				self._debug_log(f"PowerLossRecovery: Modifying {input_file} to resume from position {file_position}")
			
			# Define placeholder texts
			SETUP_PLACEHOLDER = ";;;;; PLR_RESUME - INITIAL PRINTER SETUP STARTS ;;;;;"
			GCODE_PLACEHOLDER = ";;;;; PLR_RESUME - PRINT GCODE STARTS ;;;;;"
			
			# Track state
			found_setup = False
			found_gcode_start = False
			current_position = 0
			last_layer_z = None
			
			# Buffer to track potential layer change block
			layer_block_lines = []
			in_layer_block = False
			
			with open(backup_file, 'r') as infile, open(input_file, 'w') as outfile:
				in_setup_section = False
				in_comment_block = False
				in_executable_block = False
				comment_buffer = []
				
				for line in infile:
					current_position += len(line)
					stripped_line = line.strip()
					
					# Check for executable block start/end
					if "; EXECUTABLE_BLOCK_START" in line:
						in_executable_block = True
						outfile.write(line)
						continue
					elif "; EXECUTABLE_BLOCK_END" in line:
						in_executable_block = False
						outfile.write(line)
						continue
						
					# Track layer change blocks before resume position
					if current_position < file_position:
						if stripped_line == ";LAYER_CHANGE":
							in_layer_block = True
							layer_block_lines = [line]
						elif in_layer_block:
							layer_block_lines.append(line)
							if stripped_line.startswith(";Z:"):
								try:
									last_layer_z = float(stripped_line[3:])
								except ValueError:
									pass
							elif not stripped_line.startswith(";"):
								in_layer_block = False
								layer_block_lines = []
					
					# Handle comment blocks, but not if we're in an executable block
					if not in_executable_block:
						if not in_comment_block and stripped_line.startswith(';') and not stripped_line.startswith(';;'):
							in_comment_block = True
							comment_buffer = [line]
							continue
						elif in_comment_block:
							if stripped_line.startswith(';'):
								comment_buffer.append(line)
								continue
							else:
								in_comment_block = False
								for comment_line in comment_buffer:
									outfile.write(comment_line)
								comment_buffer = []
					
					# Process placeholders if we're not in a comment block or we're in an executable block
					if not in_comment_block or in_executable_block:
						if SETUP_PLACEHOLDER in line:
							found_setup = True
							in_setup_section = True
							# Write setup placeholder
							outfile.write(line)
							
							# Write restart gcode
							if self.restart_gcode_lines:
								if self.debug_mode:
									self._debug_log(f"Writing {len(self.restart_gcode_lines)} restart G-code lines")
								for gcode_line in self.restart_gcode_lines:
									if self.debug_mode:
										self._debug_log(f"Writing line: {repr(gcode_line)}")
									outfile.write(f"{gcode_line}\n")
								
								# Add Z restoration based on last layer height
								z_height = last_layer_z if last_layer_z is not None else saved_z
								z_restore_gcode = f"G1 Z{z_height:.3f} F3000 ; Restore Z height from last layer"
								if self.debug_mode:
									self._debug_log(f"Writing Z restore: {z_restore_gcode}")
									if last_layer_z is not None:
										self._debug_log(f"Using last layer Z height: {last_layer_z}")
									else:
										self._debug_log(f"Using saved Z position: {saved_z}")
								outfile.write(f"{z_restore_gcode}\n")
							
							# Write gcode placeholder immediately after
							outfile.write(f"{GCODE_PLACEHOLDER}\n")
							found_gcode_start = True
							in_setup_section = False
							continue
						elif GCODE_PLACEHOLDER in line:
							# Skip the original GCODE_PLACEHOLDER since we already wrote it
							continue
					
					# Handle non-setup sections and other lines
					if not found_setup:
						outfile.write(line)
					elif found_gcode_start:
						if current_position >= file_position:
							outfile.write(line)
					elif in_executable_block:
						# Write lines in executable blocks before setup
						outfile.write(line)
					elif in_comment_block and not in_setup_section:
						# Write comment lines as-is if not in setup section
						outfile.write(line)
					
				# Write any remaining comment buffer at EOF
				if comment_buffer:
					for line in comment_buffer:
						outfile.write(line)
			
			if not (found_setup and found_gcode_start):
				if self.debug_mode:
					self._debug_log("PowerLossRecovery: Required placeholders not found in gcode file")
				# Restore original file if modification failed
				os.remove(input_file)
				os.rename(backup_file, input_file)
				return None
				
			if self.debug_mode:
				self._debug_log(f"PowerLossRecovery: Successfully created modified file: {input_file}")
				self._debug_log(f"PowerLossRecovery: Original file backed up as: {backup_file}")
			
			return input_file
			
		except Exception as e:
			if self.debug_mode:
				self._debug_log(f"PowerLossRecovery: Error modifying gcode file: {str(e)}")
			# Attempt to restore original file if an error occurred
			try:
				if os.path.exists(input_file):
					os.remove(input_file)
				if os.path.exists(backup_file):
					os.rename(backup_file, input_file)
			except:
				pass
			return None
	
	def _restore_original_gcode(self, filename: str):
		"""Restore the original gcode file after print completion or cancellation"""
		try:
			base_name, ext = os.path.splitext(filename)
			if ext == '.plr':  # Don't process files that are already backups
				return
				
			gcode_dir = self._get_gcode_dir()
			original_file = os.path.join(gcode_dir, filename)
			backup_file = f"{original_file}.plr"
			
			if os.path.exists(backup_file):
				if os.path.exists(original_file):
					os.remove(original_file)
				os.rename(backup_file, original_file)
				if self.debug_mode:
					logging.info(f"PowerLossRecovery: Restored original file: {original_file}")
		except Exception as e:
			if self.debug_mode:
				logging.info(f"PowerLossRecovery: Error restoring original file: {str(e)}")
	
	def _handle_print_complete(self, print_stats, eventtime):
		"""Handle print completion or cancellation"""
		if not print_stats:
			return
			
		try:
			filename = print_stats.get_status(eventtime)['filename']
			if filename:
				self._restore_original_gcode(filename)
		except Exception as e:
			if self.debug_mode:
				logging.info(f"PowerLossRecovery: Error handling print complete: {str(e)}")
