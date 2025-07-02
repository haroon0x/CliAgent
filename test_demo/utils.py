
def format_text(text):
    return text.strip().title()

def validate_input(value):
    return isinstance(value, (int, float, str))
