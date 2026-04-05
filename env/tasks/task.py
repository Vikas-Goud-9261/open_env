# env/tasks/tasks.py

# ─────────────────────────────────────────
# EASY TASK — 1 bug, obvious, simple function
# Agent should solve this in ~4 steps
# ─────────────────────────────────────────

easy_task = {
    'task_id'   : 'easy_001',
    'difficulty': 'easy',
    'language'  : 'python',
    'max_steps' : 10,

    'buggy_code': """\
def linear_search(arr, target):
    for i in range(len(arr)):
        if arr[i] == target:
            return i
    return i
""",

    'reference_code': """\
def linear_search(arr, target):
    for i in range(len(arr)):
        if arr[i] == target:
            return i
    return -1
""",

    'true_issues': [
        {
            'line'        : 5,
            'issue_type'  : 'incorrect_return',
            'description' : 'Function returns i instead of -1 when target is not found',
            'expected_fix': '    return -1'
        }
    ]
}


# ─────────────────────────────────────────
# MEDIUM TASK — 2 bugs, moderate complexity
# Agent should solve this in ~8 steps
# ─────────────────────────────────────────

medium_task = {
    'task_id'   : 'medium_001',
    'difficulty': 'medium',
    'language'  : 'python',
    'max_steps' : 20,

    'buggy_code': """\
def calculate_average(numbers):
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)

def find_max(numbers):
    max_val = 0
    for num in numbers:
        if num > max_val:
            max_val = num
    return max_val
""",

    'reference_code': """\
def calculate_average(numbers):
    total = 0
    for num in numbers:
        total += num
    if not numbers:
        return 0
    return total / len(numbers)

def find_max(numbers):
    max_val = numbers[0]
    for num in numbers:
        if num > max_val:
            max_val = num
    return max_val
""",

    'true_issues': [
        {
            'line'        : 5,
            'issue_type'  : 'division_by_zero',
            'description' : 'No check for empty list before dividing by len(numbers)',
            'expected_fix': '    if not numbers:\n        return 0'
        },
        {
            'line'        : 8,
            'issue_type'  : 'incorrect_initialization',
            'description' : 'max_val initialized to 0, fails for all negative number lists',
            'expected_fix': '    max_val = numbers[0]'
        }
    ]
}


# ─────────────────────────────────────────
# HARD TASK — 4 bugs, tricky logic
# Agent should solve this in ~15 steps
# Even GPT-4 might struggle with all 4
# ─────────────────────────────────────────

hard_task = {
    'task_id'   : 'hard_001',
    'difficulty': 'hard',
    'language'  : 'python',
    'max_steps' : 30,

    'buggy_code': """\
def binary_search(arr, target):
    left = 0
    right = len(arr)
    while left < right:
        mid = (left + right) / 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid
        else:
            right = mid
    return -1
""",

    'reference_code': """\
def binary_search(arr, target):
    left = 0
    right = len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1
""",

    'true_issues': [
        {
            'line'        : 3,
            'issue_type'  : 'off_by_one',
            'description' : 'right should be len(arr)-1 not len(arr), causes index out of bounds',
            'expected_fix': '    right = len(arr) - 1'
        },
        {
            'line'        : 4,
            'issue_type'  : 'off_by_one',
            'description' : 'while condition should be left <= right not left < right, misses single element',
            'expected_fix': '    while left <= right:'
        },
        {
            'line'        : 5,
            'issue_type'  : 'type_error',
            'description' : 'Division gives float index, use integer division // instead of /',
            'expected_fix': '        mid = (left + right) // 2'
        },
        {
            'line'        : 9,
            'issue_type'  : 'infinite_loop',
            'description' : 'left = mid never advances left pointer, causes infinite loop',
            'expected_fix': '            left = mid + 1'
        },
        {
            'line'        : 11,
            'issue_type'  : 'infinite_loop',
            'description' : 'right = mid never retreats right pointer, causes infinite loop',
            'expected_fix': '            right = mid - 1'
        }
    ]
}


# ─────────────────────────────────────────
# Task registry — environment loads from here
# ─────────────────────────────────────────

tasks = {
    'easy'  : easy_task,
    'medium': medium_task,
    'hard'  : hard_task,
}