from env.core.environment import CodeReview
from env.core.models import Action


# ─────────────────────────────────────────
# Hardcoded action sequences per difficulty
# Simulates what an LLM agent would do
# ─────────────────────────────────────────

EPISODE_ACTIONS = {

    'easy': [
        # Bug 1 — line 5, incorrect_return
        Action(
            action_type = 'identify_issue',
            line_number = 5,
            issue_type  = 'incorrect_return',
            description = 'returns i instead of -1 when target not found'
        ),
        Action(
            action_type = 'suggest_fix',
            line_number = 5,
            suggestion  = '    return -1'
        ),
        # All bugs addressed — approve
        Action(action_type = 'approve'),
    ],

    'medium': [
        # Bug 1 — line 5, division_by_zero
        Action(
            action_type = 'identify_issue',
            line_number = 5,
            issue_type  = 'division_by_zero',
            description = 'no check for empty list before dividing'
        ),
        Action(
            action_type = 'suggest_fix',
            line_number = 5,
            suggestion  = '    if not numbers:\n        return 0'
        ),
        # Bug 2 — line 8, incorrect_initialization
        Action(
            action_type = 'identify_issue',
            line_number = 8,
            issue_type  = 'incorrect_initialization',
            description = 'max_val starts at 0, fails for negative numbers'
        ),
        Action(
            action_type = 'suggest_fix',
            line_number = 8,
            suggestion  = '    max_val = numbers[0]'
        ),
        # All bugs addressed — approve
        Action(action_type = 'approve'),
    ],

    'hard': [
        # Bug 1 — line 3, off_by_one
        Action(
            action_type = 'identify_issue',
            line_number = 3,
            issue_type  = 'off_by_one',
            description = 'right should be len(arr)-1 not len(arr)'
        ),
        Action(
            action_type = 'suggest_fix',
            line_number = 3,
            suggestion  = '    right = len(arr) - 1'
        ),
        # Bug 2 — line 4, off_by_one
        Action(
            action_type = 'identify_issue',
            line_number = 4,
            issue_type  = 'off_by_one',
            description = 'while condition should be left <= right'
        ),
        Action(
            action_type = 'suggest_fix',
            line_number = 4,
            suggestion  = '    while left <= right:'
        ),
        # Bug 3 — line 5, type_error
        Action(
            action_type = 'identify_issue',
            line_number = 5,
            issue_type  = 'type_error',
            description = 'division gives float index, use // instead of /'
        ),
        Action(
            action_type = 'suggest_fix',
            line_number = 5,
            suggestion  = '        mid = (left + right) // 2'
        ),
        # Bug 4 — line 9, infinite_loop
        Action(
            action_type = 'identify_issue',
            line_number = 9,
            issue_type  = 'infinite_loop',
            description = 'left = mid never advances pointer, infinite loop'
        ),
        Action(
            action_type = 'suggest_fix',
            line_number = 9,
            suggestion  = '            left = mid + 1'
        ),
        # Bug 5 — line 11, infinite_loop
        Action(
            action_type = 'identify_issue',
            line_number = 11,
            issue_type  = 'infinite_loop',
            description = 'right = mid never retreats pointer, infinite loop'
        ),
        Action(
            action_type = 'suggest_fix',
            line_number = 11,
            suggestion  = '            right = mid - 1'
        ),
        # All bugs addressed — approve
        Action(action_type = 'approve'),
    ]
}


# ─────────────────────────────────────────
# Run one episode for a given difficulty
# ─────────────────────────────────────────

def run_episode(difficulty: str) -> dict:
    print(f'\n{"="*50}')
    print(f'TASK: {difficulty.upper()}')
    print(f'{"="*50}')

    env         = CodeReview(difficulty=difficulty)
    observation = env.reset()
    total_reward = 0
    done         = False
    step_num     = 0

    print(f'\nCode:\n{observation.code}')
    print(f'Total bugs to find: {observation.total_bugs}')

    actions = EPISODE_ACTIONS[difficulty]

    while not done:

        # Get next action from sequence
        if step_num < len(actions):
            action = actions[step_num]
        else:
            # Fallback — force approve if we run out of actions
            action = Action(action_type='approve')

        # Take step
        observation, reward, done, info = env.step(action)
        total_reward += reward
        step_num     += 1

        # Print step info
        print(f'\n--- Step {observation.current_step} ---')
        print(f'Action     : {action.action_type}', end='')
        if action.line_number:
            print(f' | line {action.line_number}', end='')
        if action.issue_type:
            print(f' | type: {action.issue_type}', end='')
        if action.suggestion:
            print(f' | fix: {action.suggestion[:30]}...', end='')
        print()
        print(f'Reward     : {round(reward, 4)}')
        print(f'Meta       : {info["meta"]}')
        print(f'Addressed  : {observation.bugs_addressed}/{observation.total_bugs}')
        print(f'Can approve: {observation.can_approve}')
        print(f'Done       : {done}')

    # Get final grader score
    grader_score = env.grade()

    print(f'\n{"─"*40}')
    print(f'EPISODE COMPLETE — {difficulty.upper()}')
    print(f'Total Reward : {round(total_reward, 4)}')
    print(f'Grader Score : {grader_score}  (0.0 - 1.0)')
    print(f'{"─"*40}')

    return {
        'difficulty'  : difficulty,
        'total_reward': round(total_reward, 4),
        'grader_score': grader_score
    }


# ─────────────────────────────────────────
# Run all 3 tasks and print summary
# ─────────────────────────────────────────

if __name__ == '__main__':

    print('CODE REVIEW ENVIRONMENT — BASELINE')
    print('Running all 3 difficulty levels...')

    results = []
    for difficulty in ['easy', 'medium', 'hard']:
        result = run_episode(difficulty)
        results.append(result)

    # Final summary
    print(f'\n{"="*50}')
    print('BASELINE SUMMARY')
    print(f'{"="*50}')
    print(f'{"Difficulty":<12} {"Total Reward":<15} {"Grader Score"}')
    print(f'{"─"*40}')
    for r in results:
        print(
            f'{r["difficulty"]:<12} '
            f'{r["total_reward"]:<15} '
            f'{r["grader_score"]}'
        )

    avg_score = sum(r['grader_score'] for r in results) / len(results)
    print(f'{"─"*40}')
    print(f'Average Grader Score: {round(avg_score, 4)}')
    print(f'{"="*50}')