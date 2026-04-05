import difflib
from env.core.models import Observation, Action, Internal_state
from env.tasks.task import tasks
from env.utils.codebleu import CodeBLEU


class CodeReview():

    # Class level constants
    VALID_ACTIONS = ['identify_issue', 'suggest_fix', 'approve']

    def __init__(self, difficulty: str = 'easy'):
        self.task = tasks[difficulty]
        self._state = None
        self.codebleu = CodeBLEU()

        # Action handlers — clean dispatch instead of if/elif
        self._action_handlers = {
            'identify_issue': self._handle_identify,
            'suggest_fix'   : self._handle_fix,
            'approve'       : self._handle_approve
        }

    # ─────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────

    def reset(self) -> Observation:
        self._state = Internal_state(
            code              = self.task['buggy_code'],
            language          = self.task.get('language', 'python'),
            task_id           = self.task['task_id'],
            difficulty        = self.task['difficulty'],
            true_issues       = self.task['true_issues'],
            identified_issues = [],
            fixes_applied     = [],
            history           = [],
            step_count        = 0,
            max_steps         = self.task['max_steps'],
            done              = False,

            # Registry — one entry per bug
            issue_registry    = {
                issue['line']: {
                    'issue'          : issue,
                    'addressed'      : False,
                    'identified'     : False,
                    'fixed'          : False,
                    'identify_score' : 0.0,
                    'fix_score'      : 0.0,
                }
                for issue in self.task['true_issues']
            }
        )
        return self._get_observations()


    def step(self, action: Action):
        reward = 0.0

        # Step penalty — encourages efficiency
        reward -= 0.1

        # Guard — episode already over
        if self._state.done:
            return self._get_observations(), reward, True, {
                'meta': 'Episode already done'
            }

        # Guard — invalid action type
        if action.action_type not in self.VALID_ACTIONS:
            return self._get_observations(), -0.5, False, {
                'meta': f'Invalid action. Must be one of {self.VALID_ACTIONS}'
            }

        # Guard — invalid line number
        if action.line_number is not None and action.line_number <= 0:
            return self._get_observations(), -0.3, False, {
                'meta': 'Line number must be positive'
            }

        # Dispatch to correct handler
        handler = self._action_handlers[action.action_type]
        action_reward, done, meta = handler(action)
        reward += action_reward

        # Update history
        self._state.step_count += 1
        self._state.history.append({
            'step'       : self._state.step_count,
            'action_type': action.action_type,
            'line_number': action.line_number,
        })

        # Check max steps
        if self._state.step_count >= self._state.max_steps:
            self._state.done = True
            meta += ' | Max steps reached'

        if done:
            self._state.done = True

        return self._get_observations(), reward, self._state.done, {
            'meta': meta
        }


    def get_state(self):
        return self._state


    # ─────────────────────────────────────────
    # ACTION HANDLERS
    # ─────────────────────────────────────────

    def _handle_identify(self, action: Action):
        """
        Agent identifies a bug at a line.
        Uses 3 layer scoring:
          Layer 1 — line number (most important)
          Layer 2 — issue type similarity via difflib
          Layer 3 — description similarity via difflib (bonus)
        Returns (reward, done, meta)
        """

        # Validate required fields
        if action.line_number is None or action.issue_type is None:
            return -0.5, False, 'Missing line_number or issue_type'

        identified_line = action.line_number
        identified_type = action.issue_type.lower().strip()
        identified_desc = (action.description or '').lower().strip()

        # Find best matching bug in registry
        best_line  = None
        best_score = 0.0

        for line, entry in self._state.issue_registry.items():
            true_issue = entry['issue']

            # Layer 1 — Line score (most important)
            if identified_line == line:
                line_score = 1.0
            elif abs(identified_line - line) == 1:
                line_score = 0.5
            else:
                continue   # too far off, skip this issue

            # Layer 2 — Issue type similarity
            type_score = difflib.SequenceMatcher(
                None,
                identified_type,
                true_issue['issue_type'].lower()
            ).ratio()

            # Layer 3 — Description similarity (bonus)
            true_desc = true_issue.get('description', '').lower()
            if identified_desc and true_desc:
                desc_score = difflib.SequenceMatcher(
                    None,
                    identified_desc,
                    true_desc
                ).ratio()
            else:
                desc_score = 0.0

            # Weighted combination
            total_score = (
                0.5 * line_score +
                0.3 * type_score +
                0.2 * desc_score
            )

            if total_score > best_score:
                best_score = total_score
                best_line  = line

        # No matching bug found anywhere
        if best_line is None:
            return -0.3, False, 'No matching bug found for that line'

        entry = self._state.issue_registry[best_line]

        # Duplicate check
        if entry['identified']:
            return -0.2, False, f'Already identified bug at line {best_line}'

        # Mark in registry
        entry['addressed']      = True
        entry['identified']     = True
        entry['identify_score'] = best_score

        # Add to identified list
        self._state.identified_issues.append({
            'line'      : identified_line,
            'issue_type': identified_type,
            'score'     : best_score
        })

        reward = best_score * 0.4   # max 0.4 for perfect match
        return (
            reward,
            False,
            f'Issue identified at line {best_line} '
            f'with score {round(best_score, 2)}'
        )


    def _handle_fix(self, action: Action):
        """
        Agent suggests a fix for an identified bug.
        Scores using CodeBLEU (with difflib fallback).
        Local score  = fix vs expected_fix
        Global score = patched_code vs reference_code
        Returns (reward, done, meta)
        """

        # Validate required fields
        if (action.line_number is None or
            action.suggestion is None or
            action.suggestion.strip() == ''):
            return -0.5, False, 'Missing line_number or suggestion'

        # Validate line in bounds
        max_lines = len(self._state.code.split('\n'))
        if action.line_number > max_lines:
            return -0.3, False, 'Line number out of bounds'

        # Must identify before fixing
        identified_lines = [
            i['line'] for i in self._state.identified_issues
        ]
        if action.line_number not in identified_lines:
            return (
                -0.5,
                False,
                'Must identify the issue before fixing it'
            )

        # Find matching issue in registry with ±1 tolerance
        best_line = None
        for line in self._state.issue_registry:
            if abs(action.line_number - line) <= 1:
                best_line = line
                break

        if best_line is None:
            return -0.3, False, 'No matching bug found for that line'

        entry      = self._state.issue_registry[best_line]
        true_issue = entry['issue']

        # Duplicate fix check
        if entry['fixed']:
            return -0.2, False, f'Already fixed bug at line {best_line}'

        # Score fix using CodeBLEU
        # Fallback to difflib if CodeBLEU fails
        try:
            local_reward = self.codebleu.score(
                code           = action.suggestion,
                reference_code = true_issue['expected_fix'],
                language       = self._state.language
            )['codebleu']
        except Exception:
            local_reward = difflib.SequenceMatcher(
                None,
                action.suggestion.strip(),
                true_issue['expected_fix'].strip()
            ).ratio()

        # If fix is good enough patch the code
        if local_reward > 0.3:
            patched_code = self._patch_code(
                self._state.code,
                action.line_number,
                action.suggestion
            )
            try:
                global_reward = self.codebleu.score(
                    code           = patched_code,
                    reference_code = self.task['reference_code'],
                    language       = self._state.language
                )['codebleu']
            except Exception:
                global_reward = 0.0

            self._state.code = patched_code
        else:
            global_reward = 0.0

        # Final fix score
        fix_score = 0.7 * local_reward + 0.3 * global_reward

        # Update registry
        entry['fixed']     = True
        entry['addressed'] = True
        entry['fix_score'] = fix_score

        # Add to fixes list
        self._state.fixes_applied.append({
            'line'         : action.line_number,
            'suggested_fix': action.suggestion,
            'score'        : fix_score
        })

        reward = 0.4 * fix_score
        return (
            reward,
            False,
            f'Fix applied at line {best_line} '
            f'with score {round(fix_score, 2)}'
        )


    def _handle_approve(self, action: Action):
        """
        Agent submits final answer.
        GATE: ALL bugs must be addressed first.
        Whether right or wrong — every bug must
        have been attempted before approving.
        Returns (reward, done, meta)
        """

        registry = self._state.issue_registry

        # ── GATE — all bugs must be addressed ──
        unaddressed = [
            line for line, entry in registry.items()
            if not entry['addressed']
        ]

        if unaddressed:
            return (
                -0.5,
                False,
                f'Cannot approve yet. '
                f'Must address bugs at lines: {unaddressed}'
            )

        # ── All addressed — calculate final reward ──
        total = len(registry)

        avg_identify = sum(
            e['identify_score'] for e in registry.values()
        ) / total

        avg_fix = sum(
            e['fix_score'] for e in registry.values()
        ) / total

        fully_correct = sum(
            1 for e in registry.values()
            if e['identify_score'] >= 0.8 and e['fix_score'] >= 0.8
        )

        # Final reward breakdown
        reward  = 0.4 * avg_identify            # identification quality
        reward += 0.4 * avg_fix                 # fix quality
        reward += 0.2 * (fully_correct / total) # bonus for perfect ones

        if fully_correct == total:
            reward += 1.0    # perfect bonus
        elif fully_correct == 0:
            reward -= 0.3    # penalty if nothing was correct

        return (
            reward,
            True,
            f'Episode complete. '
            f'Correct: {fully_correct}/{total}. '
            f'Identify avg: {round(avg_identify, 2)}. '
            f'Fix avg: {round(avg_fix, 2)}'
        )


    # ─────────────────────────────────────────
    # GRADER — always returns 0.0 to 1.0
    # ─────────────────────────────────────────

    def grade(self) -> float:
        """
        Final grader score for this episode.
        40% weight on identification quality
        60% weight on fix quality
        Always returns between 0.0 and 1.0
        """
        registry = self._state.issue_registry
        total    = len(registry)
        score    = 0.0

        for entry in registry.values():
            issue_score  = 0.4 * entry.get('identify_score', 0.0)
            issue_score += 0.6 * entry.get('fix_score', 0.0)
            score += issue_score

        return round(score / total, 4)


    # ─────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────

    def _patch_code(
        self,
        code       : str,
        line_number: int,
        new_line   : str
    ) -> str:
        """Replace a specific line in the code."""
        lines = code.split('\n')
        if line_number < 1 or line_number > len(lines):
            return code
        lines[line_number - 1] = new_line
        return '\n'.join(lines)


    def _get_observations(self) -> Observation:
        """
        Build observation from current state.
        Agent sees code, progress, and 
        whether it can approve yet.
        """
        registry  = self._state.issue_registry
        total     = len(registry)
        addressed = sum(
            1 for e in registry.values()
            if e['addressed']
        )

        return Observation(
            # Core info
            code              = self._state.code,
            language          = self._state.language,
            task_id           = self._state.task_id,
            difficulty        = self._state.difficulty,

            # Step info
            current_step      = self._state.step_count,
            max_steps         = self._state.max_steps,

            # History
            history           = self._state.history,

            # Available actions
            available_actions = self.VALID_ACTIONS,

            # Agent's own progress
            identified_issues = self._state.identified_issues,
            fixes_applied     = self._state.fixes_applied,

            # Bug progress
            total_bugs        = total,
            bugs_addressed    = addressed,

            # Can agent approve?
            can_approve       = (addressed == total)
        )