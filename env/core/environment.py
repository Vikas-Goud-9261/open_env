from env.core.models import Observation, Action, Internal_state
from env.tasks.task import task
from env.utils.codebleu import CodeBLEU

class CodeReview():

    def __init__(self):
        self.task = task
        self.state = None
        self.codebleu = CodeBLEU()

    
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
            return self._get_observations(), reward, self.state.done, {'meta' : 'Done is True'}

        if action.action_type not in VALID_ACTIONS:
            return self._get_observations(), -0.5, self.state.done, {'meta' : 'Actions not in valid actions'}

        if action.line_number is not None and action.line_number <= 0 :
            return self._get_observations(), -0.3, self.state.done, {'meta' : 'Invalid line number by action'}

        true_issues = self.state.true_issues

        if action.action_type == 'identify_issue':
            if action.line_number is None or action.issue_type is None:
                return self._get_observations(), -0.5, self.state.done, {'meta' : 'No line number or issue type in the action for identifying issue'}

            identified_line = action.line_number
            identified_issue = action.issue_type
            found = False
            for issue in true_issues:
                if identified_line == issue['line'] and identified_issue == issue['issue_type']:

                    already_found_issue = any(
                        iss['line'] == identified_line and iss['issue_type'] == identified_issue for iss in self.state.identified_issues
                    )

                    if already_found_issue:
                        return self._get_observations(), -0.2, self.state.done, {'meta' : 'Duplicate issue'}
                    else:
                        reward += 0.4
                        self.state.identified_issues.append({
                            'line' : identified_line,
                            'issue_type' : identified_issue
                        })
                    found = True
                    break

            if not found:
                reward -= 0.3

        elif action.action_type == 'suggest_fix':
            if action.line_number is None or action.suggestion is None or action.suggestion.strip() == "":
                return self._get_observations(), -0.5, self.state.done, {'meta' : 'No line number or suggestion in suggest fix. Maybe empty suggestion?'}

            max_lines = len(self.state.code.split("\n"))
            if action.line_number > max_lines:
                return self._get_observations(), -0.3, self.state.done , {'meta' : 'Line number excedded out of bound'}

            identified_lines = [i['line'] for i in self.state.identified_issues]
            if action.line_number not in identified_lines:    
                return self._get_observations(), -0.5, self.state.done, {'meta' : 'Trying to fix an issue not present in identified issues or trying to fix an issue before identifying it'}
            
            identified_fixes = action.suggestion
            found = False
            for issue in true_issues:
                
                if issue['expected_fix'] in identified_fixes:

                    already_fixed_issue = any(
                        fix['line'] == action.line_number and fix['suggested_fix'] == action.suggestion for fix in self.state.fixes_applied
                    )
                    if already_fixed_issue:
                        return self._get_observations(), -0.2 , self.state.done, {'meta' : 'Duplicate fix'}

                    else:
                        local_reward = self.codebleu.score(code = action.suggestion, reference_code = issue['expected_fix'], language = self.state.language)['codebleu']

                        if local_reward > 0.3:
                            patched_code = self._patch_code(self.state.code, action.line_number, action.suggestion)
                            global_reward = self.codebleu.score(patched_code, self.task['reference_code'], language = self.state.language)['codebleu']
                            self.state.code = patched_code
                        else :
                            global_reward = 0.0

                        final_score = 0.7*local_reward + 0.3*global_reward
                        reward += 0.4*final_score

                        self.state.fixes_applied.append({
                            'line' : action.line_number,
                            'suggested_fix' : action.suggestion
                        })
                    found = True
                    break
            if not found:
                reward -= 0.3


        elif action.action_type == 'approve':
            correct = 0
            total = len(true_issues)
            
            if len(self.state.identified_issues) == 0:
                reward -= 0.4

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

            if correct > 0:
                candidate_code = self.state.code
                reference_code = self.task['reference_code']
                approval_cb_score = self.codebleu.score(candidate_code, reference_code, language = self.state.language)['codebleu']
                reward += 0.2*approval_cb_score

            if correct == total:
                reward += 1.0
            else:
                reward -= 0.6


        self.state.step_count += 1
        self.state.history.append(action.action_type)

        if action.action_type == 'approve':
            self.state.done = True

        if self.state.step_count >= self.state.max_steps:
            self.state.done = True

        return self._get_observations(), reward, self.state.done, {'meta' : 'everything ran smoothly and we return this after each step ends.'}
        


    def state(self):
        return self.state

    def _patch_code(self, code:str, line_number:int, new_line:str) -> str:
        lines = code.split('\n')

        if line_number< 1 or line_number > len(lines):
            return code
        
        lines[line_number - 1] = new_line
        patched_code = '\n'.join(lines)
        return patched_code

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



            


        
