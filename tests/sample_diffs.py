"""
Sample git diff fixtures representing realistic real-world pull requests
for testing the Automated Code Review Board multi-agent system.
"""

# Scenario 1: Clean, well-documented, tested code change
CLEAN_DIFF = """diff --git a/src/math_utils.py b/src/math_utils.py
new file mode 100644
index 0000000..e69de29
--- /dev/null
+++ b/src/math_utils.py
@@ -0,0 +1,15 @@
+\"\"\"Mathematical utility functions for statistical computations.\"\"\"
+
+def calculate_variance(numbers: list[float]) -> float:
+    \"\"\"Calculate the sample variance of a list of floating numbers.\"\"\"
+    if len(numbers) < 2:
+        raise ValueError("Variance requires at least two data points.")
+    mean = sum(numbers) / len(numbers)
+    variance = sum((x - mean) ** 2 for x in numbers) / (len(numbers) - 1)
+    return variance
diff --git a/tests/test_math_utils.py b/tests/test_math_utils.py
new file mode 100644
index 0000000..f69de29
--- /dev/null
+++ b/tests/test_math_utils.py
@@ -0,0 +1,12 @@
+\"\"\"Unit tests for math_utils module.\"\"\"
+import pytest
+from src.math_utils import calculate_variance
+
+def test_calculate_variance_valid():
+    data = [1.0, 2.0, 3.0, 4.0, 5.0]
+    assert calculate_variance(data) == 2.5
+
+def test_calculate_variance_insufficient():
+    with pytest.raises(ValueError):
+        calculate_variance([1.0])
+"""

# Scenario 2: Severe security vulnerabilities (Hardcoded AWS Secret + SQL Injection)
SECURITY_VULN_DIFF = """diff --git a/services/user_service.py b/services/user_service.py
index 1111111..2222222 100644
--- a/services/user_service.py
+++ b/services/user_service.py
@@ -10,6 +10,14 @@
 import sqlite3
 
 AWS_SECRET_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE1234567890abcdef"
+
+def query_user_profile(db_conn, user_id: str):
+    \"\"\"Query user profile details from database.\"\"\"
+    cursor = db_conn.cursor()
+    # Raw unescaped user input in query
+    query = f"SELECT id, username, email FROM users WHERE id = '{user_id}'"
+    cursor.execute(query)
+    return cursor.fetchone()
"""

# Scenario 3: Missing test suite, high cyclomatic complexity, and malformed AST syntax
COMPLEXITY_AND_MISSING_TESTS_DIFF = """diff --git a/services/order_router.py b/services/order_router.py
new file mode 100644
index 0000000..3333333
--- /dev/null
+++ b/services/order_router.py
@@ -0,0 +1,24 @@
+def route_order(order_type, is_vip, stock_count, country, has_coupon, fraud_score):
+    if order_type == 'express':
+        if is_vip:
+            if stock_count > 0:
+                if country == 'US':
+                    if has_coupon:
+                        if fraud_score < 10:
+                            return 'priority_dispatch'
+                        else:
+                            return 'fraud_review'
+                    else:
+                        return 'standard_express'
+                elif country == 'CA':
+                    return 'international_priority'
+                else:
+                    return 'overseas_routing'
+            else:
+                return 'backorder'
+        else:
+            return 'regular_queue'
+    else:
+        return 'ground_shipping'
+    
+    # Intentional unparseable syntax for honest failure test:
+    if defective syntax line here (broken indentation
+"""
