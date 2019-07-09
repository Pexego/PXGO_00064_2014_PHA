.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

============================
MRP BoM - Export attachments
============================

This module adds a new menu option under "Bill Of Material", only visible to admin users.
The purpose of this module is to extract all attachments of each BoM to a external directory specified by user.
When export process initiates, the module creates a new directory structure based on final product of BoM attributes:

base-directory/line/subline/container_base-form_clothing_qty/product-name_01.file-extension

Where underscore character will be added as separator.


Credits
=======

Pharmadus I.T.
