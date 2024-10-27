import traceback


def stack_error(exception: Exception) -> str:
    stack_trace = traceback.format_exception(
        type(exception), exception, exception.__traceback__)
    return ''.join(stack_trace)
