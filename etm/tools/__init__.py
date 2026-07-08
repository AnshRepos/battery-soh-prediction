"""ETM Tools package — aggregates all tool classes into ETMToolsManager."""

from tools.bulk_tools import BulkTools
from tools.connection_tools import ConnectionTools
from tools.execution_tools import ExecutionTools
from tools.linking_tools import LinkingTools
from tools.misc_tools import MiscTools
from tools.testcase_tools import TestCaseTools
from tools.testplan_tools import TestPlanTools
from tools.testsuite_tools import TestSuiteTools
from tools.traceability_tools import TraceabilityTools


class ETMToolsManager(
    ConnectionTools,
    TestPlanTools,
    TestCaseTools,
    TestSuiteTools,
    ExecutionTools,
    LinkingTools,
    TraceabilityTools,
    BulkTools,
    MiscTools,
):
    """Aggregated ETM tools manager combining all tool groups.

    Inherits tool methods from:
      - ConnectionTools:   project connection, OSLC queries, resource access
      - TestPlanTools:     test plan CRUD and statistics
      - TestCaseTools:     test case CRUD, categories, custom attributes, XML fix
      - TestSuiteTools:    test suite CRUD
      - ExecutionTools:    execution results, records, attachments, templates
      - LinkingTools:      linking test cases/suites/plans, defect linking
      - TraceabilityTools: plan trees, timelines, requirement mapping, orphan detection
      - BulkTools:         batch test case creation and execution
      - MiscTools:         test scripts, build records, configurations, execution records
    """

    pass
