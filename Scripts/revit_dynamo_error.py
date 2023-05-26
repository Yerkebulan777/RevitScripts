#
# Revit Batch Processor
#
# Copyright (c) 2020  Dan Rumery, BVN
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#

DYNAMO_REVIT_MODULE_NOT_FOUND_ERROR_MESSAGE = "Could not load the Dynamo module! There must be EXACTLY ONE VERSION of Dynamo installed!"


def IsDynamoNotFoundException(exception):
    return (
            isinstance(exception, Exception)
            and
            e.message3 == DYNAMO_REVIT_MODULE_NOT_FOUND_ERROR_MESSAGE
    )
