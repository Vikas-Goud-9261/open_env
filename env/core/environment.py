from env.core.models import Observation, Action, Internal_state
from env.tasks.task import task

class CodeReview():

    def __init__(self):
        self.task = task
        self.state = None

    
    def reset(self) -> Observation:
        print(type(self.task['task_id']))
        self.state = Internal_state(
            code = self.task['buggy_code'],
            language = 'python',
            task_id = self.task['task_id'],
            difficulty = 'easy',
            true_issues = self.task['true_issues'],
            identified_issues = [],
            fixes_applied = [],
            history = [],
            step_count = 0,
            max_steps = self.task['max_steps'],
            done = False
        )

        return self._get_observations()

    def step(self, action: Action):
        reward = 0.0
        VALID_ACTIONS = ['identify_issue', 'suggest_fix', 'approve']
        reward -= 0.1

        if self.state.done:
            return self._get_observations(), reward, self.state.done, {}

        if action.action_type not in VALID_ACTIONS:
            return self._get_observations(), -0.5, self.state.done, {}

        if action.line_number is not None and action.line_number <= 0 :
            return self._get_observations(), -0.3, self.state.done, {}

        true_issues = self.state.true_issues

        if action.action_type == 'identify_issue':
            if action.line_number is None or action.issue_type is None:
                return self._get_observations(), -0.5, self.state.done, {}

            identified_line = action.line_number
            identified_issue = action.issue_type
            found = False
            for issue in true_issues:
                if identified_line == issue['line'] and identified_issue == issue['issue_type']:
                    reward += 0.4
                    self.state.identified_issues.append({
                        'line' : identified_line,
                        'issue_type' : identified_issue
                    })
                    found = True
                    break

            if not found:
                reward -= 0.2

        elif action.action_type == 'suggest_fix':
            if action.line_number is None or action.suggestion is None:
                return self._get_observations, -0.5, self.state.done, {}

            identified_fixes = action.suggestion
            found = False
            for issue in true_issues:
                if issue['expected_fix'] in identified_fixes:
                    reward += 0.4
                    self.state.fixes_applied.append({
                        'line' : action.line_number,
                        'suggested_fix' : action.suggestion
                    })
                    found = True
                    break
            if not found:
                reward -= 0.2


        elif action.action_type == 'approve':
            correct = 0
            total = len(true_issues)

            for issue in true_issues:

                issue_found = any(
                    iss['line'] == issue['line'] and iss['issue_type'] == issue['issue_type'] for iss in self.state.identified_issues
                )

                fix_found = any(
                    fix['line'] == issue['line'] and issue['expected_fix'] in fix['suggested_fix'] for fix in self.state.fixes_applied
                )

                if issue_found and fix_found:
                    correct += 1

            reward += correct/total


        self.state.step_count += 1
        self.state.history.append(action.action_type)
        
        if action.action_type == 'approve':
            self.state.done = True

        if self.state.step_count >= self.state.max_steps:
            self.state.done = True

        return self._get_observations(), reward, self.state.done, {}
        


    def state(self):
        return self.state

    def _get_observations(self) -> Observation:
        observation = Observation(
            code = self.state.code,
            language = self.state.language,
            task_id = self.state.task_id,
            difficulty = self.state.difficulty,
            history = self.state.history,
            current_step = self.state.step_count,
            max_steps = self.state.max_steps,
            available_actions =['identify_issue', 'suggest_fix', 'approve'],
        )
        return observation



            


        
