from threading import Lock
from copy import copy
from .helpers import TRANSPARENT

class ZoneManager:
	__slots__ = ('zones', 'color_map', 'temporary_zones', 'text_areas', 'lock')

	def __init__(self):
		self.zones = {}
		self.color_map = {}
		self.temporary_zones = []
		self.text_areas = []
		self.lock = Lock()
	
	def add_zone(self, zone):
		with self.lock:
			zone_id = len(self.zones)
			zone.id = zone_id
			self.zones[zone_id]=zone
			zone.add_to_map(self.color_map, zone_id)

	def add_temporary_zone(self, zone):
		self.add_zone(zone)
		with self.lock:
			self.temporary_zones.append(zone)

	def add_text_area(self, area):
		with self.lock:
			self.text_areas.append(area)

	def update_text_area_text(self, index: int, text: str):
		with self.lock:
			self.text_areas[index].text = text

	def remove_temporary_zones(self):
		with self.lock:
			for zone in self.temporary_zones:
				self.remove_zone(zone)
			self.temporary_zones.clear()

	def remove_zone(self, zone):
		with self.lock:
			self.zones.pop(zone.id)
			zone.remove_from_map(self.color_map)

	def deactivate_zones(self):
		zones = self.copy_zones()
		for c in self.zones:
			zones[c].deactivate()

	def click(self, id):
		zones = self.copy_zones()
		zones[id].click()

	def update(self, activeID):
		zones = self.copy_zones()
		for zoneID, zone in zones.items():
			zone.update(zoneID==activeID)

	def get_color(self, x, y):
		with self.lock:
			color = self.color_map.get((x,y), TRANSPARENT)
			if color not in self.zones:
				return None
			return color

	def clear(self):
		with self.lock:
			self.zones = {}
			self.color_map = {}
			self.temporary_zones = []
			self.text_areas = []

	def copy_text_areas(self):
		return self._copy(self.text_areas)

	def copy_zones(self):
		return self._copy(self.zones)

	def copy_temporary_zones(self):
		return self._copy(self.temporary_zones)

	def copy_color_map(self):
		return self._copy(self.color_map)

	def _copy(self, structure):
		with self.lock:
			return copy(structure)