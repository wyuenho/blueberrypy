0.5.4dev

* Fixed various errors when for projects generated without SQLAlchemy enabled
* Fixed regression in to_collection()

0.5.3

* Rewrote to_collection/from_collection to support fully recursive conversions
* Deprecated to_mapping/from_mapping, they are now aliases to to_collection/from_collection
