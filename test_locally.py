from tutor_model import get_tutor_reply, ChatTurn


def main():
    history: list[ChatTurn] = []

    print("AI Tutor — local test (type 'quit' to exit)\n")

    first_message = "Hi"
    print(f"You: {first_message}")
    reply = get_tutor_reply(history, first_message)
    print(f"\nAda: {reply}\n")

    history.append({"role": "user", "text": first_message})
    history.append({"role": "model", "text": reply})

    while True:
        user_input = input("You: ")
        if user_input.strip().lower() == "quit":
            break

        reply = get_tutor_reply(history, user_input)
        print(f"\nAda: {reply}\n")

        history.append({"role": "user", "text": user_input})
        history.append({"role": "model", "text": reply})


if __name__ == "__main__":
    main()