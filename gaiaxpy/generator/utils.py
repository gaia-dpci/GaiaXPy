def execute_answer(action, message=None, args=None):
    if action:
        if args:
            action(args)
        else:
            action()
        if message:
            print(message)


def get_yes_no_answer(question, yes_action, no_action, yes_message=None, no_message=None, yes_args=None, no_args=None):
    default = 'y'
    yes_choices = ['yes', default]
    no_choices = ['no', 'n']
    while True:
        user_input = input(question) or default
        if user_input.lower() in yes_choices:
            execute_answer(yes_action, yes_message, yes_args)
            break
        elif user_input.lower() in no_choices:
            execute_answer(no_action, no_message, no_args)
            break
        else:
            print('Please type yes or no.')
            continue
