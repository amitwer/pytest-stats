# Pytest-stats
This library is collecting metadata about your test executions, and enables you to send it to a datastore of your liking.

## Architecture
The library is designed in a hexagonal architecture in mind - separating data collection and reporting.
There are two main parts to the code - metadata collection and reporting. the collection engine stores the metadata in pytest's stash (for session and for test) and uses pytest built-in hooks in order to populate the data and trigger the reporting. 
The reporting part is allowing reporters to register, then delegates the actual work to the registered reporters, enabling easy customization. 

## Implementation guide
In order to include pytest-stats capabilities in your code, all you need to do is to install the package `pip install pytest-stats`.  
However, this will only provide you with a text report provided by the built-in DefaultTextReporter.
In order to store the data in your own DB you'll need to:  
1. Create a new reporter (inherit the abstract `ResultsReporter` class)
2. Register an instance of your reporter using the provided new hook `pytest_stats_register_reporters`.<br>Example: 
```
@pytest.hookimpl()
def pytest_stats_register_reporters(reporters:'ReportersRegistry'):
    reporters.register(MyReporter())
```

## Implementation details
### how is data collected and reported?
Most data is collected by hooking the following pytest-provided hooks:
* `pytest_sessionstart`
* `pytest_sessionfinish`
* `pytest_runtest_protocol`
* `pytest_runtest_makereport`
* `pytest_exception_interact`
### New hooks available
* `pytest_stats_register_reporters`: used to register a new reporter. More than one reporter can be registered at the same hook. <br> Invoked as part of `pytest_configure`
* `pytest_stats_env_data`: Enables adding custom environment information to the session data. <br> Invoked as part of `pytest_sessionstart`

### Utility functions
* `get_test_session_data(session: 'Session') -> TestSessionData` - can be used to fetch the session data in an arbitrary location
* `get_test_item_data(item: 'Item') -> TestItemData` - can be used to fetch the current test data in arbitrary location. For instance, one can call `get_test_item_data(item=request.node).foo="bar"`
* 