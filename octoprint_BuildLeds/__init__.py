# coding=utf-8
from __future__ import absolute_import
from smbus2 import SMBus

import octoprint.plugin


class BuildledsPlugin(octoprint.plugin.SettingsPlugin,
					  octoprint.plugin.AssetPlugin,
					  octoprint.plugin.TemplatePlugin,
					  octoprint.plugin.StartupPlugin):

	def on_after_startup(self):
		self._logger.info("Build LEDs plugin started")
		self.update_leds()

	def get_template_configs(self):
		return [
			dict(type="settings", custom_bindings=False)
		]

	##~~ SettingsPlugin mixin

	def get_settings_defaults(self):
		return dict(
			device_address=0x3f,
			colours=dict(printing="#808080")
		)

	def on_settings_save(self, data):
		octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
		self.update_leds()

	def update_leds(self):
		printing_colour = self._settings.get(["colours", "printing"])
		self._logger.info("printing colour {printing_colour}".format(**locals()))
		(rI, gI, bI) = self.html_to_rgb(printing_colour)
		(r, g, b, w) = self.rgb_to_rgbw(rI, gI, bI)
		self._logger.info("Levels {r} {g} {b} {w}".format(**locals()))
		device_address = self._settings.get_int(["device_address"])
		self.set_levels(device_address, r, g, b, w)

	# After https://stackoverflow.com/questions/29643352/converting-hex-to-rgb-value-in-python
	@staticmethod
	def html_to_rgb(html_colour):
		rgb_hex = html_colour.lstrip('#')
		lv = len(rgb_hex)
		return tuple(int(rgb_hex[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

	# After https://stackoverflow.com/questions/40312216/converting-rgb-to-rgbw
	def rgb_to_rgbw(self, r_i, g_i, b_i):

		# Get the maximum between R, G, and B
		t_m = max(r_i, g_i, b_i)
		# If the maximum value is 0, immediately return pure black.
		if t_m == 0:
			return 0, 0, 0, 0

		# This section serves to figure out what the color with 100% hue is
		multiplier = 255 / t_m
		r_h = r_i * multiplier
		b_h = g_i * multiplier
		g_h = b_i * multiplier

		# This calculates the Whiteness (not strictly speaking Luminance) of the color
		max_h = max(r_h, g_h, b_h)
		min_h = min(r_h, g_h, b_h)
		luminance = ((max_h + min_h) / 2 - 127.5) * (255 / 127.5) / multiplier

		# Calculate the output values
		w_o = int(luminance)
		r_o = int(r_i - luminance)
		g_o = int(g_i - luminance)
		b_o = int(b_i - luminance)

	# Clamp them so that they are all between 0 and 255
		w_o = self.clamp(w_o, 0, 255)
		r_o = self.clamp(r_o, 0, 255)
		g_o = self.clamp(g_o, 0, 255)
		b_o = self.clamp(b_o, 0, 255)

		return r_o, g_o, b_o, w_o

	@staticmethod
	def clamp(val, min_val, max_val):
		return max(min_val, min(val, max_val))

	@staticmethod
	def set_levels(addr, r, g, b, w):
		with SMBus(1) as bus:
			bus.write_byte_data(addr, 0, r)
			bus.write_byte_data(addr, 1, g)
			bus.write_byte_data(addr, 2, b)
			bus.write_byte_data(addr, 3, w)

	def get_assets(self):
		# Define your plugin's asset files to automatically include in the
		# core UI here.
		return dict(
			js=["js/BuildLeds.js"],
			css=["css/BuildLeds.css"],
			less=["less/BuildLeds.less"]
		)

	##~~ Softwareupdate hook

	def get_update_information(self):
		# Define the configuration for your plugin to use with the Software Update
		# Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
		# for details.
		return dict(
			BuildLeds=dict(
				displayName="Buildleds Plugin",
				displayVersion=self._plugin_version,

				# version check: github repository
				type="github_release",
				user="andyjduncan",
				repo="OctoPrint-Buildleds",
				current=self._plugin_version,

				# update method: pip
				pip="https://github.com/andyjduncan/OctoPrint-Buildleds/archive/{target_version}.zip"
			)
		)


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Buildleds Plugin"

# Starting with OctoPrint 1.4.0 OctoPrint will also support to run under Python 3 in addition to the deprecated
# Python 2. New plugins should make sure to run under both versions for now. Uncomment one of the following
# compatibility flags according to what Python versions your plugin supports!
# __plugin_pythoncompat__ = ">=2.7,<3" # only python 2
__plugin_pythoncompat__ = ">=3,<4"  # only python 3


# __plugin_pythoncompat__ = ">=2.7,<4" # python 2 and 3

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = BuildledsPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
	}
