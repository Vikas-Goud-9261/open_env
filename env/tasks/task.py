task = {
  "task_id": "task_1",

  "buggy_code": """
    for i in range(len(arr)):
        if arr[i] == target:
          return i
    return i
    """,

  "reference_code" : "",
  "true_issues": [
    {
      "line": 4,
      "issue_type": "incorrect_return",
      "expected_fix": "return -1"
    }
  ],

  "max_steps": 5
}
