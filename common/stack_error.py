import traceback

# 错误堆栈处理
def stack_error(exception):
    stack_trace = traceback.format_exception(type(exception), exception, exception.__traceback__)
    return ''.join(stack_trace)

stack_error = stack_error