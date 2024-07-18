# version 1.0.1
* Added xdist_worker_id to TestItemData as well
* Changed logger to be on the module name instead of the root logger
* fixed some broken tests that were mistakenly passing
* Catching exceptions from all reporters, so that the flow won't break
# version 1.0.0
* Added check for release notes
* Added two utility functions: get_test_session_data & get_test_item_data
* Added a field xdist_worker_id in TestSessionItem - None if there is no such env variable
# version 0.0.3
Fix bug with xdist having a null testrunid, add session start and end to TestSessionData
# version 0.0.2
relax pytest dependency from 8.2.2 to 8.0.0
# version 0.0.1
First release. Collects metadata, comes with a default text reporter.