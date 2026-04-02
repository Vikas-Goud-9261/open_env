from env.core.models import Action
from env.core.environment import CodeReview
from typing import List

def run_test_case(name, actions:List[Action]):
    env = CodeReview()
    print(f"\ntest name : {name}")
    ob = env.reset()

    done = False

    for action in actions:
        print("\nAction:", action)

        ob,reward, done, data = env.step(action)
        print(f'\n Reward : {reward}')
        print(f'\n MetaData : {data}')
        print(f'\nDone : {done}')

        if done:
            break


if __name__ == '__main__':
    run_test_case("VALID FLOW", [
    Action(action_type="identify_issue", line_number=4, issue_type="incorrect_return"),
    Action(action_type="suggest_fix", line_number=4, suggestion="return -1"),
    Action(action_type="approve")
    ])

    run_test_case("INVALID ACTION TYPE", [
        Action(action_type="hack_system")
    ])

    run_test_case("MISSING FIELDS", [
    Action(action_type="identify_issue")   # missing line_number, issue_type
    ])

    run_test_case("INVALID LINE", [
    Action(action_type="identify_issue", line_number=-1, issue_type="incorrect_return")
    ])

    run_test_case("EMPTY SUGGESTION", [
    Action(action_type="suggest_fix", line_number=4, suggestion="")
    ])

    run_test_case("REPEATED ACTION", [
    Action(action_type="identify_issue", line_number=4, issue_type="incorrect_return"),
    Action(action_type="identify_issue", line_number=4, issue_type="incorrect_return"),
    Action(action_type="identify_issue", line_number=4, issue_type="incorrect_return"),
    ])

    run_test_case("EARLY APPROVE", [
    Action(action_type="approve")
    ])

    run_test_case("GARBAGE INPUT", [
    Action(action_type="suggest_fix", line_number=999, suggestion="blah blah")
    ])

