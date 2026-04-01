from env.core.environment import CodeReview
from env.core.models import Action

def run_episode(env):
    observation = env.reset()
    total_reward = 0
    done = False

    print("\n--- NEW TASK ---")
    print("Code:\n", observation.code)

    while not done:
        if observation.current_step == 0:
            action = Action(
                action_type = "identify_issue",
                line_number = 4,
                issue_type = "incorrect_return"
            )

        elif observation.current_step == 1:
            action = Action(
                action_type = "suggest_fix",
                line_number = 4,
                suggestion = "return -1"
            )

        else:
            action = Action(
                action_type="approve"
            )

        observation, reward, done, _ = env.step(action)
        total_reward += reward

        print(f"\nStep {observation.current_step}")
        print("Action:", action)
        print("Reward:", reward)
        print("Done:", done)

    print("\nTotal Reward:", total_reward)
    return total_reward


if __name__ == "__main__":
    env = CodeReview()

    run_episode(env)