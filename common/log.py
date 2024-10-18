from terminaltexteffects.effects.effect_print import Print

def logger(text):
    effect = Print(text)
    
    with effect.terminal_output() as terminal:
        for frame in effect:
            terminal.print(frame)


log = logger