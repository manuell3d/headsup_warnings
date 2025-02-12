# ====================== BEGIN GPL LICENSE BLOCK ======================
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ======================= END GPL LICENSE BLOCK ========================

bl_info = {
    "name": "HeadsUp Warnings",
    "description": "Temporarily change UI colors and overlay a text with warnings about potentially destructive Blender settings",
    "author": "Manuel Lüllau",
    "version": (1, 0, 2),
    "blender": (4, 2, 0),
    'location': 'Somewhere',
    'category': '3D View',
    'support': 'COMMUNITY',
    }

from . import panels, handlers, operators, preferences, properties

def register():
    properties.register()
    preferences.register()
    operators.register()
    panels.register()
    handlers.register()
    

def unregister():
    handlers.warning(False)
    handlers.unregister()
    panels.unregister()
    operators.unregister()
    preferences.unregister()
    properties.unregister()
    
if __name__ == "__main__":
    register()